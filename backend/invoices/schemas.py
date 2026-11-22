from typing import List, Optional
from pydantic import BaseModel


class InvoiceItem(BaseModel):
    description: str
    quantity: Optional[float] = 1.0
    unit_price: Optional[float] = 0.0
    total_price: float


class StructuredInvoice(BaseModel):
    is_invoice: Optional[bool] = True
    message: Optional[str] = None
    partner_name: str
    tax_number: Optional[str] = "Nincs megadva"
    total_amount: float
    fulfillment_date: str
    cost_category: str
    items: List[InvoiceItem] = []
