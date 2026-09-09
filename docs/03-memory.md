![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=flat&logo=mongodb&logoColor=white)

# Komplex MI alkalmazások fejlesztése

A projekt célja, hogy a hagyományos "Jupyter Notebook" szintű kísérletezésen túllépve, egy valós, skálázható szoftverarchitektúrát hozzunk létre.

##  RAG és a "Memória"

### 2. Állapottartó (Stateful) Beszélgetés és NoSQL
Ahhoz, hogy a gép emlékezzen a beszélgetés fonalára, bevezettünk egy **MongoDB (NoSQL) adatbázist**. 
* **Miért NoSQL?** Az MI-vel folytatott beszélgetések természetes módon JSON/dokumentum formátumúak, amire a MongoDB tökéletes választás. A relációs adatbázisok (SQL) ehhez túl merevek lennének.
* A rendszer generál egy `session_id`-t, és minden üzenetváltást letárol, így a következő kérdésnél a FastAPI a teljes beszélgetési előzményt fel tudja tölteni a modell memóriájába.

## Csatlakozás a MongoDB-hez (VS Code Plugin)
Nem kell vaktában kódolnod! A DevContainer tartalmaz egy hivatalos MongoDB kiterjesztést.
A fenti parancssorba írd be: `mongodb://mongo:27017` majd nyomj Entert.
