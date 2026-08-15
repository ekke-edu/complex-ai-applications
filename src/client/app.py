import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="MI RAG Rendszer",
                   page_icon="🤖", layout="centered")

st.title("🤖 MI Kurzus - Tudásbázis és RAG")

tab1, tab2, tab3 = st.tabs(
    ["📚 Dokumentum Feltöltése", "💬 Kérdezés a rendszertől", "🗂️ Adatbázis tartalma"])

with tab1:
    st.header("Új ismeret betáplálása")
    doc_text = st.text_area(
        "Másolj be ide egy szakmai szöveget, szabályzatot vagy leírást:", height=200)

    if st.button("Vektorizálás és Mentés", type="primary"):
        if doc_text.strip() == "":
            st.warning("Kérlek, írj be valamilyen szöveget!")
        else:
            with st.spinner('Feldolgozás és embedding generálás...'):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/add_document",
                        json={"text": doc_text}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Siker! {data.get('message')}")
                        st.info(f"Generált azonosító: {data.get('doc_id')}")
                    else:
                        st.error(f"Hiba a szerver oldalon: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error(
                        "❌ Nem tudok csatlakozni a FastAPI backendhez. Biztosan elindítottad az Uvicornt?")

with tab2:
    st.header("Tudásalapú Kérdezz-Felelek")
    user_query = st.text_input(
        "Tedd fel a kérdésedet az adatbázis tartalmával kapcsolatban:")

    if st.button("Válasz generálása", type="primary"):
        if user_query.strip() == "":
            st.warning("Kérlek, írd be a kérdésed!")
        else:
            with st.spinner('Keresés az adatbázisban és válasz generálása...'):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/ask_rag",
                        json={"prompt": user_query}
                    )

                    if response.status_code == 200:
                        data = response.json()

                        st.markdown("### 🤖 MI Válasza:")
                        st.write(data.get("llm_response"))

                        with st.expander("🔍 Kulisszatitkok: Ebből a kontextusból dolgozott a modell"):
                            st.write(data.get("retrieved_context"))
                    else:
                        st.error(f"Hiba a szerver oldalon: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Nem tudok csatlakozni a backendhez.")

with tab3:
    st.header("Feltöltött dokumentumok listája")
    if st.button("Frissítés"):
        try:
            response = requests.get(f"{API_BASE_URL}/list_documents")
            if response.status_code == 200:
                data = response.json()
                st.metric("Összes dokumentum", data.get("total_documents"))

                for doc in data.get("documents", []):
                    st.text_area(
                        f"ID: {doc['id']}", doc['text'], height=100, disabled=True)
            else:
                st.error("Nem sikerült lekérni az adatokat.")
        except Exception:
            st.error("❌ Nem tudok csatlakozni a backendhez.")
