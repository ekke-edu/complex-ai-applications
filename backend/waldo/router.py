import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
import io
import os
from pathlib import Path
import time

from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from google import genai
from PIL import Image, UnidentifiedImageError
import requests

from .models import parse_and_annotate_waldo
from .schemas import WaldoRaceResponse

MAX_WALDO_IMAGE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_WALDO_MIMES = {"image/jpeg", "image/png"}
ALLOWED_WALDO_PIL_FORMATS = {"JPEG", "PNG"}

router = APIRouter(prefix="/waldo", tags=["Waldo Race"])

# Kliensek inicializálása
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

waldo_progress: dict[str, dict] = {}


def call_openrouter_chat(model: str, content: list, max_tokens: int = 200, temperature: float = 0) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Hiányzik az OPENROUTER_API_KEY környezeti változó.")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"] or ""


def get_app_state(request: Request):
    return request.app.state


async def _validate_and_load_waldo_image(file: UploadFile) -> tuple[bytes, Image.Image, str]:
    if file.content_type and file.content_type.lower() not in ALLOWED_WALDO_MIMES:
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
        if total_bytes > MAX_WALDO_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="A feltöltött kép mérete meghaladja a maximális 50 MB-os limitet.",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail="Üres képfájl érkezett.",
        )

    image_bytes = b"".join(chunks)

    try:
        with Image.open(io.BytesIO(image_bytes)) as verify_img:
            img_format = (verify_img.format or "").upper()
            if img_format not in ALLOWED_WALDO_PIL_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Csak JPG, JPEG vagy PNG képfájl tölthető fel.",
                )
            verify_img.verify()

        with Image.open(io.BytesIO(image_bytes)) as loaded_img:
            rgb_image = loaded_img.convert("RGB")

        resolved_mime = "image/png" if img_format == "PNG" else "image/jpeg"
        return image_bytes, rgb_image, resolved_mime
    except HTTPException:
        raise
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=400,
            detail="A feltöltött fájl nem érvényes vagy sérült képfájl.",
        )


