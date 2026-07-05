import json
from pathlib import Path
from typing import Any

from src.invoice_agent.schemas import InvoiceData


class NotificationError(Exception):
    """Raised when the Customer Service notification cannot be created."""


def _money(value: float | None, currency: str = "") -> str:
    """Format money values safely."""
    if value is None:
        return "Not found"

    if currency:
        return f"{currency} {value:,.2f}"

    return f"{value:,.2f}"


def build_notification_subject(invoice: InvoiceData) -> str:
    """Create a clear subject line for the outbound Customer Service notification."""
    vendor = invoice.vendor_name or "Unknown vendor"
    invoice_number = invoice.invoice_number or "Unknown invoice number"

    return f"Invoice Intake Notification - {vendor} - {invoice_number}"


def build_human_readable_summary(invoice: InvoiceData) -> str:
    """
    Create the human-readable Customer Service notification.

    This is meant for people who need to process the invoice.
    """
    subject = build_notification_subject(invoice)

    cost_centres = ", ".join(invoice.cost_centres) if invoice.cost_centres else "Not found"

    notes = "\n".join(
        f"- {note}" for note in invoice.important_notes
    ) if invoice.important_notes else "- No additional notes found."

    sites = "\n".join(
        f"- {site.site_name} ({site.cost_centre}) | Receiving hours: {site.receiving_hours} | Delivery window: {site.delivery_window}"
        for site in invoice.ship_to_locations
    ) if invoice.ship_to_locations else "- No ship-to/site allocation details found."

    line_items = "\n".join(
        f"- {item.sku}: {item.description} | Qty: {item.quantity} | Unit: {_money(item.unit_price, invoice.currency)} | Total: {_money(item.line_total, invoice.currency)}"
        for item in invoice.line_items
    ) if invoice.line_items else "- No line items found."

    taxes = "\n".join(
        f"- {tax.jurisdiction}: {tax.tax_type} {tax.tax_rate} on {_money(tax.taxable_amount, invoice.currency)} = {_money(tax.tax_amount, invoice.currency)}"
        for tax in invoice.tax_breakdown
    ) if invoice.tax_breakdown else "- No tax breakdown found."

    return f"""
{subject}

Summary
- Vendor: {invoice.vendor_name or "Not found"}
- Invoice Number: {invoice.invoice_number or "Not found"}
- Invoice Date: {invoice.invoice_date or "Not found"}
- Due Date: {invoice.due_date or "Not found"}
- Payment Terms: {invoice.payment_terms or "Not found"}
- Customer PO: {invoice.customer_po or "Not found"}
- Currency: {invoice.currency or "Not found"}
- Subtotal: {_money(invoice.subtotal, invoice.currency)}
- Total Tax: {_money(invoice.total_tax, invoice.currency)}
- Total Due: {_money(invoice.total_due, invoice.currency)}
- Cost Centres: {cost_centres}

Duplicate / Prior Document Warning
{invoice.duplicate_warning or "No duplicate warning found."}

Ship-To / Site Allocations
{sites}

Tax Breakdown
{taxes}

Line Items
{line_items}

Important Notes
{notes}

Source
- Email Subject: {invoice.source_email_subject or "Not found"}
- Email Sender: {invoice.source_email_sender or "Not found"}
- Source PDF: {invoice.source_pdf or "Not found"}
""".strip()


def write_notification_files(
    invoice_data: InvoiceData | dict[str, Any],
    output_dir: str | Path = "outputs",
) -> dict[str, str]:
    """
    Write Customer Service notification outputs.

    Outputs:
    - outbound_email.txt: human-readable message
    - outbound_payload.json: structured JSON payload
    """
    try:
        invoice = (
            invoice_data
            if isinstance(invoice_data, InvoiceData)
            else InvoiceData.model_validate(invoice_data)
        )

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        human_summary = build_human_readable_summary(invoice)

        txt_path = output_path / "outbound_email.txt"
        json_path = output_path / "outbound_payload.json"

        txt_path.write_text(human_summary, encoding="utf-8")

        json_payload = invoice.model_dump(mode="json")
        json_path.write_text(
            json.dumps(json_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return {
            "outbound_email_txt": str(txt_path),
            "outbound_payload_json": str(json_path),
        }

    except Exception as exc:
        raise NotificationError("Could not create Customer Service notification files.") from exc
