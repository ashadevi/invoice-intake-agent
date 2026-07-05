from typing import Any

from pydantic import BaseModel, Field


class TaxBreakdown(BaseModel):
    """Tax amount by jurisdiction and tax type."""

    jurisdiction: str = ""
    taxable_amount: float | None = None
    tax_type: str = ""
    tax_rate: str = ""
    tax_amount: float | None = None


class LineItem(BaseModel):
    """One invoice line item."""

    line_number: int | None = None
    sku: str = ""
    description: str = ""
    quantity: float | None = None
    unit_price: float | None = None
    line_total: float | None = None


class SiteAllocation(BaseModel):
    """Delivery or cost-centre allocation by receiving site."""

    site_name: str = ""
    cost_centre: str = ""
    address: str = ""
    receiving_hours: str = ""
    delivery_window: str = ""
    items: list[dict[str, Any]] = Field(default_factory=list)


class InvoiceData(BaseModel):
    """
    Structured invoice data extracted from the email and PDF.

    This model is the main JSON payload that downstream systems can consume.
    """

    vendor_name: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    due_date: str = ""
    payment_terms: str = ""
    currency: str = ""

    customer_name: str = ""
    customer_account: str = ""
    customer_po: str = ""

    subtotal: float | None = None
    total_tax: float | None = None
    total_due: float | None = None

    tax_breakdown: list[TaxBreakdown] = Field(default_factory=list)
    line_items: list[LineItem] = Field(default_factory=list)
    ship_to_locations: list[SiteAllocation] = Field(default_factory=list)

    cost_centres: list[str] = Field(default_factory=list)
    important_notes: list[str] = Field(default_factory=list)

    duplicate_warning: str = ""
    source_email_subject: str = ""
    source_email_sender: str = ""
    source_pdf: str = ""


class NotificationOutput(BaseModel):
    """
    Final outbound notification output.

    The assignment requires both:
    - a human-readable summary
    - a structured JSON payload
    """

    subject: str
    human_readable_summary: str
    structured_payload: InvoiceData
