# Komplex MI alkalmazások fejlesztése

## 3. Multimodális Gépi Látás (Vision)
A rendszer képes képeket (számlákat, diagramokat, vizuális adatokat) fogadni és feldolgozni a Gemini 1.5 Flash modell segítségével, ami közvetlenül strukturált adatokat vagy elemzést generál a bináris fájlokból.

### Az Adatfolyam Vizualizációja (Multimodális Látvány)
Az alábbi ábra bemutatja, hogyan utazik egy képes-szöveges kérés a kliensgéptől egészen az MI szerveréig és vissza:

```mermaid
sequenceDiagram
    actor User as Felhasználó (Streamlit)
    participant API as FastAPI Backend
    participant Mongo as MongoDB
    participant Gemini as Google Gemini API

    User->>API: 1. POST /chat_with_image (Kép bytes + Kérdés text)
    activate API
    API->>API: 2. Kép memóriába konvertálása (PIL / io.BytesIO)
    API->>Gemini: 3. generate_content([Kép, Kérdés])
    activate Gemini
    Gemini-->>API: 4. Elemzés / Válasz visszatérése
    deactivate Gemini
    API->>Mongo: 5. Kérés és Válasz aszinkron mentése (Chat History)
    Mongo-->>API: Sikeres mentés (Ack)
    API-->>User: 6. JSON válasz (Szöveg + Képfájl metaadat)
    deactivate API
    User->>User: 7. Frontend frissíti a UI-t (Új üzenet a chaten)
```
