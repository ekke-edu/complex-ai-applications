# Képesség: MkDocs-dokumentáció létrehozása és karbantartása

## Cél

Készíts és frissíts a projekt szerkezetéhez, nyelvi beállításaihoz és tényleges MkDocs-konfigurációjához illeszkedő dokumentációt. A feladat lehet új oldal, meglévő oldal tartalmi vagy formai javítása, navigáció módosítása, illetve a dokumentációs build hibáinak javítása.

## Mikor használd

Aktiváld, ha a kérés MkDocs-oldal, a `docs/` tartalma, az `mkdocs.yml`, a dokumentáció nyelvi változatai vagy a dokumentáció buildje/deploya körül forog. Ne módosíts dokumentációs fájlokat nem kapcsolódó kódmódosítás során.

## A projekt dokumentációs szerződése

Módosítás előtt olvasd el a gyökérbeli `mkdocs.yml`-t, az érintett oldalakat a `docs/` könyvtárban és szükség esetén a `.github/workflows/docs.yml` fájlt. A konfiguráció az irányadó; ne feltételezz olyan plugint, Markdown-kiterjesztést vagy build-parancsot, amelyet nem találsz meg.

- MkDocs-konfiguráció: gyökérbeli `mkdocs.yml`.
- Közzétett Markdown-források: `docs/`.
- Téma: Material for MkDocs; a felület alapnyelve magyar.
- Nyelvek: magyar (`hu`, alapértelmezett) és angol (`en`), mindkettő buildelve.
- Az `i18n` plugin `docs_structure: suffix` módot használ. A magyar oldalak neve például `01-api.md`, angol párjuké `01-api.en.md`; a magyar kezdőlap `index.md`, az angol `index.en.md`.
- A `nav` a magyar oldalak útvonalait sorolja fel. Az angol változatokat a suffix-alapú i18n struktúra kezeli; ne vegyél fel külön, `.en.md` végű nav-bejegyzést. Új oldalnál a menü nevét szükség esetén egészítsd ki a `nav_translations` angol fordításával.
- A GitHub Actions deploy workflow a `main` ágon, a `docs/**`, `mkdocs.yml` vagy a workflow fájl változásakor indul, és egy központi újrafelhasználható workflow-t hív meg. A `.github/agents/` tartalma nem része a publikált dokumentációnak, és önmagában nem indít deployt.
- A repositoryban nincs `requirements.txt`, `pyproject.toml` vagy más MkDocs-függőségeket rögzítő manifest. Ne találj ki függőséget, helyi telepítést vagy működő parancsot; előbb ellenőrizd, hogy az eszköz ténylegesen elérhető-e.

## Tartalom- és konfigurációs szabályok

