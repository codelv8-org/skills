#!/usr/bin/env python3
"""ตรวจการจัดหน้าและความครบถ้วนของข้อมูลในสไลด์ PDF ภาษาไทยสำหรับลูกค้า

วิธีใช้
  python scripts/slide_preflight.py --pdf service-overview.pdf --input quote-data.json --math pricing-results.json

ตรวจข้อมูลที่ขาดและข้อความที่เกินขอบหน้า จากนั้นตรวจภาพเรนเดอร์ทุกหน้าด้วยสายตา
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
import fitz


def norm(value: object) -> str:
    return re.sub(r"[\s\-–—]+", "", unicodedata.normalize("NFC", str(value or ""))).lower()


def thai_phase(value: str) -> str:
    mapped = {
        "uat": "ทดสอบรับมอบ (UAT)",
        "demo": "ระบบตัวอย่าง (Demo)",
        "go-live": "เริ่มใช้งานจริง",
        "go live": "เริ่มใช้งานจริง",
        "deploy": "ติดตั้งระบบ (Deploy)",
        "deployment": "ติดตั้งระบบ (Deploy)",
        "development": "พัฒนาระบบ",
        "design": "ออกแบบระบบ",
        "discovery": "วิเคราะห์ความต้องการ",
    }
    return mapped.get(str(value).lower().strip(), str(value))


def inspect(pdf_path: Path, source: dict, calc: dict) -> dict:
    errs=[]
    counts={}
    titles=[]
    sizes=[]
    with fitz.open(pdf_path) as pdf:
        counts["slides"] = len(pdf)
        if not 5 <= len(pdf) <= 12:
            errs.append(f"Expected 5–12 slides; found {len(pdf)}")
        parts=[]
        for index,page in enumerate(pdf, 1):
            ratio=page.rect.width / page.rect.height
            if abs(ratio - 16/9) > 0.035:
                errs.append(f"Page {index}: wrong ratio {ratio:.3f}")
            text=page.get_text()
            parts.append(text)
            if len(norm(text)) < 50:
                errs.append(f"Page {index}: suspiciously little text")
            if '�' in text or '\ufffd' in text:
                errs.append(f"Page {index}: Unicode replacement glyph")
            if re.search(r"(?i)\b(proposal overview|included scope|delivery roadmap|milestone payments|support & ownership|step\s+0\d)\b",text):
                errs.append(f"Page {index}: English-only design label")
            page_large=[]
            for block in page.get_text('dict')['blocks']:
                if 'lines' not in block:continue
                for line in block['lines']:
                    for span in line['spans']:
                        if not span['text'].strip():continue
                        r=fitz.Rect(span['bbox'])
                        if r.x0 < -0.8 or r.y0 < -0.8 or r.x1 > page.rect.width+0.8 or r.y1 > page.rect.height+0.8:
                            errs.append(f"Page {index}: text outside page ({span['text'][:28]})")
                        sz=span['size']; sizes.append(sz)
                        if sz>=25:page_large.append(span['text'])
            if not page_large:
                errs.append(f"Page {index}: no >=25pt headline/metric")
            titles.append(page_large[:2])
        all_text=norm(' '.join(parts))
    source_modules=source.get('scope',{}).get('modules',[])
    for value in source_modules:
        if norm(thai_phase(value)) not in all_text:
            errs.append('Missing module: '+str(value))
    source_phases=source.get('delivery',{}).get('phases',[])
    for phase in source_phases:
        label=thai_phase(phase['name'])
        if norm(label) not in all_text:
            errs.append('Missing phase: '+str(label))
    milestones=calc.get('milestones',[])
    for m in milestones:
        for value,tag in ((f"{m['percent']}%",'percent'),(f"{float(m['amount']):,.2f}",'amount')):
            if norm(value) not in all_text:
                errs.append(f'Missing payment {tag}: {value}')
        if norm(m['trigger']) not in all_text:
            errs.append(f'Missing payment trigger: {m["trigger"]}')
    grand_total=f"{float(calc['total']):,.2f}"
    if norm(grand_total) not in all_text:
        errs.append(f'Missing quote total: {grand_total}')
    for keyword in ('สิ่งที่ลูกค้าจะได้รับ','จ่ายตามผลงาน','บริการหลังการขาย','ยอดรวมทั้งโครงการ'):
        if norm(keyword) not in all_text:
            errs.append('Missing Thai content signpost: '+keyword)
    for diagram in source.get('presentation_diagrams', []):
        if norm(diagram.get('title','')) not in all_text:
            errs.append('Missing diagram title: '+str(diagram.get('title')))
        for node in diagram.get('nodes',[]):
            if norm(node.get('label')) not in all_text:
                errs.append('Missing diagram node: '+str(node.get('label')))
    expected=1+max(1,(len(source_modules)+5)//6)+len(source.get('presentation_diagrams',[]))+max(1,(len(source_phases)+4)//5)+max(1,(len(milestones)+2)//3)+1
    if counts['slides']!=expected:
        errs.append(f'Unexpected pagination: {counts["slides"]}, expected {expected}')
    return {'passed':not errs,'pages':counts['slides'],'expected_pages':expected,'min_font_pt':round(min(sizes),1) if sizes else None,'max_font_pt':round(max(sizes),1) if sizes else None,'titles':titles,'errors':errs}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',required=True,type=Path)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--math',required=True,type=Path)
    args=parser.parse_args()
    report=inspect(args.pdf,json.loads(args.input.read_text(encoding='utf-8')),json.loads(args.math.read_text(encoding='utf-8')))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['passed']:sys.exit(1)

if __name__=='__main__':main()
