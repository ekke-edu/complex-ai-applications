# Komplex MI alkalmazások fejlesztése

Ez a projekt egy FastAPI alapú API, amely a Google Gemini modellek segítségével generál szöveget egy `POST /generate` végpontból.

## Első lépések

A projekt használata előtt készítsd el a környezeti változókat a saját API kulcsodhoz.

1. Hozz létre egy `.env` fájlt a projekt gyökérkönyvtárában.
2. Add hozzá a Gemini API kulcsodat:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

> Fontos: a `.env` fájlt NE commitold a Git repository-ba, mert a projekt `.gitignore` már kizárja ezt a fájlt.

## Előfeltételek

- Python 3.10+
- pip
- Google Gemini API kulcs

## Telepítés

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Futtatás

A projekt futtatásához a legkönnyebb mód a `Makefile` használata:

```bash
make run
```

Vagy közvetlenül:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Miután elindult, az API dokumentáció itt érhető el:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Használat

### 1. Generálás kérés

A fő endpoint:

```http
POST /generate
```

Request body például:

```json
{
  "prompt": "Írj egy rövid összefoglalót a mesterséges intelligenciáról.",
  "model": "gemini-3.7-flash"
}
```

Válasz:

```json
{
  "text": "A mesterséges intelligencia olyan technológiák összessége,..."
}
```

### 2. Swagger UI

Nyisd meg a böngészőben a dokumentációs felületet:

```text
http://localhost:8000/docs
```

> Itt közvetlenül tudsz kéréseket küldeni a végpontra.

## Példa cURL parancs

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Írj egy rövid, barátságos üzenetet a projekt kezdéséhez.",
    "model": "gemini-3.7-flash"
  }'
```

## Hibakeresés

Ha hibaüzenetet kapsz, ellenőrizd, hogy:

- a `.env` fájl létezik,
- a `GEMINI_API_KEY` helyes,
- a Google Gemini API hozzáférés aktiválva van,
- az alkalmazás fut a projekt gyökérkönyvtárából.

Ha a kulcs nincs megadva, a Gemini kliens nem tud kapcsolódni a szolgáltatáshoz.

## Fájlok áttekintése

- `main.py`: FastAPI alkalmazás és a `/generate` végpont
- `requirements.txt`: Python függőségek
- `.env`: helyi környezeti változók (nem kerül a Gitbe)
- `Makefile`: egyszerű futtatási parancsok


