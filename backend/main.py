import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from core.config import lifespan, UPLOAD_DIR
from vision import router as vision_routers
from invoices import router as invoice_routers
from waldo import router as waldo_routers
from backend.chess_logic.router import router as chess_router
from backend.video.router import router as video_router

load_dotenv()

app = FastAPI(
    title="RAG, FastAPI és Számla Elemző Rendszer",
    version="1.2.0",
    description="Multimodális megvalósítás Groq LPU és Qwen modellek segítségével.",
    lifespan=lifespan
)

# Statikus mappák
app.mount("/static/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Routerek regisztrálása
app.include_router(vision_routers.router)
app.include_router(invoice_routers.router)
app.include_router(waldo_routers.router)
app.include_router(chess_router)
app.include_router(video_router)

@app.get("/get_image/{filename}", include_in_schema=False)
def get_uploaded_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="A kép nem található.")

@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")
