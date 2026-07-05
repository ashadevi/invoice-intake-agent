import json
import os
from pathlib import Path

from agents import Agent, ModelSettings, Runner, function_tool
from dotenv import load_dotenv

from src.invoice_agent.notification_tool import write_notification_files
from src.invoice_agent.openai_extractor import extract_invoice_data_with_openai


class AgentWorkflowError(Exception):
    """Raised when the invoice-intake agent workflow fails."""


@function_tool
def extract_invoice_data(email_path: str) -> str:
    """
    Extract structured invoice data from the local email and PDF attachment.

    Args:
        email_path: Path to the local inbound email JSON file.

    Returns:
        A JSON string containing structured invoice data.
    """
    invoice = extract_invoice_data_with_openai(email_path)
    return invoice.model_dump_json(indent=2)


@function_tool
def produce_customer_service_notification(invoice_payload_json: str) -> str:
    """
    Create the outbound Customer Service notification files.

    Args:
        invoice_payload_json: Structured invoice data as a JSON string.

    Returns:
        A JSON string containing the generated output file paths.
    """
    try:
        invoice_payload = json.loads(invoice_payload_json)
    except json.JSONDecodeError as exc:
        raise AgentWorkflowError("Tool received invalid invoice JSON.") from exc

    paths = write_notification_files(invoice_payload)
    return json.dumps(paths, indent=2)


def create_invoice_agent(model: str | None = None) -> Agent:
    """
    Create the invoice-intake agent.

    The agent has two tools:
    1. extract_invoice_data
    2. produce_customer_service_notification
    """
    load_dotenv()

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
    allowed_models = {"gpt-5-mini", "gpt-5-nano"}

    if selected_model not in allowed_models:
        raise AgentWorkflowError(
            f"Model '{selected_model}' is not allowed. Use one of: {sorted(allowed_models)}"
        )

    return Agent(
        name="Invoice Intake Agent",
        model=selected_model,
        instructions=(
            "You are an invoice-intake workflow agent. "
            "You must process a local inbound email JSON file and its PDF attachment. "
            "First, call extract_invoice_data using the provided email path. "
            "Second, call produce_customer_service_notification using the JSON returned by extract_invoice_data. "
            "Do not invent missing values. "
            "Return a short final message listing the output files created."
        ),
        tools=[
            extract_invoice_data,
            produce_customer_service_notification,
        ],
        model_settings=ModelSettings(tool_choice="auto"),
    )


async def run_invoice_agent(email_path: str | Path, model: str | None = None) -> str:
    """
    Run the full invoice-intake agent workflow.

    This calls the agent, which should use both tools:
    - extraction tool
    - notification tool
    """
    email_path = str(email_path)

    if not Path(email_path).exists():
        raise AgentWorkflowError(f"Email file not found: {email_path}")

    agent = create_invoice_agent(model=model)

    result = await Runner.run(
        agent,
        input=(
            f"Process this inbound invoice email: {email_path}. "
            "Call the extraction tool first, then call the notification tool. "
            "Finish by reporting the output file paths."
        ),
        max_turns=8,
    )

    return str(result.final_output)

