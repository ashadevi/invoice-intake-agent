import base64
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.invoice_agent.invoice_context import build_invoice_context, build_model_text_context
from src.invoice_agent.schemas import InvoiceData


class OpenAIExtractionError(Exception):
    """Raised when OpenAI invoice extraction fails."""


def encode_image_as_data_url(image_path: str | Path) -> str:
    """
    Convert a local image file to a base64 data URL.

    Why this function exists:
    - The invoice number may appear in a rendered PDF image.
    - OpenAI vision input can accept a base64 data URL.
    """
    path = Path(image_path)

    if not path.exists():
        raise OpenAIExtractionError(f"Rendered page image not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".png":
        mime_type = "image/png"
    elif suffix in {".jpg", ".jpeg"}:
        mime_type = "image/jpeg"
    else:
        raise OpenAIExtractionError(f"Unsupported image type for OpenAI vision: {suffix}")

    try:
        image_bytes = path.read_bytes()
        encoded = base64.b64encode(image_bytes).decode("utf-8")
    except OSError as exc:
        raise OpenAIExtractionError(f"Could not read rendered page image: {path}") from exc

    return f"data:{mime_type};base64,{encoded}"


def _extract_json_from_text(text: str) -> str:
    """
    Extract JSON from the model output.

    The model should return only JSON, but this makes parsing more defensive.
    """
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise OpenAIExtractionError("OpenAI response did not contain a JSON object.")

    return cleaned[start : end + 1]


def extract_invoice_data_with_openai(
    email_path: str | Path,
    model: str | None = None,
) -> InvoiceData:
    """
    Extract structured invoice data using OpenAI.

    This function:
    - builds local email/PDF context
    - sends targeted text + first page image to the model
    - validates the response against InvoiceData
    """
    load_dotenv()

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
    allowed_models = {"gpt-5-mini", "gpt-5-nano"}

    if selected_model not in allowed_models:
        raise OpenAIExtractionError(
            f"Model '{selected_model}' is not allowed. Use one of: {sorted(allowed_models)}"
        )

    if not os.getenv("OPENAI_API_KEY"):
        raise OpenAIExtractionError(
            "OPENAI_API_KEY is missing. Add it to your local .env file."
        )

    invoice_context = build_invoice_context(email_path)
    text_context = build_model_text_context(invoice_context, max_chars=12000)
    first_page_image_path = invoice_context["pdf_content"]["first_page_image"]
    image_data_url = encode_image_as_data_url(first_page_image_path)

    client = OpenAI()

    schema_description = InvoiceData.model_json_schema()

    prompt = f"""
You are an invoice-intake extraction assistant.

Extract invoice and purchase-processing data from the provided EMAIL + PDF TEXT + FIRST PAGE IMAGE.

Important requirements:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not invent values.
- If a value is missing, use an empty string, null, or an empty list.
- The invoice number may appear only inside the first page image. Read the image carefully.
- Use the email for workflow context such as PO number, terms, cost centres, duplicate-warning note, and receiving context.
- Use the PDF text for vendor, line items, tax breakdown, delivery allocation, notes, and contacts.
- Currency should be CAD if the invoice totals are listed in CAD.
- Numeric fields should be numbers, not strings, when possible.

Target JSON schema:
{json.dumps(schema_description, indent=2)}

EMAIL + PDF TEXT CONTEXT:
{text_context}
""".strip()

    try:
        response = client.responses.create(
            model=selected_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {
                            "type": "input_image",
                            "image_url": image_data_url,
                            "detail": "high",
                        },
                    ],
                }
            ],
            max_output_tokens=4000,
        )
    except Exception as exc:
        raise OpenAIExtractionError("OpenAI extraction request failed.") from exc

    raw_output = response.output_text
    json_text = _extract_json_from_text(raw_output)

    try:
        invoice = InvoiceData.model_validate_json(json_text)
    except Exception as exc:
        raise OpenAIExtractionError(
            f"OpenAI returned JSON, but it did not match InvoiceData schema. Raw JSON: {json_text}"
        ) from exc

    # Always use deterministic local source values instead of model-guessed source labels.
    email_summary = invoice_context["email_summary"]
    invoice.source_email_subject = email_summary.get("subject", "")
    invoice.source_email_sender = (
        f"{email_summary.get('from_name', '')} <{email_summary.get('from_address', '')}>"
        if email_summary.get("from_name") and email_summary.get("from_address")
        else email_summary.get("from_address", "")
    )
    invoice.source_pdf = invoice_context["pdf_path"]

    return invoice

