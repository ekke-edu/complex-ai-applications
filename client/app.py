import uuid
import streamlit as st

# Modulok importálása a views mappából
from views.vision_tab import render_vision_tab
from views.waldo_tab import render_waldo_tab
from views.invoice_tab import render_invoice_tab
from views.chess_tab import render_chess_tab
from views.video_tab import render_video_tab

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Multimodális AI & Gépi Látás Stúdió (Groq Qwen)", page_icon="⚡", layout="wide")

# Session ID inicializálása
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("⚡ Multimodális AI & Gépi Látás Stúdió Groq Qwen-val")

# BAL OLDALI SÁV (Globális beállítások vagy információk)
st.sidebar.title("🧭 Információ")
st.sidebar.divider()
st.sidebar.caption(f"Session ID:\n`{st.session_state.get('session_id', 'Nincs')}` ")

# --- FŐOLDALI FÜLEK LÉTREHOZÁSA ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👁️ Gépi Látás & Képvágás",
    "🎯 Waldo Kereső",
    "🧾 Számla & Nyugta AI",
    "🤖 AI Sakk Párbaj",
    "🎬 Intelligens Videó Elemző"
])

# --- FÜLEK TARTALMÁNAK MEGJELENÍTÉSE KÜLÖN FÁJLOKBÓL ---

with tab1:
    render_vision_tab(API_BASE_URL)

with tab2:
    render_waldo_tab(API_BASE_URL)

with tab3:
    render_invoice_tab(API_BASE_URL)

with tab4:
    render_chess_tab(API_BASE_URL)

with tab5:
    render_video_tab(API_BASE_URL)
