import base64
import datetime
import io
import json
import re
from typing import Any, Dict, cast

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from .models import DBInvoiceModel
from .schemas import StructuredInvoice

MAX_INVOICE_IMAGE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_INVOICE_MIMES = {"image/jpeg", "image/png"}
ALLOWED_INVOICE_PIL_FORMATS = {"JPEG", "PNG"}

router = APIRouter(prefix="/invoices", tags=["Invoices"])


def get_app_state(request: Request):
    return request.app.state


async def _validate_and_read_invoice_image(file: UploadFile) -> tuple[bytes, str]:
    if file.content_type and file.content_type.lower() not in ALLOWED_INVOICE_MIMES:
        raise HTTPException(
            status_code=415,
            detail="Csak JPG, JPEG vagy PNG számlakép tölthető fel.",
        )

    if not file.content_type and file.filename:
        lower_name = file.filename.lower()
        if not lower_name.endswith((".jpg", ".jpeg", ".png")):
            raise HTTPException(
                status_code=415,
                detail="Csak JPG, JPEG vagy PNG számlakép tölthető fel.",
            )

    chunks: list[bytes] = []
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_INVOICE_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="A feltöltött számlakép mérete meghaladja a maximális 50 MB-os limitet.",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=400,
            detail="Üres képfájl érkezett.",
        )

    image_bytes = b"".join(chunks)

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img_format = (img.format or "").upper()
            if img_format not in ALLOWED_INVOICE_PIL_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Csak JPG, JPEG vagy PNG számlakép tölthető fel.",
                )
            img.verify()

        resolved_mime = "image/png" if img_format == "PNG" else "image/jpeg"
        return image_bytes, resolved_mime
    except HTTPException:
        raise
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=400,
            detail="A feltöltött fájl nem érvényes vagy sérült képfájl.",
        )


def _extract_json_object(reply_text: str) -> Dict[str, Any]:
    json_str_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply_text, re.DOTALL)
    if json_str_match:
        json_str = json_str_match.group(1)
    else:
        json_str_match_simple = re.search(r"\{.*\}", reply_text, re.DOTALL)
        json_str = json_str_match_simple.group(0) if json_str_match_simple else "{}"

    parsed = json.loads(json_str)
    return parsed if isinstance(parsed, dict) else {}


