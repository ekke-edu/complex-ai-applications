import base64
import datetime
import io
from typing import Any, List, cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from tenacity import retry, stop_after_attempt, wait_exponential

from .models import DepthEstimator, VisionDetector
from .schemas import ChatVisionInput, DetectionResponseSchema, DepthResponseSchema

MAX_VISION_IMAGE_BYTES = 50 * 1024 * 1024  # 50 MB / kép
MAX_CHAT_VISION_FILES = 3
ALLOWED_VISION_MIMES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_VISION_EXTENSIONS = (".jpg", ".jpeg", ".png")
ALLOWED_VISION_PIL_FORMATS = {"JPEG", "PNG"}

router = APIRouter(prefix="/vision", tags=["Vision & Waldo"])

waldo_progress: dict[str, dict] = {}


def get_app_state(request: Request):
    return request.app.state


def get_vision_detector(request: Request) -> VisionDetector:
    state = get_app_state(request)
    return VisionDetector(groq_client=state.groq_client)


def get_depth_estimator(request: Request) -> DepthEstimator:
    state = get_app_state(request)
    if not hasattr(state, "depth_estimator"):
        state.depth_estimator = DepthEstimator()
    return state.depth_estimator


async def _validate_and_read_vision_image(file: UploadFile) -> tuple[bytes, str]:
    filename_lower = file.filename.lower() if file.filename else ""
    content_type_lower = file.content_type.lower() if file.content_type else ""

    if content_type_lower and content_type_lower not in ALLOWED_VISION_MIMES:
        raise HTTPException(
            status_code=415,
            detail="Csak JPG, JPEG vagy PNG formátumú képek tölthetők fel!",
        )

    if not content_type_lower and not filename_lower.endswith(ALLOWED_VISION_EXTENSIONS):
        raise HTTPException(
            status_code=415,
            detail="Csak JPG, JPEG vagy PNG formátumú képek tölthetők fel!",
        )

    chunks: list[bytes] = []
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_VISION_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"A(z) '{file.filename or 'kép'}' meghaladja a képenkénti maximális 50 MB-os limitet.",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail="Üres képfájl érkezett.",
        )

    image_bytes = b"".join(chunks)

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img_format = (img.format or "").upper()
            if img_format not in ALLOWED_VISION_PIL_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Csak JPG, JPEG vagy PNG formátumú képek tölthetők fel!",
                )
            img.verify()

        resolved_mime = "image/png" if img_format == "PNG" else "image/jpeg"
        return image_bytes, resolved_mime
    except HTTPException:
        raise
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=400,
            detail=f"A(z) '{file.filename or 'kép'}' nem érvényes vagy sérült képfájl.",
        )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=10))
@router.post("/chat_with_image")
async def chat_with_image(
        request: Request,
        session_id: str = Form(...),
        prompt: str = Form(...),
        files: List[UploadFile] = File(...),
):
    if len(files) > MAX_CHAT_VISION_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Egyszerre legfeljebb {MAX_CHAT_VISION_FILES} kép tölthető fel.",
        )

    state = get_app_state(request)
    groq_client = state.groq_client
    chat_coll = state.chat_collection

    try:
        content_items: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        filenames: list[str] = []

        for file in files:
            image_bytes, mime_type = await _validate_and_read_vision_image(file)
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            filenames.append(file.filename or "image")

            content_items.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
            })

        response = await cast(Any, groq_client.chat.completions).create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "user", "content": content_items}],
            max_tokens=900,
        )

        reply_text = response.choices[0].message.content
        now = datetime.datetime.utcnow()
        filenames_str = ", ".join(filenames)

        await chat_coll.insert_many([
            {
                "session_id": session_id,
                "role": "user",
                "content": f"[Képek feltöltve: {filenames_str}] - {prompt}",
                "timestamp": now,
            },
            {
                "session_id": session_id,
                "role": "assistant",
                "content": reply_text,
                "timestamp": now + datetime.timedelta(milliseconds=1),
            },
        ])

        return {
            "session_id": session_id,
            "response": reply_text,
            "filenames": filenames,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/detect_and_crop", response_model=DetectionResponseSchema)
async def detect_and_crop(
        session_id: str = Form(...),
        prompt: str = Form(...),
        file: UploadFile = File(...),
        detector: VisionDetector = Depends(get_vision_detector),
) -> DetectionResponseSchema:
    image_bytes, effective_mime = await _validate_and_read_vision_image(file)

    try:
        return await detector.detect_and_crop(
            session_id=session_id,
            prompt=prompt,
            image_bytes=image_bytes,
            filename=file.filename,
            mime_type=effective_mime,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/estimate_depth", response_model=DepthResponseSchema)
async def estimate_depth(
        session_id: str = Form(...),
        colormap: str = Form("inferno"),
        model_size: str = Form("small"),
        file: UploadFile = File(...),
        estimator: DepthEstimator = Depends(get_depth_estimator),
) -> DepthResponseSchema:
    image_bytes, _ = await _validate_and_read_vision_image(file)

    try:
        result = await estimator.estimate_depth(
            session_id=session_id,
            image_bytes=image_bytes,
            colormap=colormap,
            model_size=model_size,
            filename=file.filename,
        )
        return DepthResponseSchema(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
