![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=Prometheus&logoColor=white)

# Komplex MI alkalmazások fejlesztése - MLOps

Az utolsó fázisban a projekt kiegészül a rendszer megfigyelhetőségével (Observability). 

## MLOps és Metrikák
A FastAPI backend aszinkron metrikákat szolgáltat a Prometheus számára. A begyűjtött adatokat egy Grafana dashboard segítségével vizualizáljuk, így valós időben nyomon követhető:
- Az LLM hívások válaszideje.
- A vektoradatbázis és a Neo4j lekérdezések teljesítménye.
- A rendszer általános terheltsége.

## ⚠️ Ismert jelenségek (Hibatűrés)
Mivel az alkalmazás élő felhőszolgáltatásokra (Google Gemini API) támaszkodik, előfordulhatnak terhelési tüskék a szervereiken. 
* Ha a felületen `503 UNAVAILABLE` (Leterheltség) hibát kapsz: a Google szerverei ideiglenesen túlterheltek. Várj pár másodpercet és próbáld újra elküldeni az üzenetet.
