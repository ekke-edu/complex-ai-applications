from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from .models import VideoAnalyzer
from .schemas import VideoAnalysisResponseSchema

MAX_VIDEO_BYTES = 50 * 1024 * 1024  # 50 MB

router = APIRouter(prefix="/video", tags=["Video Analysis"])

ALLOWED_EXTENSIONS = (".mp4", ".mkv")
ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/x-matroska",
    "video/matroska",
    "application/octet-stream",  # böngészőtől függően MKV-nál előfordulhat
}


def get_app_state(request: Request):
    return request.app.state


def get_video_analyzer(request: Request) -> VideoAnalyzer:
    state = get_app_state(request)
    return VideoAnalyzer(groq_client=state.groq_client)


async def _validate_and_read_video(file: UploadFile) -> bytes:
    filename_lower = file.filename.lower() if file.filename else ""
    content_type = (file.content_type or "").lower()

    if not filename_lower.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Csak MP4 és MKV formátumú videók tölthetők fel!",
        )

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Nem támogatott fájltípus ({content_type}). Csak MP4 és MKV engedélyezett.",
        )

    chunks: list[bytes] = []
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_VIDEO_BYTES:
            raise HTTPException(
                status_code=413,
                detail="A feltöltött videó mérete meghaladja a maximális 50 MB-os limitet.",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(status_code=400, detail="Üres videófájl érkezett.")

    return b"".join(chunks)


@router.post("/analyze_video", response_model=VideoAnalysisResponseSchema)
async def analyze_video(
        session_id: str = Form(...),
        prompt: str = Form(...),
        language: str = Form("hu"),
        file: UploadFile = File(...),
        analyzer: VideoAnalyzer = Depends(get_video_analyzer),
) -> VideoAnalysisResponseSchema:
    video_bytes = await _validate_and_read_video(file)

    try:
        result = await analyzer.analyze_video(
            session_id=session_id,
            video_bytes=video_bytes,
            prompt=prompt,
            filename=file.filename,
            language=language,
        )
        return VideoAnalysisResponseSchema(**result)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
