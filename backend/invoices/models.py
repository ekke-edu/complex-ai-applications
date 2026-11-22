from typing import List, Optional
from pydantic import BaseModel

class DBInvoiceModel(BaseModel):
    session_id: str
    filename: str
    partner_name: str
    tax_number: Optional[str] = "Nincs megadva"
    total_amount: float
    fulfillment_date: str
    cost_category: str
    items: List[dict] = []
