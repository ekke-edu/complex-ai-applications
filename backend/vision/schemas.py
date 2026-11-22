from typing import List, Optional
from pydantic import BaseModel, Field


class ChatVisionInput(BaseModel):
    session_id: str
    prompt: str


class BoundingBox(BaseModel):
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)

    def to_pixel_coords(self, width: int, height: int) -> List[int]:
        """0-1000 skáláról átváltás valós pixel koordinátákra [x1, y1, x2, y2]."""
        x1 = max(0, min(width, round(self.xmin * width / 1000)))
        y1 = max(0, min(height, round(self.ymin * height / 1000)))
        x2 = max(0, min(width, round(self.xmax * width / 1000)))
        y2 = max(0, min(height, round(self.ymax * height / 1000)))

        # Ha a modell felcserélné a min/max értékeket
        return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]


class DetectionResponseSchema(BaseModel):
    session_id: str
    response: str
    found: bool
    box: Optional[List[int]] = None
    annotated_image: Optional[str] = None
    cropped_image: Optional[str] = None
    filename: Optional[str] = None

class DepthResponseSchema(BaseModel):
    session_id: str
    duration: float
    depth_image: str  # Base64 kódolt kép
    filename: Optional[str] = None
