import streamlit as st
import requests

MAX_VIDEO_SIZE_MB = 50
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024


def _is_within_video_size_limit(uploaded_file) -> bool:
    return uploaded_file.size <= MAX_VIDEO_SIZE_BYTES


def _resolve_video_mime_type(uploaded_file) -> str:
    if uploaded_file.type:
        return uploaded_file.type
    if uploaded_file.name.lower().endswith(".mkv"):
        return "video/x-matroska"
    return "video/mp4"


def render_video_tab(api_base_url: str):
    st.header("🎬 Intelligens Videó Elemző")
    st.markdown(
        f"Tölts fel egy MP4 vagy MKV videót (max. **{MAX_VIDEO_SIZE_MB} MB**): "
        "a rendszer külön al-füleken mutatja be a hangátiratot és a vizuális elemzést."
    )

    uploaded_video = st.file_uploader(
        f"Válassz ki egy MP4 vagy MKV videót (max. {MAX_VIDEO_SIZE_MB} MB):",
        type=["mp4", "mkv"],
        key="video_uploader",
    )
    video_prompt = st.text_input(
        "Mit szeretnél megtudni a videóról?",
        value="Foglald össze részletesen a videó tartalmát!",
        key="video_prompt_input",
    )

    # Legördülő lista a hang nyelvéhez
    selected_language_label = st.selectbox(
        "Videó hangjának nyelve:",
        options=["Magyar", "Angol"],
        index=0,
        key="video_language_select",
    )
    language_code = "hu" if selected_language_label == "Magyar" else "en"

    if uploaded_video is not None:
        size_mb = uploaded_video.size / (1024 * 1024)
        is_valid_size = _is_within_video_size_limit(uploaded_video)

        if not is_valid_size:
            st.error(
                f"❌ A feltöltött videó mérete ({size_mb:.1f} MB) meghaladja a "
                f"megengedett {MAX_VIDEO_SIZE_MB} MB-os limitet!"
            )
        else:
            if uploaded_video.name.lower().endswith(".mkv"):
                st.caption("Megjegyzés: az MKV előnézet lejátszása böngészőfüggő, de a videóelemzés ettől függetlenül lefut.")
            st.caption(f"Feltöltött fájl: {uploaded_video.name} ({size_mb:.1f} MB)")
            st.video(uploaded_video)

        if st.button(
            "Videó Elemzése (Hang & Kép) 🚀",
            type="primary",
            key="run_video_analysis_btn",
            disabled=not is_valid_size,
        ):
            with st.spinner("Feldolgozás alatt: Hang átírása Whisperrel + Képkockák elemzése Qwennel..."):
                try:
                    mime_type = _resolve_video_mime_type(uploaded_video)

                    files = {
                        "file": (uploaded_video.name, uploaded_video.getvalue(), mime_type)
                    }
                    data = {
                        "session_id": st.session_state.session_id,
                        "prompt": video_prompt,
                        "language": language_code,
                    }

                    res = requests.post(
                        f"{api_base_url}/video/analyze_video",
                        files=files,
                        data=data,
                        timeout=300,
                    )

                    if res.status_code == 200:
                        res_data = res.json()
                        st.session_state.video_transcript = res_data.get("transcript", "Nincs hangátirat.")
                        st.session_state.video_vision = res_data.get("vision_analysis", "Nincs vizuális elemzés.")
                        st.success("A videó elemzése sikeresen elkészült!")
                    else:
                        st.error(f"Szerver hiba ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Kapcsolódási hiba: {e}")

        if "video_transcript" in st.session_state and st.session_state.video_transcript:
            st.divider()

            video_sub_tab1, video_sub_tab2 = st.tabs([
                "🎙️ Elhangzott szöveg leírása",
                "👁️ Videóelemzés (Vizuális)",
            ])

            with video_sub_tab1:
                st.subheader("A videóban elhangzott beszéd átirata (Whisper)")
                st.info(st.session_state.video_transcript)

            with video_sub_tab2:
                st.subheader("A videó vizuális és eseményalapú elemzése (Qwen Vision)")
                st.info(st.session_state.video_vision)
