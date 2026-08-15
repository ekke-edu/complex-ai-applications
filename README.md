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

---

## Zárófeladat Kiírás (`finals`)

A félév lezárásaként egy önálló, komplex záróprojektet kell készítenetek a `finals` branch (vagy a saját Neptun-kódos mappátok) alapján. 

### A Feladat Feltételei és Szabályai:

1. **Szabad Téma / Domain:** 
   A téma teljesen szabadon választott (pl. e-commerce asszisztens, okos oktatási rendszer, sci-fi lore adatbázis, pénzügyi számlaelemző, stb.). A lényeg, hogy egy valós problémát oldjon meg.
2. **Kötelező Technológiai Stack:**
   A félév során megismert összes fő komponenst integrálnotok kell a projektbe:
   * Aszinkron **FastAPI** backend & **Streamlit** frontend (Docker DevContainer környezetben).
   * **ChromaDB** (Vektor-alapú RAG).
   * **MongoDB** (Állapottartó chat memória / session kezelés).
   * **Neo4j** (Tudásgráf és GraphRAG vizualizáció).
   * **Prometheus & Grafana** (Rendszer- és teljesítménymonitorozás).
3. **🚫 Szigorú Korlátozás (Nincs Gemini API!):**
   Mivel az órákon a Google Gemini API-t használtuk példaként, a zárófeladatban **TILOS a Gemini API használata!** Helyette más külső LLM szolgáltatót (pl. *OpenAI GPT-4o*, *Anthropic Claude*, *Mistral AI*) vagy egy helyi, nyílt forráskódú modellt (pl. *Ollama* / Llama 3) kell integrálnotok a backendbe.
4. **Benyújtás (Neptun-kód alapján):**
   A munkátokat a saját **Neptun-kódotokkal azonosított mappában** (vagy ágon) kell benyújnotok a repóban, amelynek tartalmaznia kell a teljes forráskódot, a `docker-compose.yml` fájlt, a frissített `README.md`-t (benne a választott téma leírásával és a futtatási útmutatóval), valamint a `.env.example` fájlt (kulcsok nélkül).

Sok sikert a megvalósításhoz! Mutassátok meg, mit építettetek ki a félév alatt!