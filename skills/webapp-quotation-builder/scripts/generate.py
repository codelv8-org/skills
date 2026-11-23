#!/usr/bin/env python3
"""Generate verified A4 quotation PDF and 16:9 slide PDF from confirmed JSON.

Run from any directory:
  python scripts/generate.py --input data.json --out-dir /mnt/data/quotes

Requires: Python playwright + pymupdf, Chromium/Chrome, Node pptxgenjs,
LibreOffice. Input for final customer documents must come from the discovery flow.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

import fitz
from pricing import QuoteValidationError, calculate, load_quote, money_text, public_math


def E(value) -> str:
    return html.escape(str(value), quote=True)


def image_data_uri(path: str) -> str:
    if not path:
        return ""
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise QuoteValidationError(f"Logo path does not exist: {path}")
    suffix = file_path.suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg", ".webp"):
        raise QuoteValidationError("Logo must be local PNG/JPEG/WebP (SVG conversion not implemented)")
    if file_path.stat().st_size > 4 * 1024 * 1024:
        raise QuoteValidationError("Logo must be less than 4 MB")
    mimetype, _ = mimetypes.guess_type(str(file_path))
    return f"data:{mimetype};base64,{base64.b64encode(file_path.read_bytes()).decode('ascii')}"


def compact_list(items, *, fallback="ตามขอบเขตที่ตกลง", max_items=4):
    if not items:
        return E(fallback)
    return "; ".join(E(x) for x in items[:max_items]) + (f"; และอีก {len(items)-max_items} รายการ (ดูสไลด์สรุป)" if len(items) > max_items else "")


def build_html(data, calc) -> str:
    p, c, q, scope, delivery, support = (data[k] for k in ("provider", "customer", "quotation", "scope", "delivery", "after_sales"))
    commercial = data.get("commercial", {})
    logo = image_data_uri(p.get("logo_path", ""))
    mark = f'<img class="logo" src="{logo}" alt="Provider logo">' if logo else f'<div class="mark">{E(p["name"].strip()[:1].upper())}</div>'
    rows = "\n".join(
        f'<tr><td class="center number">{item["number"]}</td>'
        f'<td><strong>{E(item["name"])}</strong><div class="item-detail">{E(item["detail"])}</div></td>'
        f'<td class="center">{E(str(item["quantity"]))} {E(item["unit"])}</td>'
        f'<td class="number">{money_text(item["unit_price"])}</td>'
        f'<td class="number strong">{money_text(item["total"])}</td></tr>'
        for item in calc["items"]
    )
    discount_row = f'<div class="sum-line"><span>ส่วนลด</span><span>- {money_text(calc["discount"])} ฿</span></div>' if calc["discount"] else ''
    vat_row = (f'<div class="sum-line"><span>ภาษีมูลค่าเพิ่ม (VAT {E(calc["vat_rate"])}%)</span><span>{money_text(calc["vat"])} ฿</span></div>' if calc["vat_registered"] else '<div class="tax-note">ผู้เสนอราคาไม่ได้จดทะเบียน VAT — ไม่คิดภาษีมูลค่าเพิ่ม</div>')
    milestones = "".join(
        f'<div class="milestone"><div class="milestone-top"><span>{E(m["label"])}</span><strong>{E(m["percent"])}%</strong></div>'
        f'<div class="milestone-amount">{money_text(m["amount"])} ฿</div>'
        f'<div class="milestone-trigger">{E(m["trigger"])}</div></div>'
        for m in calc["milestones"]
    )
    demo_banner = '<div class="demo-banner">ข้อมูลสมมติ — ตัวอย่างเท่านั้น ห้ามใช้เป็นใบเสนอราคาจริง</div>' if data.get("demo") else ''
    notes = [
        f'<b>กำหนดส่ง:</b> {E(q["lead_time"])}',
        f'<b>ตรวจรับ:</b> {E(q["acceptance"])}',
        f'<b>แก้ไขงาน:</b> {E(q["revision_policy"])}',
        f'<b>สิทธิซอร์สโค้ด:</b> {E(q["ip_terms"])}',
        f'<b>รับประกัน:</b> {E(support["warranty"])}',
        f'<b>งานเพิ่ม:</b> {E(support["change_rate"])}',
        f'<b>ไม่รวม:</b> {compact_list(scope.get("not_included", []), max_items=3)}',
    ]
    if commercial.get("withholding_note"):
        notes.append(f'<b>หัก ณ ที่จ่าย:</b> {E(commercial["withholding_note"])}')
    notes_html = "".join(f"<li>{n}</li>" for n in notes)
    contact = ' · '.join(E(x) for x in (p.get('phone',''), p.get('email','')) if x)
    return f'''<!DOCTYPE html>
<html lang="th"><head><meta charset="utf-8"><title>Quotation {E(q['number'])}</title>
<style>
@page {{ size: A4 portrait; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: 'Noto Sans Thai', 'Noto Looped Thai', Tahoma, sans-serif; color: #15243a; font-size: 11.5px; line-height: 1.48; background: white; }}
.page {{ width: 210mm; min-height: 297mm; padding: 12mm 13mm 10mm; display: flex; flex-direction: column; position: relative; }}
.demo-banner {{ color: #7c2d12; background: #fff5ed; padding: 5px 10px; border-radius: 4px; font-weight: 700; font-size: 10px; margin: -3mm 0 3mm; }}
.top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; padding-bottom: 12px; border-bottom: 2px solid #2365bf; }}
.brand {{ display: flex; gap: 11px; align-items: center; width: 55%; }}
.mark {{ background: #2563eb; width: 49px; height: 49px; border-radius: 12px; display:flex; align-items:center;justify-content:center; color:white; font-size:25px; font-weight:800; flex: 0 0 49px; }}
.logo {{ width: 58px; height: 51px; object-fit: contain; flex-shrink:0; }}
.provider-name {{ font-size: 15px; font-weight: 800; line-height:1.26; }}
.muted {{ color: #63758c; }}
.brand-sub {{ font-size: 9.7px; margin-top: 3px; line-height: 1.45; }}
.quote-heading {{ width: 42%; text-align: right; }}
.quote-heading .eng {{ font-size: 27px; line-height: 1.1; letter-spacing: -.6px; font-weight: 800; color: #174b96; }}
.quote-heading .thai {{ font-size: 12px; font-weight: 750; margin-bottom:5px; }}
.meta {{ display:grid; grid-template-columns: auto auto; justify-content:end; gap:1px 12px; font-size: 10.3px; }}
.meta span:nth-child(odd) {{ text-align: right; color: #718098; }}
.meta span:nth-child(even) {{ text-align: right; font-weight: 650; }}
.section-head {{ text-transform: uppercase; letter-spacing: .9px; color: #1c63b7; font-size:10px; font-weight:850; margin: 13px 0 5px; }}
.client-grid {{ display:grid; grid-template-columns: 1fr .9fr; gap: 11px; }}
.client-box {{ background:#f2f6fc; border-radius:8px; padding:10px 12px; min-height:58px; }}
.client-box .lbl {{ color: #72839b; font-size: 9px; letter-spacing:.4px; font-weight:750; }}
.client-box .val {{ font-size: 12px; font-weight:700; margin:3px 0; }}
.client-box .sm {{ font-size: 10px; line-height: 1.4; }}
.project {{ margin-top: 11px; }}
.project h1 {{ margin: 0 0 3px; font-size: 16px; line-height: 1.3; }}
.project p {{ margin: 0; color: #5b6a7e; font-size: 10.8px; }}
table {{ width:100%; border-collapse:collapse; margin-top: 12px; table-layout:fixed; font-size:10.5px; }}
col.c0 {{ width:7%; }} col.c1 {{ width:48%; }} col.c2 {{ width:13%; }} col.c3 {{ width:15%; }} col.c4 {{ width:17%; }}
thead th {{ background:#183f75; color:white; font-weight:700; font-size:10px; padding:8px 7px; text-align:left; }}
thead th:first-child {{ border-radius:5px 0 0 0; }} thead th:last-child {{ border-radius:0 5px 0 0; }}
tbody td {{ padding: 7px 7px; vertical-align:middle; border-bottom:1px solid #e6ebf3; overflow-wrap:anywhere; }}
tbody tr:nth-child(even) {{ background: #fafbfd; }}
.item-detail {{ color:#718096; font-size:9.5px; line-height:1.38; margin-top:2px; }}
.number {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }} .center {{ text-align:center; }} .strong {{font-weight:750;}}
.money-row {{ display:grid; grid-template-columns: 1fr 205px; gap:16px; margin-top:8px; align-items:end; }}
.money-note {{ background:#edf5ff; border-left:3px solid #377ada; padding:10px; border-radius:4px; font-size:10px; }}
.money-note strong {{font-size:10.5px;}}
.sum-line {{ display:flex; justify-content:space-between; gap:5px; margin:2px 0; font-size:10.3px; }}
.sum-line span:last-child {{ flex:0 0 auto; white-space:nowrap; text-align:right; }}
.grand {{ border-top:1px solid #b2c5de; padding-top:6px; display:flex; flex-direction:column; align-items:flex-end; gap:2px; color:#174b96; font-size:12px; font-weight:800; }}
.grand .amount {{ font-size:22px; white-space:nowrap; line-height:1.24; }}
.tax-note {{ font-size:9px; color:#65778e; }}
.milestones {{ display:grid; grid-template-columns: repeat({len(calc['milestones'])}, minmax(0,1fr)); gap:7px; }}
.milestone {{ padding:9px; background:#f3f7fc; border:1px solid #e1eaf5; border-radius:7px; min-width:0; }}
.milestone-top {{ display:flex; justify-content:space-between; gap:6px; font-size:10px; color:#53667e; }}
.milestone-top strong {{color:#2460af; font-size:11px;}}
.milestone-amount {{ font-weight:850; color:#122b4d; font-size:13px; margin:4px 0; }}
.milestone-trigger {{font-size:9.2px; color:#677891; line-height:1.4;}}
.terms {{ margin-top: 2px; }}
.terms ul {{ display:grid; grid-template-columns:1fr 1fr; gap: 3px 15px; padding:0; margin:0; list-style:none; font-size:9.6px; line-height:1.48; }}
.terms li {{ position:relative; padding-left:10px; break-inside:avoid; }}
.terms li::before {{ content:'•'; color:#3477d6; position:absolute; left:0; }}
.bottom {{ margin-top:auto; padding-top:11px; }}
.accept {{ display:flex; justify-content:space-between; align-items:end; gap:12px; }}
.accept .ref {{font-size:9.1px; max-width:45%; color:#74849a;}}
.sig {{ width:42%; text-align:center; font-size:9.5px; padding-top:9px; border-top:1px solid #7c8ba0; }}
.footer {{ border-top:1px solid #e0e6ed; margin-top:13px; padding-top:6px; color:#66788d; font-size:9px; display:flex; justify-content:space-between; }}
</style></head><body><div class="page">
{demo_banner}
<div class="top">
  <div class="brand">{mark}<div><div class="provider-name">{E(p['name'])}</div><div class="brand-sub muted">{E(p['address'])}<br>{E(p.get('contact',''))}<br>{contact}</div></div></div>
  <div class="quote-heading"><div class="eng">QUOTATION</div><div class="thai">ใบเสนอราคาพัฒนาระบบ Web App</div>
    <div class="meta"><span>เลขที่</span><span>{E(q['number'])}</span><span>วันที่ออก</span><span>{E(q['issue_date'])}</span><span>ใช้ได้ถึง</span><span>{E(q['valid_until'])}</span></div>
  </div>
</div>
<div class="section-head">เสนอราคาให้ / Prepared for</div>
<div class="client-grid"><div class="client-box"><div class="lbl">ผู้ว่าจ้าง / CUSTOMER</div><div class="val">{E(c['name'])}</div><div class="sm muted">{E(c['address'])} · {E(c['contact'])}</div></div>
<div class="client-box"><div class="lbl">ข้อตกลงหลัก / PROJECT TERMS</div><div class="val">ส่งมอบ {E(q['lead_time'])}</div><div class="sm muted">สกุลเงิน: THB (บาท) · ขอบเขตงาน: ดูสไลด์บริการแนบ</div></div></div>
<div class="project"><h1>{E(q['project_name'])}</h1><p>{E(q['summary'])}</p></div>
<table><colgroup><col class="c0"><col class="c1"><col class="c2"><col class="c3"><col class="c4"></colgroup>
<thead><tr><th class="center">#</th><th>รายการงาน/ขอบเขต</th><th class="center">จำนวน</th><th class="number">ราคาต่อหน่วย</th><th class="number">รวม (บาท)</th></tr></thead><tbody>{rows}</tbody></table>
<div class="money-row"><div class="money-note"><strong>ขอบเขตที่ส่งมอบ</strong><br>{compact_list(delivery['handover'], max_items=4)}<br><span class="muted">รายการนอกขอบเขตที่เพิ่มภายหลัง ใช้ Change Request แยก</span></div>
<div><div class="sum-line"><span>รวมก่อนส่วนลด</span><span>{money_text(calc['subtotal'])} ฿</span></div>{discount_row}{vat_row}<div class="grand"><span>ยอดเสนอราคารวม</span><span class="amount">{money_text(calc['total'])} ฿</span></div></div></div>
<div class="section-head">งวดชำระเงิน / Payment milestones</div><div class="milestones">{milestones}</div>
<div class="section-head">เงื่อนไขสำคัญ / Commercial terms</div><div class="terms"><ul>{notes_html}</ul></div>
<div class="bottom"><div class="accept"><div class="ref">{E(commercial.get('payment_note', 'ชำระเงินตามเหตุการณ์ที่ตกลงกัน'))}<br>โปรดอ้างอิงเลขที่ใบเสนอราคาเมื่อติดต่อผู้ให้บริการ</div><div class="sig">ลงชื่อผู้ยอมรับข้อเสนอ / วันที่</div></div><div class="footer"><span>ใบเสนอราคา (QUOTATION) — ไม่ใช่ใบกำกับภาษี</span><span>{E(q['number'])} · หน้า 1 / 1</span></div></div>
</div></body></html>'''


def require_executable(*names) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError(f"Missing executable: {' or '.join(names)}")


def print_html_to_pdf(html_file: Path, pdf_file: Path):
    from playwright.sync_api import sync_playwright
    chromium = require_executable("chromium", "chromium-browser", "google-chrome")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium, headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1050, "height": 1485}, device_scale_factor=1)
        page.set_content(html_file.read_text(encoding="utf-8"), wait_until="load")
        page.evaluate("() => document.fonts.ready")
        page.pdf(path=str(pdf_file), print_background=True, prefer_css_page_size=True, display_header_footer=False)
        browser.close()


def export_slides_to_pdf(pptx_file: Path, destination: Path, temp_dir: Path):
    soffice = require_executable("soffice", "libreoffice")
    lo_profile = (temp_dir / "lo-profile").absolute().as_uri()
    command = [soffice, f"-env:UserInstallation={lo_profile}", "--headless", "--convert-to", "pdf", "--outdir", str(temp_dir), str(pptx_file)]
    process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=150)
    intermediate = temp_dir / (pptx_file.stem + ".pdf")
    if process.returncode or not intermediate.is_file():
        raise RuntimeError(f"Slide PDF conversion failed: {process.stdout} {process.stderr}")
    shutil.copyfile(intermediate, destination)


def verify_pdf_files(quotation_path: Path, slides_path: Path, calc: dict):
    with fitz.open(quotation_path) as pdf:
        if len(pdf) != 1:
            raise RuntimeError(f"A4 quotation overflow: expected 1 page; got {len(pdf)}. Shorten or regroup scope without deleting terms.")
        page = pdf[0]
        if abs(page.rect.width - 595.28) > 2 or abs(page.rect.height - 841.89) > 2:
            raise RuntimeError(f"Wrong A4 size: {page.rect}")
        text = page.get_text()
        if "QUOTATION" not in text.upper() or money_text(calc["total"]) not in text:
            raise RuntimeError("Quotation verification failed: key heading or grand total absent")
        if len(text.strip()) < 200:
            raise RuntimeError("Quotation has unexpectedly little selectable text")
    with fitz.open(slides_path) as pdf:
        if not 4 <= len(pdf) <= 6:
            raise RuntimeError(f"Expected 4..6 slides, got {len(pdf)}")
        for num, page in enumerate(pdf, start=1):
            w, h = page.rect.width, page.rect.height
            if w <= h or abs((w / h) - 16/9) > 0.08:
                raise RuntimeError(f"Slide {num} is not approximately 16:9 landscape")
            if len(page.get_text().strip()) < 50:
                raise RuntimeError(f"Slide {num} might be blank")
        all_text = "\n".join(page.get_text() for page in pdf)
        if money_text(calc["total"]) not in all_text:
            raise RuntimeError("Slide deck has no matching total")


def make_previews(paths: list[Path], preview_dir: Path):
    preview_dir.mkdir(exist_ok=True, parents=True)
    for pdf_path in paths:
        with fitz.open(pdf_path) as pdf:
            for i, page in enumerate(pdf):
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.1, 1.1), alpha=False)
                pixmap.save(str(preview_dir / f"{pdf_path.stem}-p{i+1}.png"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Confirmed JSON spec")
    parser.add_argument("--out-dir", required=True, help="Output folder for two PDF artifacts")
    parser.add_argument("--keep-pptx", action="store_true", help="Also keep source PPTX in output directory")
    args = parser.parse_args()
    data = load_quote(args.input)
    calc = calculate(data)
    out_dir = Path(args.out_dir).absolute()
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / "_qa"
    temp_dir.mkdir(exist_ok=True)
    quote_file = out_dir / f'quotation-{calc["quote_id"]}.pdf'
    slides_file = out_dir / f'service-overview-{calc["quote_id"]}.pdf'
    html_file = temp_dir / "quotation.html"
    html_file.write_text(build_html(data, calc), encoding="utf-8")
    print_html_to_pdf(html_file, quote_file)
    math_file = temp_dir / "pricing-results.json"
    math_file.write_text(json.dumps(public_math(calc), indent=2, ensure_ascii=False), encoding="utf-8")
    slides_pptx = temp_dir / f'service-overview-{calc["quote_id"]}.pptx'
    node = require_executable("node")
    slide_script = Path(__file__).with_name("build_slides.js")
    process = subprocess.run([node, str(slide_script), str(Path(args.input).absolute()), str(math_file), str(slides_pptx)], capture_output=True, text=True, timeout=150)
    if process.returncode:
        raise RuntimeError(f"Slide generation failed: {process.stdout}\n{process.stderr}")
    export_slides_to_pdf(slides_pptx, slides_file, temp_dir)
    verify_pdf_files(quote_file, slides_file, calc)
    make_previews([quote_file, slides_file], temp_dir / "previews")
    if args.keep_pptx:
        shutil.copyfile(slides_pptx, out_dir / slides_pptx.name)
    print(json.dumps({"quotation_pdf": str(quote_file), "slides_pdf": str(slides_file), "math": public_math(calc), "qa_previews": str(temp_dir / 'previews')}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (QuoteValidationError, RuntimeError, OSError, subprocess.TimeoutExpired) as ex:
        sys.exit(f"ERROR: {ex}")