@router.post("/process_invoice")
async def process_invoice(
    request: Request,
    session_id: str = Form(...),
    file: UploadFile = File(...),
):
    state = get_app_state(request)
    groq_client = state.groq_client
    mongo_client = state.mongo_client
    invoices_coll = mongo_client["mi_kurzus"]["invoices"]

    try:
        image_bytes, mime_type = await _validate_and_read_invoice_image(file)
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "Vizsgáld meg a csatolt képet, és döntsd el, hogy számla vagy nyugta-e. "
            "Ha a kép NEM számla és NEM nyugta, ne találj ki adatokat, hanem pontosan ezt a JSON-t add vissza:\n"
            '{"is_invoice": false, "message": "A csatolt kép nem számla vagy nyugta."}\n\n'
            "Ha a kép SZÁMLA vagy NYUGTA, add vissza az adatait pontosan az alábbi JSON struktúrában. "
            "Ne írj semmi mást, csak tiszta JSON objektumot:\n"
            "{\n"
            '  "is_invoice": true,\n'
            '  "partner_name": "Kiállító/Partner neve",\n'
            '  "tax_number": "Adószám vagy HU... ha van",\n'
            '  "total_amount": 0.0,\n'
            '  "fulfillment_date": "ÉÉÉÉ-HH-NN",\n'
            '  "cost_category": "Anyagköltség vagy Igénybe vett szolgáltatás vagy Áruk beszerzése (ELÁBÉ) vagy Tárgyi eszköz beszerzés vagy Egyéb rezsi",\n'
            '  "items": [{"description": "megnevezés", "quantity": 1.0, "unit_price": 0.0, "total_price": 0.0}]\n'
            "}\n\n"
            "A 'cost_category' mezőbe KIZÁRÓLAG az alábbi 5 kategória egyikét írhatod bele, pontosan így:\n"
            "- Anyagköltség\n"
            "- Igénybe vett szolgáltatás\n"
            "- Áruk beszerzése (ELÁBÉ)\n"
            "- Tárgyi eszköz beszerzés\n"
            "- Egyéb rezsi"
        )

        response = await cast(Any, groq_client.chat.completions).create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=800,
            temperature=0,
        )

        reply_text = response.choices[0].message.content or ""
        parsed_data = _extract_json_object(reply_text)

        if parsed_data.get("is_invoice") is False:
            raise HTTPException(
                status_code=400,
                detail=parsed_data.get("message") or "A csatolt kép nem számla vagy nyugta.",
            )

        if parsed_data.get("total_amount") is None:
            parsed_data["total_amount"] = 0.0
        if not parsed_data.get("partner_name"):
            parsed_data["partner_name"] = "Ismeretlen"
        if not parsed_data.get("fulfillment_date"):
            parsed_data["fulfillment_date"] = datetime.date.today().isoformat()
        if not parsed_data.get("cost_category"):
            parsed_data["cost_category"] = "Egyéb rezsi"
        if parsed_data.get("items") is None:
            parsed_data["items"] = []

        try:
            structured = StructuredInvoice(**parsed_data)
        except ValidationError as val_exc:
            raise HTTPException(
                status_code=422,
                detail=f"A kinyert számlaadatok szerkezete érvénytelen: {val_exc}",
            ) from val_exc

        db_invoice = DBInvoiceModel(
            session_id=session_id,
            filename=file.filename or "",
            partner_name=structured.partner_name,
            tax_number=structured.tax_number or "Nincs megadva",
            total_amount=float(structured.total_amount),
            fulfillment_date=structured.fulfillment_date,
            cost_category=structured.cost_category,
            items=[item.model_dump() for item in structured.items],
        )

        invoice_record = {
            **db_invoice.model_dump(),
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        }

        await invoices_coll.insert_one(invoice_record)
        invoice_record.pop("_id", None)
        invoice_record.pop("created_at", None)

        return {
            "status": "success",
            "message": "A számla sikeresen feldolgozva és mentve a MongoDB-be!",
            "data": invoice_record,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Hiba a számla feldolgozása közben: {str(exc)}",
        ) from exc


@router.get("/get/{session_id}")
async def get_invoices(request: Request, session_id: str):
    state = get_app_state(request)
    invoices_coll = state.mongo_client["mi_kurzus"]["invoices"]

    cursor = invoices_coll.find({"session_id": session_id})
    invoices = await cursor.to_list(length=100)

    for inv in invoices:
        inv["_id"] = str(inv["_id"])
        if "created_at" in inv and hasattr(inv["created_at"], "isoformat"):
            inv["created_at"] = inv["created_at"].isoformat()

    return {"invoices": invoices}


@router.get("/analyze_invoices_report")
async def analyze_invoices_report(request: Request):
    state = get_app_state(request)
    groq_client = state.groq_client
    invoices_coll = state.mongo_client["mi_kurzus"]["invoices"]

    cursor = invoices_coll.find({})
    invoices = await cursor.to_list(length=500)

    if not invoices:
        return {
            "report": "Még nincsenek rögzített számlák az adatbázisban.",
            "summary_data": {},
        }

    summary: Dict[str, Dict[str, float]] = {}
    for inv in invoices:
        date_str = str(inv.get("fulfillment_date") or "2026-01-01")
        year = date_str.split("-")[0] if "-" in date_str else "2026"
        cost_cat = str(inv.get("cost_category") or "Egyéb rezsi")
        amount = float(inv.get("total_amount") or 0.0)

        if year not in summary:
            summary[year] = {}
        summary[year][cost_cat] = summary[year].get(cost_cat, 0.0) + amount

    prompt = (
        "Az alábbiakban egy vállalkozás számlaadatai láthatók évek és adónemek (költségkategóriák) szerint összesítve:\n"
        f"{str(summary)}\n\n"
        "Kérlek, készíts egy részletes, szakmai pénzügyi elemzést és értékelést magyar nyelven! "
        "Mutass rá a főbb költségtendenciákra, az adónemek szerinti megoszlásra, és adj pénzügyi tanácsokat a költségek optimalizálására."
    )

    response = await cast(Any, groq_client.chat.completions).create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
    )

    report_text = response.choices[0].message.content or "Nincs értékelés."

    return {
        "summary_data": summary,
        "report": report_text,
    }
