"""
https://chessfox.com/chess-puzzles-for-beginners/
"""
import time
import io
import base64
import os
import chess
import chess.engine
import chess.svg
from PIL import Image
from google import genai
from groq import Groq
from dotenv import load_dotenv
from .schemas import ModelResponse
from pathlib import Path
import re

load_dotenv()


def _format_turn_label(turn_color: str) -> str:
    return (
        "Fekete (Sötét)"
        if (turn_color or "").strip().lower() in ("black", "fekete", "sötét")
        else "Fehér (Világos)"
    )


def _extract_move(text: str) -> str:
    if not text:
        return ""

    match = re.search(
        r"LÉPÉS:\s*\[?([A-Za-z0-9+#=\-O0]+)\]?",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip().strip("[]().,")

    san_matches = re.findall(
        r"\b(?:O-O(?:-O)?|[KQRBN][a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|[a-h]x?[a-h][1-8](?:=[QRBN])?[+#]?)\b",
        text,
    )
    if san_matches:
        return san_matches[-1].strip()

    return "Nem sikerült egyértelműen kinyerni"


def _build_chess_vision_prompt(turn_color: str) -> str:
    side = _format_turn_label(turn_color)
    return (
        f"Nézd meg ezt a sakktábla képet! A soron következő játékos: {side}.\n"
        "A válaszod elején külön sorban, pontosan így add meg a lépést: LÉPÉS: [lépés]\n\n"
        "Gondold végig lépésről lépésre (Chain-of-Thought), mi a jelenlegi állás "
        f"(bábuk helyzete, taktikai lehetőségek/fenyegetések), majd javasolj egy 100%-ban legális lépést "
        f"{side} számára SAN formátumban (pl. Nf3, e4, Qxd8, O-O)."
    )


class ChessAIAnalyzer:

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        if image.mode in ("P", "RGBA", "LA"):
            image = image.convert("RGBA").convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")

        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"

    @classmethod
    def analyze_with_gemini(
        cls,
        image: Image.Image,
        api_key: str = "",
        turn_color: str = "white",
    ) -> ModelResponse:
        start_time = time.time()
        try:
            effective_key = api_key or os.getenv("GEMINI_API_KEY")
            if not effective_key:
                raise ValueError("Hiányzik a Gemini API kulcs (sem a felületen, sem a .env-ben nincs megadva).")

            client = genai.Client(api_key=effective_key)
            prompt = _build_chess_vision_prompt(turn_color)

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[image, prompt],
            )

            duration = time.time() - start_time
            text_response = response.text or ""
            extracted_move = _extract_move(text_response)

            return ModelResponse(
                model_name="Gemini 3.5 Flash",
                thought_process=text_response,
                move=extracted_move,
                duration_seconds=duration,
                error=None,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ModelResponse(
                model_name="Gemini 3.5 Flash",
                thought_process="",
                move="",
                duration_seconds=duration,
                error=str(e),
            )

    @classmethod
    def analyze_with_groq(
        cls,
        image: Image.Image,
        api_key: str = "",
        turn_color: str = "white",
    ) -> ModelResponse:
        start_time = time.time()
        try:
            effective_key = api_key or os.getenv("GROQ_API_KEY")
            if not effective_key:
                raise ValueError("Hiányzik a Groq API kulcs (sem a felületen, sem a .env-ben nincs megadva).")

            image_url = cls._image_to_base64(image)
            client = Groq(api_key=effective_key)
            prompt = _build_chess_vision_prompt(turn_color)
            system_instruction = (
                "Szigorú formátumszabály: a válaszod legelső sorában kizárólag ezt írd: "
                "LÉPÉS: <lépés> (például: LÉPÉS: Qg6). Ne írj semmi mást az első sorba!"
            )

            completion = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    },
                ],
                max_tokens=1000,
                temperature=0,
            )

            duration = time.time() - start_time
            text_response = completion.choices[0].message.content or ""
            extracted_move = _extract_move(text_response)

            return ModelResponse(
                model_name="Groq VLM",
                thought_process=text_response,
                move=extracted_move,
                duration_seconds=duration,
                error=None,
            )
        except Exception as e:
            duration = time.time() - start_time
            return ModelResponse(
                model_name="Groq VLM",
                thought_process="",
                move="",
                duration_seconds=duration,
                error=str(e),
            )


