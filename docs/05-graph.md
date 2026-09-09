![Neo4j](https://img.shields.io/badge/Neo4j-018bff?style=flat&logo=neo4j&logoColor=white)

# Komplex MI alkalmazások fejlesztése

## 4. Tudásgráfok és GraphRAG (Neo4j)
A vektorok jók a szemantikai hasonlóság keresésére, de a pontos relációk (pl. "Ki kinek a felettese?") megtalálásához hálózatokra van szükség. A bemeneti szövegekből az MI entitás-kapcsolat hármasokat (Triples) nyer ki, amelyeket egy **Neo4j gráfadatbázisban** tárolunk, a felületen pedig a `streamlit-agraph` segítségével vizuálisan, interaktívan is megjelenítünk.

```mermaid
graph LR
    A[Nyers Szöveg] -->|API Kérés| B(Gemini 3.5 Flash)
    B -->|Entitás Kinyerés| C{JSON Triples}
    C -->|Relációk| D[(Neo4j Gráfadatbázis)]
    C -->|Vizuális Render| E[Streamlit UI - Agraph]
```
