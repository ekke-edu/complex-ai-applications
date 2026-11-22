import io
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from .models import ChessAIAnalyzer, ChessCoachSimulator, ChessGameSimulator
from .schemas import ChessBattleResponse, CoachPlayResponse, MatchSimulationResponse

MAX_CHESS_IMAGE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_CHESS_MIMES = {"image/jpeg", "image/png"}
ALLOWED_CHESS_PIL_FORMATS = {"JPEG", "PNG"}

# FastAPI router definíció
router = APIRouter(prefix="/chess_logic", tags=["Chess Battle"])


async def _validate_and_load_chess_image(file: UploadFile) -> Image.Image:
    if file.content_type and file.content_type.lower() not in ALLOWED_CHESS_MIMES:
        raise HTTPException(
            status_code=415,
            detail="Csak JPG, JPEG vagy PNG képfájl tölthető fel.",
        )

    if not file.content_type and file.filename:
        lower_name = file.filename.lower()
        if not lower_name.endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(
                status_code=415,
                detail="Csak JPG, JPEG vagy PNG képfájl tölthető fel.",
            )

    chunks: list[bytes] = []
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_CHESS_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="A feltöltött kép mérete meghaladja a maximális 50 MB-os limitet.",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail="A feltöltött képfájl üres.",
        )

    raw_bytes = b"".join(chunks)

    try:
        with Image.open(io.BytesIO(raw_bytes)) as verify_img:
            img_format = (verify_img.format or "").upper()
            if img_format not in ALLOWED_CHESS_PIL_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Csak JPG, JPEG vagy PNG képfájl tölthető fel.",
                )
            verify_img.verify()

        with Image.open(io.BytesIO(raw_bytes)) as loaded_img:
            return loaded_img.copy()
    except HTTPException:
        raise
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=400,
            detail="A feltöltött fájl nem érvényes vagy sérült kép.",
        )


class ChessBattleOrchestrator:
    """Az üzleti logika réteg a kép-alapú elemzéshez"""

    @staticmethod
    def run_battle(
        image: Image.Image,
        gemini_key: str,
        groq_key: str,
        turn_color: str = "white",
    ) -> ChessBattleResponse:
        gemini_res = ChessAIAnalyzer.analyze_with_gemini(image, gemini_key, turn_color=turn_color)
        groq_res = ChessAIAnalyzer.analyze_with_groq(image, groq_key, turn_color=turn_color)

        return ChessBattleResponse(
            gemini_result=gemini_res,
            groq_result=groq_res,
        )


# --- 1. HTTP VÉGPONT: Képalapú párbaj ---
@router.post("/battle", response_model=ChessBattleResponse)
async def run_chess_battle_endpoint(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    turn_color: str = Form("white"),
    gemini_api_key: str = Form(""),
    groq_api_key: str = Form(""),
):
    image = await _validate_and_load_chess_image(file)

    result = ChessBattleOrchestrator.run_battle(
        image=image,
        gemini_key=gemini_api_key,
        groq_key=groq_api_key,
        turn_color=turn_color,
    )
    return result


# --- 2. HTTP VÉGPONT: AI vs AI önműködő meccs szimuláció ---
@router.post("/simulate_match", response_model=MatchSimulationResponse)
async def run_simulate_match_endpoint(
    session_id: str = Form(...),
    gemini_api_key: str = Form(""),
    groq_api_key: str = Form(""),
    opponent: str = Form("groq"),
    max_turns: int = Form(15),
):
    """
    Meghívja a ChessGameSimulator-t, ami körről körre lejátsza a partit
    Gemini (Világos) és Groq (Sötét) között.
    """
    history = ChessGameSimulator.play_full_game(
        gemini_api_key=gemini_api_key,
        secondary_api_key=groq_api_key,
        opponent=opponent,
        max_turns=max_turns,
    )

    return MatchSimulationResponse(history=history)


@router.post("/play_vs_stockfish", response_model=CoachPlayResponse)
async def play_vs_stockfish_endpoint(
    session_id: str = Form(...),
    fen: str = Form(...),
    player_move: str = Form(...),
    groq_api_key: str = Form(""),
):
    """
    Kezeli az élő játékos és a Stockfish 19 közötti interaktív partit,
    valamint meghívja a Groq AI mentort.
    """
    result = ChessCoachSimulator.play_turn(fen, player_move, groq_api_key)
    return CoachPlayResponse(**result)


@router.post("/engine_move_stockfish", response_model=CoachPlayResponse)
async def engine_move_stockfish_endpoint(
    session_id: str = Form(...),
    fen: str = Form(...),
    groq_api_key: str = Form(""),
):
    result = ChessCoachSimulator.engine_move_only(fen, groq_api_key)
    return CoachPlayResponse(**result)