class ChessGameSimulator:

    @staticmethod
    def fen_to_svg_base64(fen: str) -> str:
        board = chess.Board(fen)
        svg_data = chess.svg.board(board=board, size=400)
        base64_svg = base64.b64encode(svg_data.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{base64_svg}"

    @staticmethod
    def play_full_game(
        gemini_api_key: str = "",
        secondary_api_key: str = "",
        opponent: str = "groq",
        max_turns: int = 15,
    ) -> list:
        board = chess.Board()
        game_history = []

        effective_gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        client_gemini = genai.Client(api_key=effective_gemini_key)

        effective_sec_key = secondary_api_key or os.getenv("GROQ_API_KEY")
        client_secondary = Groq(api_key=effective_sec_key)
        model_name = "qwen/qwen3.8-27b"
        player_name = "Groq (Sötét)"

        turn_count = 0

        while not board.is_game_over() and turn_count < max_turns:
            turn_count += 1
            is_white_turn = board.turn == chess.WHITE
            current_player = "Gemini (Világos)" if is_white_turn else player_name

            fen = board.fen()
            base_prompt = (
                f"Játssz sakkot! A tábla jelenlegi FEN állása: {fen}\n"
                f"Eddigi lépések száma: {turn_count - 1}\n"
                "Feladatod: Adj meg EGYETLEN legális sakk lépést SAN (pl. Nf3, e4, Qxd8) formátumban.\n"
                "FONTOS: A válaszod ELEJÉRE add meg a lépést pontosan így: LÉPÉS: [lépés]\n"
                "Utána leírhatod a gondolatmenetet is, ha szeretnéd."
            )

            current_prompt = base_prompt
            start_time = time.time()
            move_str = ""
            thought = ""
            success = False
            max_self_corrections = 2
            final_error = ""

            for attempt in range(max_self_corrections + 1):
                try:
                    api_success = False
                    for api_try in range(3):
                        try:
                            if is_white_turn:
                                response = client_gemini.models.generate_content(
                                    model="gemini-3.5-flash-lite",
                                    contents=[current_prompt],
                                )
                                thought = response.text or ""
                            else:
                                completion = client_secondary.chat.completions.create(
                                    model=model_name,
                                    messages=[{"role": "user", "content": current_prompt}],
                                    max_tokens=500,
                                )
                                thought = completion.choices[0].message.content or ""

                            api_success = True
                            break
                        except Exception as api_err:
                            if "503" in str(api_err) or "rate_limit" in str(api_err).lower():
                                time.sleep(2 * (api_try + 1))
                            else:
                                raise api_err

                    if not api_success:
                        raise Exception("API elérhetőségi hiba 3 próbálkozás után.")

                    if "LÉPÉS:" in thought:
                        parts = thought.split("LÉPÉS:")
                        move_str = parts[1].strip().split()[0]
                    else:
                        move_str = thought.strip().split()[0]

                    move_str = move_str.strip("[]()-,.")

                    move = board.parse_san(move_str)
                    if move in board.legal_moves:
                        success = True
                        break
                    else:
                        raise ValueError(f"Az '{move_str}' lépés nem legális a jelenlegi állásban.")

                except Exception as e:
                    final_error = str(e)
                    if attempt < max_self_corrections:
                        current_prompt = (
                            f"{base_prompt}\n\n"
                            f"🛑 FIGYELEM: Az előző válaszodban megadott '{move_str}' lépés érvénytelen vagy illegális volt. "
                            f"Hibaüzenet: {final_error}\n"
                            "Kérlek, figyelmesen ellenőrizd a FEN állást, és ezúttal KIZÁRÓLAG EGY VALÓBAN LEGÁLIS LÉPÉST adj meg LÉPÉS: [lépés] formátumban!"
                        )
                    else:
                        success = False

            duration = time.time() - start_time

            if success:
                board.push(move)
                game_history.append({
                    "turn": turn_count,
                    "player": current_player,
                    "move": move_str,
                    "thought": thought,
                    "duration": round(duration, 2),
                    "fen": board.fen(),
                    "board_image": ChessGameSimulator.fen_to_svg_base64(board.fen()),
                    "status": "Sikeres lépés" if attempt == 0 else "Sikeres lépés (önkorrekció után)",
                })
            else:
                game_history.append({
                    "turn": turn_count,
                    "player": current_player,
                    "move": "Érvénytelen / Hiba",
                    "thought": (
                        f"Az AI nem tudott legális lépést hozni {max_self_corrections + 1} próbálkozás után. "
                        f"Utolsó hiba: {final_error} \n\nEredeti válasz: {thought}"
                    ),
                    "duration": round(duration, 2),
                    "fen": board.fen(),
                    "board_image": ChessGameSimulator.fen_to_svg_base64(board.fen()),
                    "status": "Hiba",
                })
                break

        return game_history


class ChessCoachSimulator:
    STOCKFISH_PATH = str(Path(__file__).resolve().parents[2] / "engines" / "stockfish.exe")

    @staticmethod
    def play_turn(fen: str, player_move: str, groq_api_key: str = "") -> dict:
        try:
            board = chess.Board(fen)

            try:
                if len(player_move) == 4 and player_move[0] in "abcdefgh" and player_move[2] in "abcdefgh":
                    move = chess.Move.from_uci(player_move)
                else:
                    move = board.parse_san(player_move)

                if move not in board.legal_moves:
                    return {"success": False, "error": f"A(z) '{player_move}' lépés nem legális ebben a pozícióban!"}

                board.push(move)
            except Exception as e:
                return {"success": False, "error": f"Érvénytelen lépés formátum vagy hiba: {str(e)}"}

            if board.is_game_over():
                return {
                    "success": True,
                    "new_fen": board.fen(),
                    "engine_move_uci": "",
                    "from_square": 0,
                    "to_square": 0,
                    "evaluation": 0,
                    "ai_explanation": "A játszma véget ért!",
                    "game_over": True,
                }

            if not os.path.exists(ChessCoachSimulator.STOCKFISH_PATH):
                raise FileNotFoundError(f"A Stockfish motor nem található itt: {ChessCoachSimulator.STOCKFISH_PATH}")

            with chess.engine.SimpleEngine.popen_uci(ChessCoachSimulator.STOCKFISH_PATH) as engine:
                result = engine.play(board, chess.engine.Limit(time=1.0))
                engine_move = result.move

                info = engine.analyse(board, chess.engine.Limit(time=0.5))
                score = info["score"].relative.score(mate_score=10000)

            from_sq = engine_move.from_square
            to_sq = engine_move.to_square

            board.push(engine_move)
            updated_fen = board.fen()

            effective_groq_key = groq_api_key or os.getenv("GROQ_API_KEY")
            ai_explanation = "A Groq API kulcs hiányzik a szakértői magyarázathoz."

            if effective_groq_key:
                try:
                    client = Groq(api_key=effective_groq_key)
                    prompt = (
                        f"Te egy mester sakkoktató vagy. Az új FEN állás a táblán: {updated_fen}. "
                        f"A Stockfish gép ezt lépte: {engine_move.uci()}. "
                        f"Az állás értékelése centipawnban (pozitív = világos áll jobban): {score}. "
                        "Kérlek, magyarázd el magyarul, hogy miért ez volt a gép lépése, "
                        "és mit kell most tennie a játékosnak taktikai szempontból (max 4-5 mondatban)."
                    )
                    completion = client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=400,
                    )
                    ai_explanation = completion.choices[0].message.content
                except Exception as ai_err:
                    ai_explanation = f"Hiba az AI elemzés közben: {str(ai_err)}"

            return {
                "success": True,
                "new_fen": updated_fen,
                "engine_move_uci": engine_move.uci(),
                "from_square": from_sq,
                "to_square": to_sq,
                "evaluation": score,
                "ai_explanation": ai_explanation,
                "game_over": board.is_game_over(),
                "error": None,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def engine_move_only(fen: str, groq_api_key: str = "") -> dict:
        try:
            board = chess.Board(fen)
            if board.is_game_over():
                return {
                    "success": True,
                    "new_fen": board.fen(),
                    "engine_move_uci": "",
                    "from_square": 0,
                    "to_square": 0,
                    "evaluation": 0,
                    "ai_explanation": "A játszma véget ért!",
                    "game_over": True,
                }

            if not os.path.exists(ChessCoachSimulator.STOCKFISH_PATH):
                raise FileNotFoundError(f"A Stockfish motor nem található itt: {ChessCoachSimulator.STOCKFISH_PATH}")

            with chess.engine.SimpleEngine.popen_uci(ChessCoachSimulator.STOCKFISH_PATH) as engine:
                result = engine.play(board, chess.engine.Limit(time=1.0))
                engine_move = result.move
                info = engine.analyse(board, chess.engine.Limit(time=0.5))
                score = info["score"].relative.score(mate_score=10000)

            board.push(engine_move)
            updated_fen = board.fen()

            effective_groq_key = groq_api_key or os.getenv("GROQ_API_KEY")
            ai_explanation = "A Groq API kulcs hiányzik a szakértői magyarázathoz."
            if effective_groq_key:
                try:
                    client = Groq(api_key=effective_groq_key)
                    prompt = (
                        f"Te egy mester sakkoktató vagy. Az új FEN állás a táblán: {updated_fen}. "
                        f"A Stockfish gép ezt lépte: {engine_move.uci()}. "
                        f"Az állás értékelése centipawnban (pozitív = világos áll jobban): {score}. "
                        "Magyarázd el magyarul, miért ez volt a gép lépése, és mit tegyen most a játékos (max 4-5 mondat)."
                    )
                    completion = client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=400,
                    )
                    ai_explanation = completion.choices[0].message.content
                except Exception as ai_err:
                    ai_explanation = f"Hiba az AI elemzés közben: {str(ai_err)}"

            return {
                "success": True,
                "new_fen": updated_fen,
                "engine_move_uci": engine_move.uci(),
                "from_square": engine_move.from_square,
                "to_square": engine_move.to_square,
                "evaluation": score,
                "ai_explanation": ai_explanation,
                "game_over": board.is_game_over(),
                "error": None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
