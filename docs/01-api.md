![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=flat&logo=googlegemini&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat&logo=pydantic&logoColor=white)

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

## Használat

Nyisd meg a böngészőben a dokumentációs felületet:

```text
http://localhost:8000/docs
```
