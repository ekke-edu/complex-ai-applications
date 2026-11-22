import streamlit as st
import requests
import base64
import mimetypes
import os

MAX_IMAGE_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


def _is_within_size_limit(size_bytes: int) -> bool:
    return size_bytes <= MAX_IMAGE_SIZE_BYTES


def _load_local_waldo_image(filename: str, caption: str) -> bytes | None:
    try:
        file_size = os.path.getsize(filename)
        if not _is_within_size_limit(file_size):
            st.error(
                f"❌ A '{filename}' mérete ({file_size / (1024 * 1024):.1f} MB) "
                f"meghaladja a képenkénti {MAX_IMAGE_SIZE_MB} MB-os limitet!"
            )
            return None

        with open(filename, "rb") as f:
            file_bytes = f.read()

        st.image(
            file_bytes,
            caption=f"{caption} ({file_size / (1024 * 1024):.1f} MB)",
            width=400
        )
        return file_bytes
    except FileNotFoundError:
        st.error(f"❌ A '{filename}' nem található a gyökérmappában!")
        return None


def render_waldo_tab(api_base_url: str):
    st.header("🎯 Speciális Waldo Kereső Modul – 3 Modell Versenye 🏁")
    st.caption(f"Támogatott formátum: JPG, JPEG, PNG — maximum {MAX_IMAGE_SIZE_MB} MB / kép.")

    with st.expander("💡 Tájékoztatás az MI modellek működéséről és korlátairól", expanded=False):
        st.markdown("""
        ### 💡 Miért tévedhet az MI? (A multimodális modellek korlátai)

        Az olyan nagyméretű, multimodális modellek, mint a Qwen, Gemini vagy Nemotron, általános feladatokra lettek optimalizálva, és **nincsenek feltétlenül feltanítva az apró, rejtett objektumok milliméter pontos (pixel-szintű) lokalizációjára.**

        Súgó: Waldo helyzete a nagy fesztiváli képen: `[ymin:255, xmin:812, ymax:355, xmax:888]`
        """)

    # 🎯 REFERENCIA KARAKTER MEGJELENÍTÉSE (ha létezik a gyökérben)
    if os.path.exists("waldo_character.jpg"):
        st.markdown("##### 👤 Keresendő karakter (Referencia az MI-nek):")
        st.image("waldo_character.jpg", width=120)
        st.divider()

    image_choice = st.radio(
        "Válassz képet a küldéshez:",
        [
            "🔍 Rejtvénykép (waldo_puzzle.jpg)",
            "👤 Keresendő karakter (waldo_character.jpg)",
            "✅ Megoldás / Bekarikázott kép (waldo_solution.jpg)",
            "📁 Saját kép feltöltése"
        ],
        key="waldo_image_choice"
    )

    waldo_file_bytes = None
    waldo_filename = "waldo_puzzle.jpg"

    if image_choice == "🔍 Rejtvénykép (waldo_puzzle.jpg)":
        waldo_filename = "waldo_puzzle.jpg"
        waldo_file_bytes = _load_local_waldo_image(
            waldo_filename,
            "Kiválasztva küldésre: Rejtvénykép"
        )

    elif image_choice == "👤 Keresendő karakter (waldo_character.jpg)":
        waldo_filename = "waldo_character.jpg"
        waldo_file_bytes = _load_local_waldo_image(
            waldo_filename,
            "Kiválasztva küldésre: Keresendő karakter"
        )

    elif image_choice == "✅ Megoldás / Bekarikázott kép (waldo_solution.jpg)":
        waldo_filename = "waldo_solution.jpg"
        waldo_file_bytes = _load_local_waldo_image(
            waldo_filename,
            "Kiválasztva küldésre: Megoldás kép"
        )

    else:
        uploaded_custom = st.file_uploader(
            f"Töltsd fel a saját képed (max. {MAX_IMAGE_SIZE_MB} MB):",
            type=["jpg", "jpeg", "png"],
            key="waldo_custom_uploader"
        )
        if uploaded_custom is not None:
            size_mb = uploaded_custom.size / (1024 * 1024)
            if not _is_within_size_limit(uploaded_custom.size):
                st.error(
                    f"❌ A feltöltött kép mérete ({size_mb:.1f} MB) meghaladja a "
                    f"képenkénti {MAX_IMAGE_SIZE_MB} MB-os limitet!"
                )
            else:
                waldo_file_bytes = uploaded_custom.getvalue()
                waldo_filename = uploaded_custom.name
                st.image(
                    uploaded_custom,
                    caption=f"Feltöltött saját kép ({size_mb:.1f} MB)",
                    width=400
                )

    if waldo_file_bytes is not None:
        default_hint = "Waldonak barna haja, fekete szemüvege van, piros-fehér sapkája piros bojttal. Illetve piros-fehér színű pulóvert hord."
        hint_input = st.text_area(
            "Súgás vagy kérdés az MI-nek ehhez a képhez:",
            value=default_hint,
            key="waldo_hint_input"
        )

        if st.button("🏁 3 Modell Versenyének Indítása", type="primary", key="waldo_submit_btn"):
            waldo_prompt = f"Kérlek, válaszolj magyarul. A felhasználó ezt a képet küldte: {waldo_filename}. Feladat / Súgás: {hint_input}."
            mime_type, _ = mimetypes.guess_type(waldo_filename)
            mime_type = mime_type or "image/jpeg"

            files = {"file": (waldo_filename, waldo_file_bytes, mime_type)}
            data = {"session_id": st.session_state.session_id, "prompt": waldo_prompt}

            with st.spinner(
                    "Mind a 3 modell (Qwen, Gemini, Nemotron) egyszerre keresi Waldot a referenciakép alapján..."):
                try:
                    res = requests.post(
                        f"{api_base_url}/waldo/waldo_race",
                        files=files,
                        data=data,
                        timeout=300
                    )

                    if res.status_code == 200:
                        res_data = res.json()
                        results = res_data.get("results", [])

                        if results:
                            st.success("A verseny lezárult! Íme az eredmények egymás alatt:")

                            for idx, item in enumerate(results):
                                st.divider()
                                with st.container(border=True):
                                    header_col, time_col, status_col = st.columns([3, 1, 1])

                                    with header_col:
                                        st.subheader(f"🤖 {item.get('model', 'Ismeretlen modell')}")
                                    with time_col:
                                        st.metric("Válaszidő", f"{item.get('time', 0.0)} mp")
                                    with status_col:
                                        if item.get("found"):
                                            st.success("🎯 Találat!")
                                        else:
                                            st.warning("❌ Nincs találat")

                                    st.info(item.get("response", "Nincs szöveges válasz."))

                                    annotated_b64 = item.get("annotated_image")
                                    if annotated_b64:
                                        st.image(
                                            base64.b64decode(annotated_b64),
                                            caption=f"🎯 {item.get('model')} jelölése",
                                            width="stretch"
                                        )
                        else:
                            st.warning("A szerver üres eredménylistát adott vissza.")
                    else:
                        st.error(f"Szerver hiba ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Kapcsolódási hiba: {e}")