@router.post("/waldo_race", response_model=WaldoRaceResponse)
async def waldo_race(
        request: Request,
        session_id: str = Form(...),
        prompt: str = Form(...),
        file: UploadFile = File(...),
):
    state = get_app_state(request)
    groq_client = state.groq_client

    waldo_progress[session_id] = {"current": 1, "total": 6, "message": "Kép beolvasása és ellenőrzése...", "done": False}

    try:
        image_bytes, image, mime_type = await _validate_and_load_waldo_image(file)
    except HTTPException:
        waldo_progress.pop(session_id, None)
        raise

    width, height = image.size
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Referenciakép betöltése a gyökérből
    root_dir = Path(__file__).resolve().parents[2]
    reference_path = root_dir / "waldo_character.jpg"
    reference_image_bytes = None
    if reference_path.exists():
        with open(reference_path, "rb") as f:
            reference_image_bytes = f.read()

    # --- 1. Alap prompt (Kép nélkül) ---
    base_prompt = (
        f"Feladat: Keresd meg Waldo/Wally figurát ezen a rejtvényképen.\n"
        f"Felhasználói támpont: {prompt}\n\n"
        "A válaszod első sora: FOUND: NO vagy FOUND: YES [ymin, xmin, ymax, xmax] (0-1000 skálán)."
    )
    base_payload = [
        {"type": "text", "text": base_prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
    ]

    # --- 2. Referenciás prompt (Képpel) ---
    ref_prompt = (
        f"Feladat: Keresd meg a csatolt referenciaképen látható karaktert ezen a fő rejtvényképen.\n"
        f"További felhasználói támpont: {prompt}\n\n"
        "A válaszod első sora: FOUND: NO vagy FOUND: YES [ymin, xmin, ymax, xmax] (0-1000 skálán)."
    )
    ref_payload = []
    if reference_image_bytes:
        ref_base64 = base64.b64encode(reference_image_bytes).decode("utf-8")
        ref_payload.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{ref_base64}"}
        })
        ref_payload.append({"type": "text", "text": "Itt van a keresendő karakter referenciája:"})
    ref_payload.append({"type": "text", "text": ref_prompt})
    ref_payload.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}})

    waldo_progress[session_id] = {"current": 2, "total": 6, "message": "Modellek futtatása (alap + referenciás)...", "done": False}

    # --- QWEN FUNKCIÓK ---
    async def query_qwen_base():
        start_time = time.time()
        try:
            res = await groq_client.chat.completions.create(
                model="qwen/qwen3.8-27b", messages=[{"role": "user", "content": base_payload}], max_tokens=200, temperature=0
            )
            return parse_and_annotate_waldo(res.choices[0].message.content or "", start_time, image, width, height, "Qwen 3.8 (Alap)")
        except Exception as e:
            return {"model": "Qwen 3.8 (Alap)", "response": f"Hiba: {e}", "found": False, "time": 0.0, "annotated_image": None}

    async def query_qwen_ref():
        start_time = time.time()
        try:
            res = await groq_client.chat.completions.create(
                model="qwen/qwen3.8-27b", messages=[{"role": "user", "content": ref_payload}], max_tokens=200, temperature=0
            )
            return parse_and_annotate_waldo(res.choices[0].message.content or "", start_time, image, width, height, "Qwen 3.8 (Referenciával)")
        except Exception as e:
            return {"model": "Qwen 3.8 (Referenciával)", "response": f"Hiba: {e}", "found": False, "time": 0.0, "annotated_image": None}

    # --- GEMINI FUNKCIÓK ---
    def query_gemini_base():
        start_time = time.time()
        try:
            res = gemini_client.models.generate_content(model="gemini-3.5-flash-lite", contents=[base_prompt, image])
            return parse_and_annotate_waldo(res.text or "", start_time, image, width, height, "Gemini 2.5 Flash (Alap)")
        except Exception as e:
            return {"model": "Gemini 3.5 Flash (Alap)", "response": f"Hiba: {e}", "found": False, "time": 0.0, "annotated_image": None}

    def query_gemini_ref():
        start_time = time.time()
        try:
            contents = [ref_prompt]
            if reference_image_bytes:
                ref_img = Image.open(io.BytesIO(reference_image_bytes)).convert("RGB")
                contents.insert(0, ref_img)
                contents.insert(1, "Keresendő referencia karakter:")
            contents.append(image)
            res = gemini_client.models.generate_content(model="gemini-3.5-flash-lite", contents=contents)
            return parse_and_annotate_waldo(res.text or "", start_time, image, width, height, "Gemini 2.5 Flash (Referenciával)")
        except Exception as e:
            return {"model": "Gemini 3.5 Flash (Referenciával)", "response": f"Hiba: {e}", "found": False, "time": 0.0, "annotated_image": None}

    # --- NEMOTRON FUNKCIÓK ---
    def query_openrouter_base():
        start_time = time.time()
        try:
            content_text = call_openrouter_chat(
                model="nvidia/nemotron-3.5-super-vl:free",
                content=base_payload,
                max_tokens=200,
                temperature=0,
            )
            return parse_and_annotate_waldo(content_text, start_time, image, width, height, "Nemotron 3.5 (Alap)")
        except Exception as e:
            return {"model": "Nemotron 3.5 (Alap)", "response": f"Hiba: {e}", "found": False, "time": 0.0, "annotated_image": None}

    def query_openrouter_ref():
        start_time = time.time()
        try:
            content_text = call_openrouter_chat(
                model="nvidia/nemotron-3.5-super-vl:free",
                content=ref_payload,
                max_tokens=200,
                temperature=0,
            )
            return parse_and_annotate_waldo(content_text, start_time, image, width, height, "Nemotron 3.5 (Referenciával)")
        except Exception as e:
            return {"model": "Nemotron 3.5 (Referenciával)", "response": f"Hiba: {e}", "found": False, "time": 0.0, "annotated_image": None}

    # Párhuzamos futtatás szálkezeléssel
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_gem_base = loop.run_in_executor(executor, query_gemini_base)
        f_gem_ref = loop.run_in_executor(executor, query_gemini_ref)
        f_or_base = loop.run_in_executor(executor, query_openrouter_base)
        f_or_ref = loop.run_in_executor(executor, query_openrouter_ref)

        results = await asyncio.gather(
            query_qwen_base(),
            query_qwen_ref(),
            f_gem_base,
            f_gem_ref,
            f_or_base,
            f_or_ref
        )

    waldo_progress[session_id] = {"current": 6, "total": 6, "message": "Kész!", "done": True}

    return WaldoRaceResponse(session_id=session_id, results=results)


@router.get("/waldo_progress/{session_id}")
async def get_waldo_progress(session_id: str):
    return waldo_progress.get(
        session_id,
        {"current": 0, "total": 6, "message": "Várakozás...", "done": False},
    )
