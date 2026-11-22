from typing import Any, Optional, List
from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import cast
from fastapi import Request
from fastapi.datastructures import State
from groq import AsyncGroq
from motor.motor_asyncio import AsyncIOMotorClient

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class AppState(State):
    groq_client: AsyncGroq
    mongo_client: AsyncIOMotorClient
    chat_collection: Any

@asynccontextmanager
async def lifespan(app: Any):
    groq_client = AsyncGroq()
    app.state.groq_client = groq_client

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_client = mongo_client
    app.state.chat_collection = mongo_client["mi_kurzus"]["chat_history"]

    try:
        yield
    finally:
        mongo_client.close()
        await groq_client.close()

def get_app_state(request: Request) -> AppState:
    return cast(AppState, request.app.state)
