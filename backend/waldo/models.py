import io
import re
import time
import base64
from PIL import Image, ImageDraw


def parse_and_annotate_waldo(reply_text: str, start_time: float, image: Image.Image, width: int, height: int,
                             model_name: str) -> dict:
    elapsed = round(time.time() - start_time, 2)
    annotated_b64 = None
    found = False

    # 1. Próbáljunk meg bármilyen 4 számot találni szögletes, kerek zárójelben vagy akár anélkül
    # Ez a regex keres 4 darab számot (egész vagy tizedes) vesszőkkel elválasztva
    coord_match = re.search(
        r"(?:\[|\(|\b)?\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:\]|\)|\b)?",
        reply_text
    )

    # Megvizsgáljuk, hogy a válasz tartalmazza-e a YES szót, vagy pozitív jelzést ad
    is_positive = bool(re.search(r"(YES|FOUND|igen|itt van|megvan)", reply_text, re.IGNORECASE)) or bool(coord_match)

    if is_positive and coord_match:
        try:
            numbers = [float(g) for g in coord_match.groups() if g is not None]
            if len(numbers) >= 4:
                ymin, xmin, ymax, xmax = map(int, numbers[:4])
                found = True

                # Koordináták átszámítása 0-1000 skáláról a kép tényleges pixelméretére
                left = round(xmin * width / 1000)
                top = round(ymin * height / 1000)
                right = round(xmax * width / 1000)
                bottom = round(ymax * height / 1000)

                # Biztosítjuk, hogy a koordináták ne lógjanak ki a képből
                left = max(0, min(width, left))
                top = max(0, min(height, top))
                right = max(0, min(width, right))
                bottom = max(0, min(height, bottom))

                box = [left, top, right, bottom]

                annotated = image.copy()
                draw = ImageDraw.Draw(annotated)

                # Dinamikus keretvastagság
                line_width = max(4, round(min(width, height) / 200))
                draw.rectangle(box, outline="red", width=line_width)

                buffered = io.BytesIO()
                annotated.save(buffered, format="JPEG", quality=92)
                annotated_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"Hiba a koordináták feldolgozásakor ({model_name}): {e}")

    return {
        "model": model_name,
        "response": reply_text,
        "found": found,
        "time": elapsed,
        "annotated_image": annotated_b64
    }
