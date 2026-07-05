import json
from pathlib import Path
from typing import Any


class EmailLoadError(Exception):
    """Raised when the inbound email file cannot be loaded or parsed."""


def load_email(email_path: str | Path) -> dict[str, Any]:
    """
    Load the inbound email JSON file.

    Why this function exists:
    - The assignment gives the email as a local file.
    - Our program should read that file instead of hardcoding email content.
    - This keeps the project reusable for other email JSON files.
    """
    path = Path(email_path)

    if not path.exists():
        raise EmailLoadError(f"Email file not found: {path}")

    if not path.is_file():
        raise EmailLoadError(f"Email path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise EmailLoadError(f"Invalid JSON in email file: {path}") from exc
    except OSError as exc:
        raise EmailLoadError(f"Could not read email file: {path}") from exc

    if "Message" not in data:
        raise EmailLoadError("Email JSON does not contain a 'Message' object.")

    return data


def get_message(email_data: dict[str, Any]) -> dict[str, Any]:
    """Return the Message object from the email JSON."""
    message = email_data.get("Message")

    if not isinstance(message, dict):
        raise EmailLoadError("Email 'Message' must be a JSON object.")

    return message


def get_email_body(message: dict[str, Any]) -> str:
    """Extract the plain text body from the email message."""
    body = message.get("Body", {})
    content = body.get("Content", "")

    if not isinstance(content, str):
        return ""

    return content


def get_pdf_attachment_name(message: dict[str, Any]) -> str:
    """
    Find the first PDF attachment name in the email.

    This satisfies the requirement to handle the provided PDF attachment
    from the local inbound email file.
    """
    attachments = message.get("Attachments", [])

    if not attachments:
        raise EmailLoadError("No attachments found in the email.")

    for attachment in attachments:
        name = attachment.get("Name", "")
        content_type = attachment.get("ContentType", "")

        is_pdf_name = isinstance(name, str) and name.lower().endswith(".pdf")
        is_pdf_type = isinstance(content_type, str) and content_type.lower() == "application/pdf"

        if is_pdf_name or is_pdf_type:
            if not name:
                raise EmailLoadError("PDF attachment found, but it has no file name.")
            return name

    raise EmailLoadError("No PDF attachment found in the email.")


def summarize_email(message: dict[str, Any]) -> dict[str, Any]:
    """Create a clean summary of useful email metadata."""
    sender = message.get("From", {}).get("EmailAddress", {})
    to_recipients = message.get("ToRecipients", [])
    cc_recipients = message.get("CcRecipients", [])

    return {
        "subject": message.get("Subject", ""),
        "sent_datetime": message.get("SentDateTime", ""),
        "from_name": sender.get("Name", ""),
        "from_address": sender.get("Address", ""),
        "to": [
            recipient.get("EmailAddress", {})
            for recipient in to_recipients
        ],
        "cc": [
            recipient.get("EmailAddress", {})
            for recipient in cc_recipients
        ],
        "body": get_email_body(message),
        "pdf_attachment_name": get_pdf_attachment_name(message),
    }
