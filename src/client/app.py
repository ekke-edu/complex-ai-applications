import uuid
import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="MI RAG Rendszer",
                   page_icon="🤖", layout="centered")

st.title("Chat memory RAG rendszer MongoDB-vel")

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

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []

with tab2:
    st.header("💬 Intelligens Asszisztens")
    st.caption(
        f"Aktuális munkamenet azonosító: `{st.session_state.session_id}`")

    for msg in st.session_state.chat_history:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Írj egy üzenetet..."):

        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append(
            {"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Gondolkodik..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json={
                            "session_id": st.session_state.session_id,
                            "prompt": prompt
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        llm_reply = data.get("response")
                        st.markdown(llm_reply)

                        st.session_state.chat_history.append(
                            {"role": "model", "content": llm_reply})
                    elif response.status_code == 503:
                        st.warning(
                            "⚠️ Az MI szerverei jelenleg nagyon leterheltek. Kérlek, várj pár másodpercet, és próbáld újra!")
                    else:
                        st.error(
                            f"Hiba a szerver oldalon: {response.text}")
                except Exception:
                    st.error("❌ Nem tudok csatlakozni a backendhez.")
