# Komplex MI alkalmazások fejlesztése
Ez a projekt egy modern, "State-of-the-Art" mikroszolgáltatás-alapú mesterséges intelligencia rendszert mutat be, amelyet lépésről lépésre, az alábbi fejlesztési fázisokon (`features`) keresztül építettem fel.

---

## A Félév Ütemterve (Branch Agenda)

A repository ágai a szoftverarchitektúra fokozatos bővülését követik:

* **`feature/01_fastapi-geminiapi`** – **Alapozás és API:** Aszinkron FastAPI backend.
* **`feature/02_rag-vector-database`** – **Vektoros RAG:** Dokumentumok feldolgozása és szemantikai keresése lokális ChromaDB vektoradatbázisban.
* **`feature/03_chat-memory-mongodb`** – **Állapottartó Memória:** Session-alapú beszélgetéstörténet tárolása NoSQL MongoDB adatbázisban.
* **`feature/04_multimodal-vision`** – **Multimodális Látás:** Képek és vizuális dokumentumok közvetlen elemzése a modell segítségével.
* **`feature/05_graph-rag-neo4j`** – **Tudásgráfok és GraphRAG:** Entitás-kapcsolat hármasok kinyerése és tárolása Neo4j gráfadatbázisban, interaktív `streamlit-agraph` vizualizációval.
* **`feature/06_mlops-docker-grafana`** – **Megfigyelhetőség (MLOps):** Valós idejű teljesítménymérés Prometheus metrikákkal és egyedi Grafana műszerfalakkal.
