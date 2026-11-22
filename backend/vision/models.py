import base64
import datetime
import io
import re
from typing import Any, List, Optional, Tuple, cast

import numpy as np
import cv2
from transformers import pipeline
import torch

from PIL import Image, ImageDraw
from pydantic import BaseModel, Field

from .schemas import BoundingBox, DetectionResponseSchema


# ==========================================
# ADATBÁZIS MODELLEK
# ==========================================

class DBChatMessageModel(BaseModel):
    session_id: str
    role: str
    content: str
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class DBVisionLogModel(BaseModel):
    session_id: str
    filename: str
    prompt: str
    response: str
    found: Optional[bool] = None
    box: Optional[List[int]] = None
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


# ==========================================
# ÜZLETI LOGIKA / DETEKTOR
# ==========================================

class VisionDetector:
    """Objektumdetektálásért és képvágásért felelős osztály."""

    def __init__(self, groq_client: Any, model_name: str = "qwen/qwen3.8-27b"):
        self.groq_client = groq_client
        self.model_name = model_name

    @staticmethod
    def _build_prompt(target_prompt: str) -> str:
        return (
            f"Feladat: keresd meg a következő objektumot/elemet a képen: '{target_prompt}'.\n"
            "A válaszod első sora pontosan az alábbiak egyike legyen:\n"
            "FOUND: NO\n"
            "vagy\n"
            "FOUND: YES [ymin, xmin, ymax, xmax]\n\n"
            "A koordináták a TELJES KÉPRE vonatkozzanak, 0–1000 közötti skálán. "
            "A sorrend: felső, bal, alsó, jobb."
        )

    @staticmethod
    def _parse_coordinates(reply_text: str) -> Optional[BoundingBox]:
        if re.search(r"FOUND\s*:\s*NO", reply_text, re.IGNORECASE):
            return None

        match = re.search(
            r"FOUND\s*:\s*YES\s*\[\s*(\d{1,4})\s*,\s*(\d{1,4})\s*,\s*(\d{1,4})\s*,\s*(\d{1,4})\s*\]",
            reply_text,
            re.IGNORECASE,
        )
        if not match:
            return None

        ymin, xmin, ymax, xmax = map(int, match.groups())
        return BoundingBox(
            ymin=min(1000, ymin),
            xmin=min(1000, xmin),
            ymax=min(1000, ymax),
            xmax=min(1000, xmax),
        )

    @staticmethod
    def _encode_image_to_base64(image: Image.Image, quality: int = 92) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _process_images(
        self, image: Image.Image, pixel_box: List[int]
    ) -> Tuple[str, str]:
        width, height = image.size

        # 1. Keretezett kép generálása
        annotated = image.copy()
        draw = ImageDraw.Draw(annotated)
        line_width = max(4, round(min(width, height) / 250))
        draw.rectangle(pixel_box, outline="red", width=line_width)
        annotated_b64 = self._encode_image_to_base64(annotated)

        # 2. Kivágott kép generálása
        cropped = image.crop(tuple(pixel_box))
        cropped_b64 = self._encode_image_to_base64(cropped)

        return annotated_b64, cropped_b64

    async def detect_and_crop(
        self,
        session_id: str,
        prompt: str,
        image_bytes: bytes,
        filename: Optional[str] = None,
        mime_type: str = "image/jpeg",
    ) -> DetectionResponseSchema:
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            raise ValueError("A feltöltött fájl nem olvasható képfájl.") from exc

        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        detection_prompt = self._build_prompt(prompt)

        response = await cast(Any, self.groq_client.chat.completions).create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": detection_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=300,
            temperature=0,
        )

        reply_text = response.choices[0].message.content or ""
        bbox = self._parse_coordinates(reply_text)

        if not bbox:
            return DetectionResponseSchema(
                session_id=session_id,
                response="A modell nem találta meg a keresett objektumot a képen.",
                found=False,
                filename=filename,
            )

        width, height = image.size
        pixel_box = bbox.to_pixel_coords(width, height)

        if pixel_box[2] <= pixel_box[0] or pixel_box[3] <= pixel_box[1]:
            return DetectionResponseSchema(
                session_id=session_id,
                response="A modell érvénytelen vágási koordinátákat adott vissza.",
                found=False,
                filename=filename,
            )

        annotated_b64, cropped_b64 = self._process_images(image, pixel_box)

        return DetectionResponseSchema(
            session_id=session_id,
            response=f"Sikeres detektálás!\n{reply_text}",
            found=True,
            box=pixel_box,
            annotated_image=annotated_b64,
            cropped_image=cropped_b64,
            filename=filename,
        )


class DepthEstimator:
    """Depth Anything V2 alapú mélységbecslésért felelős osztály."""

    def __init__(self):
        self._pipelines = {}

    def _get_pipeline(self, model_size: str):
        model_map = {
            "small": "depth-anything/Depth-Anything-V2-Small-hf",
            "base": "depth-anything/Depth-Anything-V2-Base-hf",
            "large": "depth-anything/Depth-Anything-V2-Large-hf"
        }
        model_id = model_map.get(model_size, model_map["small"])

        if model_id not in self._pipelines:
            # Ha van GPU (CUDA), használja azt (device=0), különben CPU (-1)
            device = 0 if torch.cuda.is_available() else -1
            self._pipelines[model_id] = pipeline(task="depth-estimation", model=model_id, device=device)

        return self._pipelines[model_id]

    @staticmethod
    def _apply_colormap(depth_pil: Image.Image, colormap_name: str) -> str:
        depth_np = np.array(depth_pil)

        # Normalizálás 0-255 tartományba, ha szükséges
        if depth_np.dtype != np.uint8:
            depth_np = cv2.normalize(depth_np, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Színskála kiválasztása OpenCV alapján
        cmap_dict = {
            "inferno": cv2.COLORMAP_INFERNO,
            "viridis": cv2.COLORMAP_VIRIDIS,
            "szürkeárnyalatos": None,
            "grayscale": None
        }

        cv_map = cmap_dict.get(colormap_name, cv2.COLORMAP_INFERNO)

        if cv_map is not None:
            colored = cv2.applyColorMap(depth_np, cv_map)
        else:
            colored = cv2.cvtColor(depth_np, cv2.COLOR_GRAY2BGR)

        # Visszakódolás Base64-be
        _, buffer = cv2.imencode(".png", colored)
        return base64.b64encode(buffer).decode("utf-8")

    async def estimate_depth(
            self,
            session_id: str,
            image_bytes: bytes,
            colormap: str = "inferno",
            model_size: str = "small",
            filename: Optional[str] = None,
    ) -> dict:
        import time
        start_time = time.time()

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            raise ValueError("A feltöltött fájl nem olvasható képfájl.") from exc

        pipe = self._get_pipeline(model_size)
        result = pipe(image)

        # A pipeline visszad egy 'depth' nevű PIL képet
        depth_pil = result["depth"]

        # Ha a kimeneti kép mérete eltérne az eredetitől, átméretezhetjük,
        # de a pipeline alapból jól kezeli.
        depth_b64 = self._apply_colormap(depth_pil, colormap)

        duration = time.time() - start_time

        return {
            "session_id": session_id,
            "duration": duration,
            "depth_image": depth_b64,
            "filename": filename,
        }
