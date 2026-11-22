from pydantic import BaseModel
from typing import List, Optional

class WaldoModelResult(BaseModel):
    model: str
    response: str
    found: bool
    time: float
    annotated_image: Optional[str] = None # Base64 kódolt kép

class WaldoRaceResponse(BaseModel):
    session_id: str
    results: List[WaldoModelResult]
