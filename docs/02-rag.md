![ChromaDB](https://img.shields.io/badge/ChromaDB-FC5E20?style=flat)

# Komplex MI alkalmazások fejlesztése
Ebben a repóban egy modern, "State-of-the-Art" (SOTA) mesterséges intelligencia alkalmazás alapjait építjük fel. 

##  RAG és Vektoradatbázisok

Mielőtt belevágunk a kódolásba, fontos megérteni a projekt lelkét adó technológiákat. A modern Nagy Nyelvi Modellek (LLM-ek, mint a GPT-4 vagy a Gemini) lenyűgözőek, de van két komoly hibájuk:
1. **Hallucinálnak:** Ha nem tudják a választ, hajlamosak hihetően hangzó, de hamis információkat kitalálni.
2. **Nincs friss/privát tudásuk:** Nem látnak bele a vállalatod belső dokumentumaiba.

Erre a problémára a iparági standard megoldás a **RAG (Retrieval-Augmented Generation)**.

### Mi az a Vektoradatbázis és az Embedding?
Ahhoz, hogy a gép "megértse" a szöveget, át kell alakítanunk azt számokká. Ezt a folyamatot hívjuk **beágyazásnak (embedding)**. Egy speciális MI modell a szövegeket többdimenziós térbeli pontokká (vektorokká) alakítja. A **vektoradatbázis** (a mi esetünkben a `ChromaDB`) arra van optimalizálva, hogy pillanatok alatt megtalálja a térben egymáshoz legközelebb eső (leginkább releváns) vektorokat.

### Hogyan működik a RAG folyamat?
1. **Betáplálás (Ingestion):** A dokumentumainkat feldaraboljuk, vektorizáljuk, majd elmentjük a vektoradatbázisba.
2. **Kérdezés (Retrieval & Generation):** Megkeressük a vektoradatbázisban a kérdéshez leginkább hasonló bekezdést, és átadjuk az LLM-nek a kérdéssel együtt.

## Fejlesztői Környezet Indítása

```bash
make run-api
make run-app
```
