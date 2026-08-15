
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import chromadb
import uuid


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = genai.Client()
    app.state.gemini_client = client.aio
    yield

app = FastAPI(lifespan=lifespan, title="RAG, FastAPI és ChromaDB példa", version="1.0.0",
              description="Ez egy egyszerű példa a Retrieval-Augmented Generation (RAG) megvalósítására FastAPI és ChromaDB segítségével.")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="kurzus_tudasbazis")

# JAVÍTÁS: Az ID kikerült a bemeneti sémából, a felhasználónak csak a szöveget kell küldenie


class DocumentInput(BaseModel):
    text: str


class QueryInput(BaseModel):
    prompt: str


@app.post("/add_document")
async def add_document(doc: DocumentInput, request: Request):
    """1. Lépés: Dokumentumok feltöltése és vektorizálása (Automatikus ID-val)"""
    client = request.app.state.gemini_client

    # JAVÍTÁS: Automatikus, egyedi azonosító generálása a dokumentumnak
    doc_id = str(uuid.uuid4())

    try:
        # JAVÍTÁS: Itt TISZTÁN a modell neve szerepel, "models/" előtag nélkül!
        response = await client.models.embed_content(
            model="gemini-embedding-001",
            contents=doc.text
        )

        embedding = response.embeddings[0].values

        # Mentés a ChromaDB-be a generált azonosítóval
        collection.add(
            embeddings=[embedding],
            documents=[doc.text],
            ids=[doc_id]
        )

        # Visszaadjuk a generált ID-t is, hogy a felhasználó tudja, mi lett a rekord azonosítója
        return {
            "status": "ok",
            "doc_id": doc_id,
            "message": "Dokumentum sikeresen vektorizálva és elmentve."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask_rag")
async def ask_rag(query: QueryInput, request: Request):
    """2. Lépés: A tényleges RAG megvalósítása"""
    client = request.app.state.gemini_client

    try:
        # A. Kérdés vektorizálása ("models/" előtag nélkül!)
        query_response = await client.models.embed_content(
            model="gemini-embedding-001",
            contents=query.prompt
        )
        query_embedding = query_response.embeddings[0].values

        # B. Keresés a ChromaDB-ben
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2
        )

        context = " ".join(results['documents'][0])

        if not context:
            return {"response": "Nincs elegendő információ az adatbázisban a válaszhoz."}

        # C. Prompt összeállítása a kontextussal
        augmented_prompt = f"""
        Válaszold meg a felhasználó kérdését a megadott kontextus alapján. 
        Ha a kontextus nem tartalmazza a választ, mondd meg, hogy nem tudod.
        
        Kontextus: {context}
        
        Kérdés: {query.prompt}
        """

        # D. Generálás az MI modellel
        response = await client.models.generate_content(
            model="gemini-3.7-flash",
            contents=augmented_prompt
        )

        return {
            "retrieved_context": context,
            "llm_response": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list_documents")
def list_documents():
    """Segédvégpont: A ChromaDB-ben tárolt dokumentumok kilistázása"""
    try:
        # A .get() paraméterek nélkül a gyűjtemény (collection) összes elemét visszaadja
        # (Figyelem: hatalmas adatbázisoknál ezt paginálni (limit/offset) kellene,
        # de a mi kurzusunkhoz ez most tökéletes)
        results = collection.get()

        # Formázzuk a kimenetet egy tiszta listává
        docs = []
        # Ellenőrizzük, hogy vannak-e egyáltalán dokumentumok
        if results['ids']:
            for i in range(len(results['ids'])):
                docs.append({
                    "id": results['ids'][i],
                    "text": results['documents'][i]
                })

        return {
            "total_documents": len(docs),
            "documents": docs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")
