import base64
import datetime
import os
import subprocess
import tempfile
from typing import Any, Optional, cast

import cv2
import imageio_ffmpeg
from pydantic import BaseModel, Field


# ==========================================
# ADATBÁZIS / LOG MODELLEK
# ==========================================

class DBVideoLogModel(BaseModel):
    session_id: str
    filename: str
    prompt: str
    transcript: str
    vision_analysis: str
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


# ==========================================
# VIDEÓ ELEMZŐ (Whisper + Qwen VLM)
# ==========================================

class VideoAnalyzer:
    """Videók hangjának átírásáért (Whisper) és képkockák elemzéséért (VLM) felelős osztály."""

    def __init__(self, groq_client: Any, model_name: str = "qwen/qwen3.8-27b"):
        self.groq_client = groq_client
        self.model_name = model_name

    async def analyze_video(
            self,
            session_id: str,
            video_bytes: bytes,
            prompt: str,
            filename: Optional[str] = None,
            language: str = "hu",
    ) -> dict:
        ext = os.path.splitext(filename or "")[1].lower()
        if ext not in (".mp4", ".mkv"):
            ext = ".mp4"

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_video:
            tmp_video.write(video_bytes)
            tmp_video_path = tmp_video.name

        try:
            # 1. HANG KINYERÉSE ÉS ÁTÍRÁSA (Groq Whisper API)
            transcript_text = "Nem található hang a videóban vagy hiba történt az átírás során."
            tmp_audio_path = f"{tmp_video_path}.mp3"
            try:
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                subprocess.run(
                    [
                        ffmpeg_exe, "-y",
                        "-i", tmp_video_path,
                        "-vn",
                        "-ac", "1",
                        "-ar", "16000",
                        "-b:a", "32k",
                        tmp_audio_path,
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                audio_source_path = tmp_audio_path if os.path.exists(tmp_audio_path) else tmp_video_path
                audio_filename = (os.path.splitext(filename or "video.mp4")[0]) + ".mp3"

                with open(audio_source_path, "rb") as audio_file:
                    transcription = await self.groq_client.audio.transcriptions.create(
                        file=(audio_filename, audio_file.read()),
                        model="whisper-large-v3",
                        language=language,
                        response_format="text"
                    )
                    if isinstance(transcription, str):
                        transcript_text = transcription
                    elif isinstance(transcription, dict):
                        transcript_text = transcription.get("text", "")
                    else:
                        transcript_text = getattr(transcription, "text", str(transcription))
            except Exception as e:
                transcript_text = f"Hangátírás nem sikerült: {str(e)}"
            finally:
                if os.path.exists(tmp_audio_path):
                    os.remove(tmp_audio_path)

            # 2. KÉPKOCKÁK KINYERÉSE (OpenCV segítségével)
            content_items = [
                {
                    "type": "text",
                    "text": f"Feladat a videóhoz: {prompt}\n\nA videóban elhangzott beszéd leirata (Whisper): {transcript_text}",
                }
            ]

            cap = cv2.VideoCapture(tmp_video_path)
            try:
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
                max_frames_to_extract = 3
                step = max(1, total_frames // max_frames_to_extract) if total_frames > 0 else 30

                frame_count = 0
                extracted_count = 0
                while cap.isOpened() and extracted_count < max_frames_to_extract:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        break

                    if frame_count % step == 0:
                        resized = cv2.resize(frame, (640, 360))
                        _, buffer = cv2.imencode(".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        b64_frame = base64.b64encode(buffer).decode("utf-8")

                        content_items.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_frame}"},
                        })
                        extracted_count += 1

                    frame_count += 1
            finally:
                cap.release()

            # 3. VIZUÁLIS ELEMZÉS A GROQ VISION MODELLEL (Qwen)
            response = await cast(Any, self.groq_client.chat.completions).create(
                model=self.model_name,
                messages=[{"role": "user", "content": content_items}],
                max_tokens=1000,
            )

            vision_analysis = response.choices[0].message.content or "Nincs vizuális elemzés."

            return {
                "session_id": session_id,
                "transcript": transcript_text,
                "vision_analysis": vision_analysis,
                "filename": filename,
            }

        finally:
            if os.path.exists(tmp_video_path):
                os.remove(tmp_video_path)
