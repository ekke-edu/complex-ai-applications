import base64
import requests
import streamlit as st

MAX_IMAGE_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_FILES_TAB1 = 3


def _resolve_image_mime_type(uploaded_file) -> str:
    if uploaded_file.type:
        return uploaded_file.type
    if uploaded_file.name.lower().endswith(".png"):
        return "image/png"
    return "image/jpeg"


def _is_within_size_limit(uploaded_file) -> bool:
    return uploaded_file.size <= MAX_IMAGE_SIZE_BYTES


def _filter_oversized_files(uploaded_files) -> tuple[list, list]:
    valid_files = []
    oversized_files = []
    for f in uploaded_files:
        if _is_within_size_limit(f):
            valid_files.append(f)
        else:
            oversized_files.append(f)
    return valid_files, oversized_files


def render_vision_tab(api_base_url: str):
    st.header("👁️ Gépi Látás & Objektumdetektálás")

    vision_sub_tab1, vision_sub_tab2, vision_sub_tab3 = st.tabs([
        "👁️ Általános Képelemzés",
        "✂️ Objektumdetektálás & Kivágás",
        "📏 Mélységbecslés (Depth Anything V2)"
    ])

    # --- 1. AL-FÜL: Általános Képelemzés (max 3 kép, képenként max 50 MB) ---
    with vision_sub_tab1:
        st.subheader("Qwen Vision Elemzés")
        st.caption(f"Maximum {MAX_FILES_TAB1} kép tölthető fel egyszerre, képenként legfeljebb {MAX_IMAGE_SIZE_MB} MB méretben.")

        uploaded_files = st.file_uploader(
            "Válassz ki legfeljebb 3 képet...",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="vision_multi_uploader"
        )

        if uploaded_files:
            too_many_files = len(uploaded_files) > MAX_FILES_TAB1
            valid_size_files, oversized_files = _filter_oversized_files(uploaded_files)

            if too_many_files:
                st.error(
                    f"Egyszerre legfeljebb {MAX_FILES_TAB1} képet lehet elemezni "
                    f"(jelenleg {len(uploaded_files)} kép van kiválasztva). "
                    f"Kérlek, távolíts el {len(uploaded_files) - MAX_FILES_TAB1} fájlt."
                )

            if oversized_files:
                names_with_sizes = ", ".join(
                    f"{f.name} ({f.size / (1024 * 1024):.1f} MB)" for f in oversized_files
                )
                st.error(
                    f"A következő fájl(ok) meghaladják a képenkénti {MAX_IMAGE_SIZE_MB} MB-os limitet: "
                    f"{names_with_sizes}"
                )

            # Csak a méretkorláton belüli képeket jelenítjük meg előnézetben
            for uploaded_file in valid_size_files:
                size_mb = uploaded_file.size / (1024 * 1024)
                st.image(
                    uploaded_file,
                    caption=f"Feltöltve: {uploaded_file.name} ({size_mb:.1f} MB)",
                    width=300
                )

            vision_prompt = st.text_input(
                "Mit szeretnél tudni a kép(ek)ről?",
                value="Írd le egy-egy mondatban mi van a képeken!",
                key="multi_vision_prompt",
            )

            can_analyze_multi = (
                not too_many_files
                and len(oversized_files) == 0
                and len(valid_size_files) > 0
            )

            if st.button(
                "Képek Elemzése Groq Vision-nel 🚀",
                type="primary",
                key="vision_analyze_btn",
                disabled=not can_analyze_multi
            ):
                with st.spinner("A multimodális modell elemzi a feltöltött képeket..."):
                    try:
                        files = [
                            ("files", (file.name, file.getvalue(), _resolve_image_mime_type(file)))
                            for file in valid_size_files
                        ]
                        data = {
                            "session_id": st.session_state.session_id,
                            "prompt": vision_prompt,
                        }

                        res = requests.post(f"{api_base_url}/vision/chat_with_image", files=files, data=data)

                        if res.status_code == 200:
                            res_data = res.json()
                            if res_data:
                                st.success("Sikeres elemzés!")
                                st.info(res_data.get("response", "Nincs válasz."))
                            else:
                                st.success("Sikeres elemzés, de üres válasz érkezett.")
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(f"Kapcsolódási hiba: {e}")

    # --- 2. AL-FÜL: Objektumdetektálás & Kivágás (max 50 MB / kép) ---
    with vision_sub_tab2:
        st.subheader("Interaktív Objektumdetektálás & Automatikus Kivágás")
        st.caption(f"Támogatott formátum: JPG, JPEG, PNG — maximum {MAX_IMAGE_SIZE_MB} MB / kép.")

        uploaded_crop_file = st.file_uploader(
            "Válassz ki egy JPG vagy PNG képet elemzésre:",
            type=["jpg", "jpeg", "png"],
            key="crop_image_uploader"
        )
        detection_query = st.text_input(
            "Mit keressek a képen?",
            value="Pl. a kép közepét emeld ki!",
            key="detection_query_input"
        )

        if uploaded_crop_file is not None:
            crop_size_mb = uploaded_crop_file.size / (1024 * 1024)
            crop_valid_size = _is_within_size_limit(uploaded_crop_file)

            if not crop_valid_size:
                st.error(
                    f"A fájl mérete ({crop_size_mb:.1f} MB) meghaladja a megengedett "
                    f"{MAX_IMAGE_SIZE_MB} MB-os limitet."
                )
            else:
                st.image(
                    uploaded_crop_file,
                    caption=f"Feltöltött eredeti kép ({crop_size_mb:.1f} MB)",
                    width=400
                )

            if st.button(
                "Keresés és Kivágás indítása 🚀",
                type="primary",
                key="run_detection_btn",
                disabled=not crop_valid_size
            ):
                if not detection_query.strip():
                    st.warning("Add meg, mit keresel!")
                else:
                    try:
                        files = {
                            "file": (
                                uploaded_crop_file.name,
                                uploaded_crop_file.getvalue(),
                                _resolve_image_mime_type(uploaded_crop_file),
                            )
                        }
                        data = {
                            "session_id": st.session_state.session_id,
                            "prompt": detection_query
                        }
                        res = requests.post(f"{api_base_url}/vision/detect_and_crop", files=files, data=data)
                        if res.status_code == 200:
                            res_data = res.json()
                            if res_data:
                                st.info(res_data.get("response", ""))
                                if res_data.get("found", False):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if res_data.get("annotated_image"):
                                            st.image(
                                                base64.b64decode(res_data.get("annotated_image")),
                                                caption="Berajzolva"
                                            )
                                    with col2:
                                        if res_data.get("cropped_image"):
                                            st.image(
                                                base64.b64decode(res_data.get("cropped_image")),
                                                caption="Kivágva"
                                            )
                            else:
                                st.warning("Üres válasz érkezett a detektáláshoz.")
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(f"Hiba: {e}")

    # --- 3. AL-FÜL: Mélységbecslés (max 50 MB / kép) ---
    with vision_sub_tab3:
        st.subheader("3D Mélységtérkép Generálás (Depth Anything V2)")
        st.markdown("Tölts fel egy 2D-s képet, és az MI megbecsüli a kamerától mért távolságokat.")
        st.caption(f"Támogatott formátum: JPG, JPEG, PNG — maximum {MAX_IMAGE_SIZE_MB} MB / kép.")

        uploaded_depth_file = st.file_uploader(
            "Válassz ki egy képet mélységbecsléshez:",
            type=["jpg", "jpeg", "png"],
            key="depth_image_uploader"
        )

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            colormap_choice = st.selectbox(
                "Színskála (Hőtérkép):",
                ["Inferno (Lila-Sárga)", "Viridis (Kék-Zöld-Sárga)", "Szürkeárnyalatos (Grayscale)"],
                key="depth_colormap"
            )
        with col_opt2:
            model_size = st.selectbox(
                "Modell mérete:",
                ["Small (Gyors - CPU/GPU)", "Base (Kiegyensúlyozott)", "Large (Legpontosabb - GPU ajánlott)"],
                key="depth_model_size"
            )

        if uploaded_depth_file is not None:
            depth_size_mb = uploaded_depth_file.size / (1024 * 1024)
            depth_valid_size = _is_within_size_limit(uploaded_depth_file)

            if not depth_valid_size:
                st.error(
                    f"A fájl mérete ({depth_size_mb:.1f} MB) meghaladja a megengedett "
                    f"{MAX_IMAGE_SIZE_MB} MB-os limitet."
                )

            if st.button(
                "Mélységtérkép Generálása 🚀",
                type="primary",
                key="run_depth_btn",
                disabled=not depth_valid_size
            ):
                with st.spinner("A Depth Anything V2 számolja a térbeli mélységet..."):
                    try:
                        files = {
                            "file": (
                                uploaded_depth_file.name,
                                uploaded_depth_file.getvalue(),
                                _resolve_image_mime_type(uploaded_depth_file),
                            )
                        }
                        data = {
                            "session_id": st.session_state.session_id,
                            "colormap": colormap_choice.split(" ")[0].lower(),
                            "model_size": model_size.split(" ")[0].lower()
                        }

                        res = requests.post(f"{api_base_url}/vision/estimate_depth", files=files, data=data)

                        if res.status_code == 200:
                            res_data = res.json()
                            depth_b64 = res_data.get("depth_image")

                            if depth_b64:
                                st.success(f"Kész! Feldolgozási idő: {res_data.get('duration', 0.0):.2f} mp")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.image(uploaded_depth_file, caption="Eredeti 2D kép", width="stretch")
                                with col2:
                                    st.image(base64.b64decode(depth_b64), caption="Generált Mélységtérkép", width="stretch")
                            else:
                                st.warning("Nem érkezett vissza kép a szervertől.")
                        else:
                            st.error(f"Szerver hiba ({res.status_code}): {res.text}")
                    except Exception as e:
                        st.error(f"Kapcsolódási hiba: {e}")
