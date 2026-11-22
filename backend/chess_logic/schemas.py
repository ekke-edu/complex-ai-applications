from pydantic import BaseModel
from typing import Optional, List, Any

class ChessAnalysisRequest(BaseModel):
    image_path: Optional[str] = None
    prompt: str

class ModelResponse(BaseModel):
    model_name: str
    thought_process: str
    move: str
    duration_seconds: float
    error: Optional[str] = None

class ChessBattleResponse(BaseModel):
    gemini_result: ModelResponse
    groq_result: ModelResponse

# --- ÚJ SÉMÁK A MECCS SZIMULÁCIÓHOZ ---

class MatchStep(BaseModel):
    turn: int
    player: str
    move: str
    thought: str
    duration: float
    fen: str
    status: str
    board_image: Optional[str] = None

class MatchSimulationResponse(BaseModel):
    history: List[MatchStep]

class CoachPlayRequest(BaseModel):
    fen: str
    player_move: str
    groq_api_key: Optional[str] = ""

class CoachPlayResponse(BaseModel):
    success: bool = False
    new_fen: str = ""
    engine_move_uci: str = ""
    from_square: int = 0
    to_square: int = 0
    evaluation: Optional[int] = 0
    ai_explanation: str = ""
    game_over: bool = False
    error: Optional[str] = None
