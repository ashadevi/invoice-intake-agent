from pathlib import Path
from typing import Any

from src.invoice_agent.email_loader import (
    get_message,
    load_email,
    summarize_email,
)
from src.invoice_agent.pdf_extractor import extract_pdf_content


class InvoiceContextError(Exception):
    """Raised when email and PDF context cannot be prepared."""


def resolve_pdf_path(email_path: str | Path, pdf_attachment_name: str) -> Path:
    """
    Resolve the PDF attachment path from the email file location.

    Example:
    email path: data/input_email.json
    attachment name: Invoice.pdf
    resolved path: data/Invoice.pdf
    """
    email_file_path = Path(email_path)
    pdf_path = email_file_path.parent / pdf_attachment_name

    if not pdf_path.exists():
        raise InvoiceContextError(
            f"PDF attachment listed in email but not found locally: {pdf_path}"
        )

    return pdf_path


def build_invoice_context(email_path: str | Path) -> dict[str, Any]:
    """
    Build a complete local context package for the invoice-intake workflow.

    This function does not call OpenAI.
    It prepares the email summary, PDF text, and rendered page image.
    """
    email_data = load_email(email_path)
    message = get_message(email_data)
    email_summary = summarize_email(message)

    pdf_attachment_name = email_summary["pdf_attachment_name"]
    pdf_path = resolve_pdf_path(email_path, pdf_attachment_name)

    pdf_content = extract_pdf_content(pdf_path)

    return {
        "email_path": str(email_path),
        "email_summary": email_summary,
        "pdf_path": str(pdf_path),
        "pdf_content": pdf_content,
    }


def build_model_text_context(invoice_context: dict[str, Any], max_chars: int = 12000) -> str:
    """
    Create a controlled text context for the future OpenAI extraction step.

    We limit characters to avoid large prompt dumps and unnecessary API cost.
    """
    email_summary = invoice_context["email_summary"]
    pdf_content = invoice_context["pdf_content"]

    email_body = email_summary.get("body", "")
    pdf_text = pdf_content.get("full_text", "")

    combined = f"""
EMAIL SUBJECT:
{email_summary.get("subject", "")}

EMAIL FROM:
{email_summary.get("from_name", "")} <{email_summary.get("from_address", "")}>

EMAIL BODY:
{email_body}

PDF TEXT:
{pdf_text}
""".strip()

    if len(combined) > max_chars:
        return combined[:max_chars] + "\n\n[TRUNCATED TO CONTROL API USAGE]"

    return combined
