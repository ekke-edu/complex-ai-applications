from typing import Optional
from pydantic import BaseModel, Field


class VideoAnalysisResponseSchema(BaseModel):
    session_id: str
    transcript: str = Field(..., description="A videó hangjának átirata (Whisper)")
    vision_analysis: str = Field(..., description="A videó képkockáinak vizuális elemzése (Qwen Vision)")
    filename: Optional[str] = None
