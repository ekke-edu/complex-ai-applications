from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = genai.Client()

    app.state.gemini_client = client.aio

    yield

app = FastAPI(lifespan=lifespan)


class GenerateRequest(BaseModel):
    prompt: str
    model: str = "gemini-3.7-flash"


class GenerateResponse(BaseModel):
    text: str


@app.post("/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest, request: Request):
    client = request.app.state.gemini_client

    try:
        interaction = await client.interactions.create(
            model=payload.model,
            input=payload.prompt
        )

        return GenerateResponse(text=interaction.output_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    """Automatikusan átirányít a Swagger UI dokumentációra."""
    return RedirectResponse(url="/docs")
