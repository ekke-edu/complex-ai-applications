import requests
import streamlit as st

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


def _extract_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("detail") is not None:
            detail = payload["detail"]
            if isinstance(detail, str):
                return detail
            return str(detail)
    except ValueError:
        pass
    return response.text or f"Hiba történt (HTTP {response.status_code})."


def render_invoice_tab(api_base_url: str):
    st.header("🧾 Intelligens Számla- és Nyugtafeldolgozó Rendszer")

    inv_sub_tab1, inv_sub_tab2 = st.tabs([
        "📤 Számla Feltöltés & Mentés",
        "📊 Adónemenkénti Elemzés & Diagramok",
    ])

    # --- 1. AL-FÜL: Számla Feltöltés & Mentés (max 50 MB / kép) ---
    with inv_sub_tab1:
        st.subheader("Számla / Nyugta beküldése és struktúrált kinyerése")
        st.caption(
            f"Támogatott formátum: JPG, JPEG, PNG — maximum {MAX_IMAGE_SIZE_MB} MB / kép."
        )

        uploaded_invoice = st.file_uploader(
            f"Tölts fel egy számlát vagy nyugtát (JPG, PNG — max. {MAX_IMAGE_SIZE_MB} MB):",
            type=["jpg", "jpeg", "png"],
            key="invoice_uploader",
        )

        if uploaded_invoice is not None:
            size_mb = uploaded_invoice.size / (1024 * 1024)
            is_valid_size = _is_within_size_limit(uploaded_invoice)

            if not is_valid_size:
                st.error(
                    f"❌ A feltöltött fájl mérete ({size_mb:.1f} MB) meghaladja a "
                    f"képenkénti {MAX_IMAGE_SIZE_MB} MB-os limitet!"
                )
            else:
                st.image(
                    uploaded_invoice,
                    caption=f"Feltöltött számla ({size_mb:.1f} MB)",
                    width=400,
                )

            if st.button(
                "Számla Feldolgozása & Mentés MongoDB-be 🚀",
                type="primary",
                key="process_inv_btn",
                disabled=not is_valid_size,
            ):
                with st.spinner("A Qwen Vision elemzi a számlát és kinyeri az adatokat..."):
                    try:
                        files = {
                            "file": (
                                uploaded_invoice.name,
                                uploaded_invoice.getvalue(),
                                _resolve_image_mime_type(uploaded_invoice),
                            )
                        }
                        data = {"session_id": st.session_state.session_id}

                        res = requests.post(
                            f"{api_base_url}/invoices/process_invoice",
                            files=files,
                            data=data,
                            timeout=90,
                        )

                        if res.status_code == 200:
                            res_data = res.json()
                            st.success(
                                res_data.get("message")
                                or "A számla sikeresen feldolgozva és mentve!"
                            )

                            inv_info = res_data.get("data", {})
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(
                                    label="Partner Neve",
                                    value=inv_info.get("partner_name", "Ismeretlen"),
                                )
                                st.text(f"Adószám: {inv_info.get('tax_number', '')}")
                                st.text(f"Teljesítés: {inv_info.get('fulfillment_date', '')}")
                            with col2:
                                st.metric(
                                    label="Végösszeg",
                                    value=f"{inv_info.get('total_amount', 0.0)} Ft",
                                )
                                st.text(
                                    f"Költségtípus: {inv_info.get('cost_category', '')}"
                                )

                            if inv_info.get("items"):
                                st.markdown("##### Tételek:")
                                st.json(inv_info.get("items"))
                        else:
                            err_msg = _extract_error_message(res)
                            if res.status_code == 400 and (
                                "nem számla" in err_msg.lower()
                                or "nyugta" in err_msg.lower()
                            ):
                                st.warning(f"⚠️ {err_msg}")
                            else:
                                st.error(f"❌ {err_msg} (HTTP {res.status_code})")

                    except requests.Timeout:
                        st.error(
                            "❌ A számla feldolgozása túllépte az időkorlátot. Próbáld újra!"
                        )
                    except Exception as e:
                        st.error(f"❌ Hiba történt: {e}")

    # --- 2. AL-FÜL: Adónemenkénti Elemzés & Diagramok ---
    with inv_sub_tab2:
        st.subheader("Költségek csoportosítása évek és kategóriák szerint")

        if st.button("🔄 Jelentés és Elemzés Frissítése", key="refresh_report_btn"):
            with st.spinner("Adatok lekérdezése és MI elemzés generálása..."):
                try:
                    res = requests.get(
                        f"{api_base_url}/invoices/analyze_invoices_report",
                        timeout=90,
                    )
                    if res.status_code == 200:
                        report_data = res.json()
                        summary = report_data.get("summary_data", {})
                        report_text = report_data.get("report", "")

                        if not summary:
                            st.warning("Még nincsenek rögzített számlák az adatbázisban.")
                        else:
                            st.success("Sikeres elemzés!")

                            st.markdown("### 🤖 MI Pénzügyi Szakértői Vélemény")
                            st.info(report_text)

                            st.divider()
                            st.markdown("### 📊 Vizuális Diagramok & Adatok")

                            flat_rows = []
                            for year, categories in summary.items():
                                for cat, amount in categories.items():
                                    flat_rows.append({
                                        "Év": str(year),
                                        "Költségtípus": str(cat),
                                        "Összeg (Ft)": float(amount),
                                    })

                            if flat_rows:
                                max_amount = max(row["Összeg (Ft)"] for row in flat_rows) or 1.0
                                colors = ["#4F46E5", "#0EA5E9", "#10B981", "#F59E0B", "#EF4444"]
                                years = sorted({row["Év"] for row in flat_rows})
                                year_color_map = {
                                    y: colors[i % len(colors)] for i, y in enumerate(years)
                                }

                                bars_html = [
                                    "<div style='display:flex; flex-direction:column; gap:10px; margin:12px 0;'>"
                                ]
                                for row in flat_rows:
                                    pct = max(2.0, (row["Összeg (Ft)"] / max_amount) * 100.0)
                                    bar_color = year_color_map[row["Év"]]
                                    bars_html.append(
                                        f"<div>"
                                        f"<div style='display:flex; justify-content:space-between; font-size:14px; margin-bottom:3px;'>"
                                        f"<span><b>{row['Költségtípus']}</b> ({row['Év']})</span>"
                                        f"<span>{row['Összeg (Ft)']:,.0f} Ft</span>"
                                        f"</div>"
                                        f"<div style='width:100%; background:#e5e7eb; border-radius:6px; height:18px; overflow:hidden;'>"
                                        f"<div style='width:{pct:.1f}%; background:{bar_color}; height:100%;'></div>"
                                        f"</div>"
                                        f"</div>"
                                    )
                                bars_html.append("</div>")
                                st.markdown("".join(bars_html), unsafe_allow_html=True)

                                st.markdown("##### Részletes adatok táblázatban:")
                                table_html = [
                                    "<table style='width:100%; border-collapse:collapse; margin-top:8px;'>",
                                    "<thead><tr style='border-bottom:2px solid #d1d5db; text-align:left;'>"
                                    "<th style='padding:8px;'>Év</th>"
                                    "<th style='padding:8px;'>Költségtípus</th>"
                                    "<th style='padding:8px; text-align:right;'>Összeg (Ft)</th>"
                                    "</tr></thead><tbody>",
                                ]
                                for row in flat_rows:
                                    table_html.append(
                                        f"<tr style='border-bottom:1px solid #e5e7eb;'>"
                                        f"<td style='padding:8px;'>{row['Év']}</td>"
                                        f"<td style='padding:8px;'>{row['Költségtípus']}</td>"
                                        f"<td style='padding:8px; text-align:right;'>{row['Összeg (Ft)']:,.0f} Ft</td>"
                                        f"</tr>"
                                    )
                                table_html.append("</tbody></table>")
                                st.markdown("".join(table_html), unsafe_allow_html=True)
                    else:
                        err_msg = _extract_error_message(res)
                        st.error(f"❌ {err_msg} (HTTP {res.status_code})")
                except requests.Timeout:
                    st.error("❌ A jelentés generálása túllépte az időkorlátot.")
                except Exception as e:
                    st.error(f"❌ Hiba a jelentés készítése közben: {e}")
