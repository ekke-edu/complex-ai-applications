import streamlit as st
import requests
import base64
import chess
import chess.svg

MAX_IMAGE_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


def _resolve_image_mime_type(uploaded_file) -> str:
    if uploaded_file.type:
        return uploaded_file.type
    if uploaded_file.name.lower().endswith(".png"):
        return "image/png"
    return "image/jpeg"


def _is_within_size_limit(uploaded_file) -> bool:
    return uploaded_file.size <= MAX_IMAGE_SIZE_BYTES


def render_chess_tab(api_base_url: str):
    st.header("🤖 AI Sakk Párbaj & Bajnokság")
    st.markdown("""
    Válassz üzemmódot: elemeztesd a táblát egy képről, vagy indíts el egy **önműködő AI vs AI sakk-meccset**, 
    ahol a Gemini és a Groq egymás ellen játszanak körről körre, amíg matt nem lesz!
    """)

    col_key1, col_key2 = st.columns(2)
    with col_key1:
        gemini_api_key = st.text_input(
            "Google Gemini API Key (Opcionális, ha a .env-ben be van állítva)",
            type="password",
            key="tab4_gemini_key"
        )
    with col_key2:
        groq_api_key = st.text_input(
            "Groq API Key (Opcionális, ha a .env-ben be van állítva)",
            type="password",
            key="tab4_groq_key"
        )

    st.divider()

    # Al-fülek a különböző funkciókhoz
    chess_sub_tab1, chess_sub_tab2, chess_sub_tab3 = st.tabs([
        "👁️ Kép Alapú Elemzés",
        "⚔️ AI vs AI Önműködő Meccs",
        "🎓 Élő Meccs a Stockfish 19 ellen & Groq Sakkmentor"
    ])

    # --- 1. AL-FÜL: Kép alapú párbaj (max 50 MB / kép) ---
    with chess_sub_tab1:
        st.subheader("Sakktábla Fotó Elemzése (Gemini vs Groq)")
        st.caption(f"Támogatott formátum: JPG, JPEG, PNG — maximum {MAX_IMAGE_SIZE_MB} MB / kép.")

        uploaded_chess_file = st.file_uploader(
            f"Válassz ki egy sakktábla fotót (max. {MAX_IMAGE_SIZE_MB} MB):",
            type=["jpg", "jpeg", "png"],
            key="chess_battle_uploader"
        )

        turn_label = st.radio(
            "Ki következik a képen?",
            options=["Világos (Fehér)", "Sötét (Fekete)"],
            horizontal=True,
            key="chess_turn_select",
        )
        turn_color = "white" if "Világos" in turn_label else "black"

        if uploaded_chess_file is not None:
            size_mb = uploaded_chess_file.size / (1024 * 1024)
            is_valid_size = _is_within_size_limit(uploaded_chess_file)

            if not is_valid_size:
                st.error(
                    f"❌ A feltöltött kép mérete ({size_mb:.1f} MB) meghaladja a "
                    f"képenkénti {MAX_IMAGE_SIZE_MB} MB-os limitet!"
                )
            else:
                st.image(
                    uploaded_chess_file,
                    caption=f"Feltöltött sakktábla ({size_mb:.1f} MB)",
                    width=400
                )

            if st.button(
                "🚀 Kép Elemzése & Párbaj",
                type="primary",
                key="run_chess_battle_btn",
                disabled=not is_valid_size
            ):
                with st.spinner("A két AI modell párhuzamosan elemzi a sakktáblát..."):
                    try:
                        files = {
                            "file": (
                                uploaded_chess_file.name,
                                uploaded_chess_file.getvalue(),
                                _resolve_image_mime_type(uploaded_chess_file)
                            )
                        }
                        data = {
                            "session_id": st.session_state.session_id,
                            "turn_color": turn_color,
                            "gemini_api_key": gemini_api_key,
                            "groq_api_key": groq_api_key
                        }

                        res = requests.post(f"{api_base_url}/chess_logic/battle", files=files, data=data, timeout=300)

                        if res.status_code == 200:
                            res_data = res.json()
                            gemini_res = res_data.get("gemini_result", {})
                            groq_res = res_data.get("groq_result", {})

                            st.success("A párbaj véget ért!")
                            col_gemini, col_groq = st.columns(2)

                            with col_gemini:
                                with st.container(border=True):
                                    st.subheader(f"🔵 {gemini_res.get('model_name', 'Gemini')}")
                                    st.metric("Válaszidő", f"{gemini_res.get('duration_seconds', 0.0):.2f} mp")
                                    if gemini_res.get("error"):
                                        st.error(f"Hiba: {gemini_res.get('error')}")
                                    else:
                                        if gemini_res.get("move"):
                                            st.markdown(f"**Javasolt lépés:** `{gemini_res.get('move')}`")
                                        st.markdown("##### 🧠 Gondolatmenet:")
                                        st.info(gemini_res.get("thought_process", "Nincs válasz."))

                            with col_groq:
                                with st.container(border=True):
                                    st.subheader(f"⚡ {groq_res.get('model_name', 'Groq VLM')}")
                                    st.metric("Válaszidő", f"{groq_res.get('duration_seconds', 0.0):.2f} mp")
                                    if groq_res.get("error"):
                                        st.error(f"Hiba: {groq_res.get('error')}")
                                    else:
                                        if groq_res.get("move"):
                                            st.markdown(f"**Javasolt lépés:** `{groq_res.get('move')}`")
                                        st.markdown("##### 🧠 Gondolatmenet:")
                                        st.info(groq_res.get("thought_process", "Nincs válasz."))
                        else:
                            st.error(f"Szerver hiba ({res.status_code}): {res.text}")
                    except Exception as e:
                        st.error(f"Kapcsolódási hiba: {e}")

    # --- 2. AL-FÜL: Önműködő meccs szimuláció ---
    with chess_sub_tab2:
        st.subheader("Önműködő AI vs AI Bajnokság (Gemini vs Groq)")
        st.markdown("Itt nincs szükség képre: a modellek a kezdőállástól indulva, körről körre játszanak egymás ellen.")

        opponent_choice = st.selectbox(
            "Válassz Sötét ellenfelet a Gemini (Világos) mellé:",
            ["Groq (Qwen 3.8)"],
            key="chess_opponent_select"
        )
        opponent_key = "nemotron" if "Nemotron" in opponent_choice else "groq"

        max_turns = st.slider("Maximális lépésszám a mérkőzésen:", min_value=5, max_value=40, value=15, key="match_max_turns")

        if "match_history" not in st.session_state:
            st.session_state.match_history = []
        if "current_step_index" not in st.session_state:
            st.session_state.current_step_index = 0

        if st.button("🏁 Teljes Sakk Meccs Indítása", type="primary", key="run_match_btn"):
            with st.spinner(f"A nagymester modellek (Gemini vs {opponent_choice}) összecsapnak... Ez eltarthat egy kis ideig."):
                try:
                    data = {
                        "session_id": st.session_state.session_id,
                        "gemini_api_key": gemini_api_key,
                        "groq_api_key": groq_api_key,
                        "opponent": opponent_key,
                        "max_turns": max_turns
                    }
                    res = requests.post(f"{api_base_url}/chess_logic/simulate_match", data=data, timeout=300)

                    if res.status_code == 200:
                        match_data = res.json()
                        history = match_data.get("history", [])

                        if history:
                            initial_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                            board_init = chess.Board(initial_fen)
                            svg_init = chess.svg.board(board=board_init, size=400)
                            b64_init = base64.b64encode(svg_init.encode('utf-8')).decode('utf-8')
                            initial_img = f"data:image/svg+xml;base64,{b64_init}"

                            full_history = [{
                                "turn": 0,
                                "player": "Kezdőállás",
                                "move": "Kezdés",
                                "thought": "A mérkőzés kezdeti alaphelyzete.",
                                "duration": 0.0,
                                "fen": initial_fen,
                                "board_image": initial_img
                            }] + history

                            st.session_state.match_history = full_history
                            st.session_state.current_step_index = 0
                            st.success(f"A mérkőzés lezárult! Összesen {len(history)} lépés történt.")
                        else:
                            st.warning("A szimuláció nem adott vissza lépéseket.")
                    else:
                        st.error(f"Szerver hiba ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Kapcsolódási hiba: {e}")

        # Vizuális visszajátszó és lapozó felület nyilakkal és grafikus táblával
        if st.session_state.match_history:
            st.divider()
            st.markdown("### ♟️ Mérkőzés Visszajátszás & Grafikus Tábla Állapot")

            history = st.session_state.match_history
            max_idx = len(history) - 1

            col_btn1, col_info, col_btn2 = st.columns([1, 2, 1])

            with col_btn1:
                if st.button("⬅️ Előző lépés", width="stretch"):
                    if st.session_state.current_step_index > 0:
                        st.session_state.current_step_index -= 1

            with col_info:
                current_idx = st.session_state.current_step_index
                st.markdown(f"<h4 style='text-align: center;'>Lépés: {current_idx} / {max_idx}</h4>", unsafe_allow_html=True)

            with col_btn2:
                if st.button("Következő lépés ➡️", width="stretch"):
                    if st.session_state.current_step_index < max_idx:
                        st.session_state.current_step_index += 1

            current_step = history[st.session_state.current_step_index]

            with st.container(border=True):
                col_board, col_details = st.columns([1, 1])

                with col_board:
                    st.markdown(f"#### 🎯 {current_step.get('player')}")
                    st.write(f"Meglépve: **{current_step.get('move')}**")
                    if current_step.get("board_image"):
                        svg_data_uri = current_step.get("board_image")
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                                <img src="{svg_data_uri}" width="350" style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" />
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.caption(f"Tábla állás a(z) {current_step.get('turn')}. kör után")

                with col_details:
                    st.metric("Válaszidő", f"{current_step.get('duration'):.2f}s")
                    st.markdown("##### 🔍 Részletes AI Gondolatmenet:")
                    st.info(current_step.get('thought', 'Nincs gondolatmenet.'))
                    st.code(f"FEN: {current_step.get('fen')}", language="text")

    # --- 3. AL-FÜL: Élő Sakk Párbaj Stockfish 19 ellen + Groq Tanácsadó ---
    with chess_sub_tab3:
        st.subheader("🎓 Élő Meccs a Stockfish 19 ellen & Groq Sakkmentor")
        st.markdown(
            "Játssz közvetlenül a világ legerősebb nyílt forráskódú motorja ellen! A Groq AI körről körre elmagyarázza a lépéseket."
        )

        # Session állapotok az élő meccshez
        if "coach_board" not in st.session_state:
            st.session_state.coach_board = chess.Board()
        if "coach_history" not in st.session_state:
            st.session_state.coach_history = [st.session_state.coach_board.fen()]
        if "coach_explanations" not in st.session_state:
            st.session_state.coach_explanations = ["Kezdőállás. Húzz egyet Világosként!"]
        if "coach_moves" not in st.session_state:
            st.session_state.coach_moves = []

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            player_color = st.selectbox("Válassz színt:", ["Világos (Fehér)", "Sötét (Fekete)"], key="coach_color")
        with col_cfg2:
            if st.button("🔄 Új Játék Indítása", key="reset_coach_game"):
                st.session_state.coach_board = chess.Board()
                st.session_state.coach_history = [st.session_state.coach_board.fen()]
                st.session_state.coach_explanations = ["Új játék indult."]
                st.session_state.coach_moves = []
                st.rerun()

        current_board = st.session_state.coach_board

        is_player_turn = (
                (player_color.startswith("Világos") and current_board.turn == chess.WHITE)
                or (player_color.startswith("Sötét") and current_board.turn == chess.BLACK)
        )

        svg_data = chess.svg.board(board=current_board, size=400)
        b64_svg = base64.b64encode(svg_data.encode("utf-8")).decode("utf-8")

        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                <img src="data:image/svg+xml;base64,{b64_svg}" width="400" style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" />
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_player_turn and not current_board.is_game_over():
            st.markdown("##### ✍️ Add meg a lépésed (SAN formátumban, pl. `e4`, `Nf3`, `Qxd5`):")
            col_input, col_send = st.columns([3, 1])
            with col_input:
                player_move_input = st.text_input(
                    "Lépés:", key="player_move_text_input", label_visibility="collapsed"
                )
            with col_send:
                send_clicked = st.button("Lépés Meccselése 🚀", type="primary", width="stretch")

            if send_clicked and player_move_input:
                with st.spinner("Stockfish 19 számol és a Groq AI elemez..."):
                    try:
                        res = requests.post(
                            f"{api_base_url}/chess_logic/play_vs_stockfish",
                            data={
                                "session_id": st.session_state.session_id,
                                "fen": current_board.fen(),
                                "player_move": player_move_input,
                                "groq_api_key": groq_api_key,
                            },
                            timeout=30,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            if data.get("error"):
                                st.warning(data.get("error"))
                            else:
                                raw_move = player_move_input.strip()
                                is_uci = (
                                        len(raw_move) == 4
                                        and raw_move[0] in "abcdefgh"
                                        and raw_move[2] in "abcdefgh"
                                )
                                move_obj = (
                                    chess.Move.from_uci(raw_move)
                                    if is_uci
                                    else current_board.parse_san(raw_move)
                                )
                                player_san = current_board.san(move_obj)

                                tmp_board = chess.Board(current_board.fen())
                                tmp_board.push(move_obj)

                                engine_uci = data.get("engine_move_uci", "")
                                engine_san = ""
                                if engine_uci:
                                    engine_san = tmp_board.san(chess.Move.from_uci(engine_uci))

                                player_label = "Világos" if player_color.startswith("Világos") else "Sötét"
                                engine_label = "Sötét" if player_color.startswith("Világos") else "Világos"

                                st.session_state.coach_moves.append(f"{player_label}: {player_san}")
                                if engine_san:
                                    st.session_state.coach_moves.append(f"Gép ({engine_label}): {engine_san}")

                                st.session_state.coach_board = chess.Board(data.get("new_fen"))
                                st.session_state.coach_history.append(data.get("new_fen"))
                                st.session_state.coach_explanations.append(data.get("ai_explanation"))
                                st.rerun()
                        else:
                            st.error(f"Szerver hiba: {res.text}")
                    except Exception as e:
                        st.error(f"Kapcsolódási hiba: {e}")

        elif not current_board.is_game_over():
            with st.spinner("🤖 A Stockfish gép lép és a Groq AI elemzi..."):
                try:
                    res = requests.post(
                        f"{api_base_url}/chess_logic/engine_move_stockfish",
                        data={
                            "session_id": st.session_state.session_id,
                            "fen": current_board.fen(),
                            "groq_api_key": groq_api_key,
                        },
                        timeout=30,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("error"):
                            st.warning(data.get("error"))
                        else:
                            engine_uci = data.get("engine_move_uci", "")
                            if engine_uci:
                                engine_san = current_board.san(chess.Move.from_uci(engine_uci))
                                engine_label = "Világos" if current_board.turn == chess.WHITE else "Sötét"
                                st.session_state.coach_moves.append(f"Gép ({engine_label}): {engine_san}")

                            st.session_state.coach_board = chess.Board(data.get("new_fen"))
                            st.session_state.coach_history.append(data.get("new_fen"))
                            st.session_state.coach_explanations.append(data.get("ai_explanation"))
                            st.rerun()
                    else:
                        st.error(f"Szerver hiba: {res.text}")
                except Exception as e:
                    st.error(f"Kapcsolódási hiba: {e}")
        else:
            st.success("🏁 A mérkőzés véget ért!")

        if st.session_state.coach_explanations:
            st.divider()
            st.markdown("### 🧠 Groq AI Sakkmentor Naplója")
            st.info(st.session_state.coach_explanations[-1])

        if st.session_state.coach_moves:
            st.divider()
            st.markdown("### 📜 Megtett lépések eddig")
            st.markdown(" • ".join(st.session_state.coach_moves))