1. **Két nyelv:** Új, navigációba kerülő oldalhoz alapértelmezés szerint készíts magyar és angol változatot a suffix-konvenció szerint. Ha a kérés egyértelműen csak egy nyelvre szól, ne készíts kéretlen fordítást; jelezd, ha emiatt a másik nyelvű oldal hiányos marad. Meglévő tartalom frissítésekor tartsd szinkronban a párját, hacsak a felhasználó másként nem kéri.
2. **Navigáció:** Új oldal magyar útvonalát pontosan egyszer illeszd be a `mkdocs.yml` megfelelő `nav` szakaszába. Ellenőrizd az útvonalat, a menücím sorrendjét és az angol `nav_translations` értékét. Ne hagyj navigációból elérhetetlennek szánt oldalt árva fájlként.
3. **Nyelv és állítások:** A magyar oldal természetes, következetes magyar szöveget használjon; az angol változat legyen tartalmilag egyező, ne szó szerinti, hibás fordítás. A technikai parancsokat, útvonalakat, kódot és API-neveket pontosan tartsd meg. A projekt aktuális működését a kódból és konfigurációból ellenőrizd, ne másold át automatikusan az esetleg elavult állításokat.
4. **Markdown és kód:** Használj áttekinthető címsor-hierarchiát, rövid bekezdéseket, rendezett vagy rendezetlen listát ott, ahol segíti az olvasást. Minden kódblokkhoz adj meg megfelelő nyelvi jelölést; parancskimenethez használható például `text`. A példák legyenek futtathatók vagy egyértelműen illusztratívak, és ne tartalmazzanak valódi titkot, kulcsot vagy személyes adatot.
5. **Bővített Markdown:** Admonitiont, kódannotációt, speciális táblázatot vagy más Material/Python-Markdown szintaxist csak akkor használj, ha az ehhez szükséges kiterjesztés ténylegesen engedélyezett. A Material téma önmagában nem bizonyítja, hogy minden kiterjesztés aktív.
6. **Diagramok:** Mermaid-diagramot csak működő Mermaid-renderelési beállítás mellett adj hozzá. A jelenlegi `mkdocs.yml` nem deklarál Mermaid-integrációt vagy `pymdownx.superfences`-t; egy `mermaid` nyelvjelölésű blokk ezért önmagában nem garantál renderelt diagramot. Ha diagram a kérés része, ellenőrizd a build-beállítást, és csak a szükséges, feladatba illő konfigurációval együtt használd.
7. **HTML:** Kerüld a nyers HTML-t, ha Markdown is megfelel. HTML-t csak akkor használj, ha a szükséges kiterjesztés engedélyezett és az elem indokolt.
8. **Linkek és képek:** Az oldalak közötti hivatkozásokat relatív, a MkDocs-forrásszerkezethez illő Markdown-linkként írd. Ellenőrizd a célfájl létezését, a horgonyszöveget és a magyar/angol céloldalt. Kép esetén részesítsd előnyben a repositoryban tárolt, releváns assetet és adj értelmes alternatív szöveget; ne hivatkozz nem létező helyi fájlra. A jelenlegi konfiguráció nem jelez törött linkeket kereső plugint, ezért a build eredményét ne tekintsd teljes linkellenőrzésnek.
9. **Hatókör:** Csak a kéréshez szükséges oldalakat, navigációt és közvetlenül kapcsolódó konfigurációt változtasd. Ne adj hozzá plugint, függőséget, kézi deploy-lépést vagy új dokumentációs rendszert külön indok nélkül.

## Munkafolyamat

1. **Felmérés:** Nézd meg a `mkdocs.yml`-t, az érintett magyar és angol oldalakat, a rokon oldalak stílusát, valamint konfigurációs vagy deployfeladatnál a workflow-t. Ellenőrizd, hogy a célfájlok és a nav-bejegyzés már léteznek-e; őrizd meg a munkafában talált, nem kapcsolódó módosításokat.
2. **Tényellenőrzés:** Dokumentáld a projekt valós viselkedését. Ha egy állítás nem támasztható alá forrásból, konfigurációból vagy a felhasználó által megadott követelményből, ne állítsd biztos tényként.
3. **Szerkesztés:** Módosítsd a szükséges oldalakat a meglévő számozási, fájlnév- és nyelvi konvenció szerint. Új oldalnál frissítsd a navot és a megfelelő fordításokat is. Konfigurációs változás esetén gondoskodj róla, hogy az mindkét nyelv buildjével összhangban maradjon.
4. **Ellenőrzés:** Ellenőrizd a fájlneveket, a nav célútvonalait, a nyelvi párokat, a Markdown-szintaxist és az összes új vagy módosított belső hivatkozást. Vizsgáld meg a diffet is, hogy ne kerüljön bele kéretlen változás.
5. **Build:** Ha az MkDocs telepítve van a rendelkezésre álló környezetben, futtasd a repositoryhoz illő buildet, például `mkdocs build --strict`-et. Ha a parancs vagy valamely szükséges plugin hiányzik, jelezd pontosan a korlátozást; ne telepíts függőséget engedély nélkül, és ne állíts sikeres buildet ellenőrzés nélkül. A build csak a generált konfigurációt és tartalmat ellenőrzi; a nem konfigurált linkellenőrzést nem helyettesíti.
6. **Összegzés:** Röviden sorold fel a módosított fájlokat, az elvégzett ellenőrzéseket és az esetleges nyitott korlátozásokat.

## A jelenlegi konfiguráció fontos korlátai

A jelenlegi `mkdocs.yml` Material témát, `search` és `i18n` plugint, valamint suffix-alapú magyar/angol struktúrát állít be. Nem deklarál `markdown_extensions`-t, admonition- vagy kódannotáció-beállítást, Mermaid-renderelést, illetve linkellenőrző plugint. Ezeket minden feladatnál ellenőrizd újra a fájl aktuális állapotában, és ne kezeld automatikusan támogatottnak.
