# Komplex MI alkalmazások fejlesztése
Ebben a repóban egy modern, "State-of-the-Art" (SOTA) mesterséges intelligencia alkalmazás alapjait építjük fel. 

A projekt célja, hogy egy valós, skálázható szoftverarchitektúrát hozzunk létre, amely egy FastAPI backendből és egy Streamlit frontendből áll.

---

##  RAG és Vektoradatbázisok

Mielőtt belevágunk a kódolásba, fontos megérteni a projekt lelkét adó technológiákat. A modern Nagy Nyelvi Modellek (LLM-ek, mint a GPT-4 vagy a Gemini) lenyűgözőek, de van két komoly hibájuk:
1. **Hallucinálnak:** Ha nem tudják a választ, hajlamosak hihetően hangzó, de hamis információkat kitalálni.
2. **Nincs friss/privát tudásuk:** Nem látnak bele a vállalatod belső dokumentumaiba, vagy az egyetemi szabályzatokba.

Erre a problémára a iparági standard megoldás a **RAG (Retrieval-Augmented Generation)**.

### Mi az a Vektoradatbázis és az Embedding?
Ahhoz, hogy a gép "megértse" a szöveget, át kell alakítanunk azt számokká. Ezt a folyamatot hívjuk **beágyazásnak (embedding)**. Egy speciális MI modell a szövegeket többdimenziós térbeli pontokká (vektorokká) alakítja. 
* Ha két mondat jelentése hasonló (pl. "Kutya ugat" és "Ebgondolat"), a szoftveres térben a vektoraik nagyon közel lesznek egymáshoz.
* A **vektoradatbázis** (a mi esetünkben a `ChromaDB`) arra van optimalizálva, hogy pillanatok alatt megtalálja a térben egymáshoz legközelebb eső (leginkább releváns) vektorokat.

### Hogyan működik a RAG folyamat?
A RAG két fő lépésből áll, amelyeket az API-nk is leképez:
1. **Betáplálás (Ingestion):** A dokumentumainkat feldaraboljuk, embedding modellt használva vektorizáljuk, majd elmentjük a vektoradatbázisba.
2. **Kérdezés (Retrieval & Generation):** 
   * A felhasználó felteszi a kérdését.
   * A kérdést is vektorizáljuk.
   * Megkeressük a vektoradatbázisban a kérdéshez leginkább hasonló 2-3 bekezdést (Keresés/Retrieval).
   * Ezt a kigyűjtött, releváns kontextust átadjuk az LLM-nek a kérdéssel együtt, és megkérjük: *"Kizárólag a megadott kontextus alapján válaszold meg a kérdést!"* (Kiterjesztett Generálás/Augmented Generation).

---

## Technológiai Stack

A projekt a legmodernebb ipari standardokra épül:
* **Környezet:** Docker DevContainer (Garantálja, hogy minden csapattagnál ugyanúgy fusson a kód).
* **Backend:** `FastAPI` (Aszinkron, gyors, automatikus dokumentációval rendelkező API).
* **Frontend:** `Streamlit` (Gyors UI prototípus-fejlesztés Pythonban).
* **Vektoradatbázis:** `ChromaDB` (Lokális, pehelysúlyú adatbázis).
* **MI Integráció:** `google-genai` (A legújabb hivatalos SDK a Gemini modellekhez).

---

## Fejlesztői Környezet Indítása

### 1. Előfeltételek és Beállítások
Győződj meg róla, hogy a VS Code-ban a DevContainer sikeresen felépült.
Létre kell hoznod egy `.env` nevű fájlt a projekt gyökerében, amely tartalmazza a Google API kulcsodat:
```env
GEMINI_API_KEY=ide_masold_a_sajat_kulcsod
```

### 2. A Szolgáltatások Futtatása (A Makefile használata)
A projekt tartalmaz egy Makefile-t, amely leegyszerűsíti a szolgáltatások indítását. Ne feledd: a backendet és a frontendet két külön terminálablakban kell futtatnod!

A Backend API indítása:
Nyiss egy terminált, és add ki az alábbi parancsot. Ez elindítja a FastAPI szervert a http://localhost:8000 címen.
```bash
make run-api
```

> (Tipp: Nyisd meg a http://localhost:8000/docs oldalt a Swagger UI API dokumentáció eléréséhez, alapból átnavigál a /docs-ra ha csak a http://localhost:8000 címet ütöd be)

#### A Frontend UI indítása:
Nyiss egy ÚJ terminálablakot (a VS Code-ban a + ikonnal), és indítsd el a felhasználói felületet:
```bash
make run-app
```
> Ez automatikusan megnyitja a böngészőben a Streamlit alkalmazást (jellemzően a http://localhost:8501 címen).

### Project struktúra
```
/
├── src/
│   ├── backend/          
│   │   ├── __init__.py
│   │   └── api.py        # A FastAPI végpontok (a RAG logika)
│   └── frontend/
│       ├── __init__.py
│       └── app.py        # A Streamlit felhasználói felület
├── chroma_db/            # Ide menti a rendszer a vektorokat (automatikusan létrejön)
├── requirements.txt      # A projekt függőségeinek listája
├── Makefile              # Parancs-gyűjtemény a könnyű futtatáshoz
└── .env                  # Környezeti változók (NE KÜLDD BE GITHUB-RA!)
```