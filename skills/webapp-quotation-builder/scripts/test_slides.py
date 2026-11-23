#!/usr/bin/env python3
"""ทดสอบการสร้างใบเสนอราคา PDF และการแบ่งหน้าสไลด์สำหรับเนื้อหายาว

รัน python scripts/test_slides.py
ต้องมี playwright/Chromium, pptxgenjs, soffice, PyMuPDF และฟอนต์ไทย
"""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
EXAMPLE=json.loads((ROOT/'assets/quote-data.example.json').read_text(encoding='utf-8'))


def run_case(name: str, data: dict, expected_pages: int, tmpdir: Path):
    entry=tmpdir/f'{name}.json';entry.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    dest=tmpdir/name
    completed=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/generate.py'),'--input',str(entry),'--out-dir',str(dest),'--keep-pptx'], capture_output=True,encoding='utf-8',timeout=180)
    if completed.returncode:
        raise AssertionError(f'{name} failed: {completed.stdout}\n{completed.stderr}')
    report=json.loads((dest/'_qa/slide-preflight.json').read_text(encoding='utf-8'))
    if report['pages'] != expected_pages or not report['passed']:
        raise AssertionError(f'{name}: unexpected report {report}')
    print(f'PASS {name}: {report["pages"]} pages; PDF content verified')


def main():
    with tempfile.TemporaryDirectory(prefix='quotation-slide-test-') as td:
        work=Path(td)
        case1=copy.deepcopy(EXAMPLE);case1['quotation']['number']='DEMO-BASE-001'
        run_case('base',case1,5,work)
        case2=copy.deepcopy(EXAMPLE);case2['quotation']['number']='DEMO-STRESS-002'
        case2['scope']['modules']=[
            'บัญชีผู้ใช้และสิทธิ์','จองคิวออนไลน์','ปฏิทินและช่วงเวลา','แจ้งเตือนสถานะ',
            'รายงานผู้ดูแล','ประวัติการใช้งาน','ตั้งค่ารอบบริการ','ข้อมูลสาขาและเจ้าหน้าที่',
            'บันทึกความคิดเห็น','พิมพ์เอกสาร','นำเข้าข้อมูล','ตั้งค่าความปลอดภัย'
        ]
        case2['delivery']['phases']=[
            {'name': name, 'duration': f'สัปดาห์ {i+1}'}
            for i,name in enumerate(['สำรวจหน้างาน','เก็บความต้องการ','ออกแบบฐานข้อมูล','ออกแบบหน้าจอ',
                                     'พัฒนา','เชื่อมต่อระบบ','ทดสอบรับมอบ','อบรมผู้ใช้','เริ่มใช้งานจริง'])
        ]
        case2['milestones']=[
            {'label':f'งวดงาน {i+1}','percent':20,'trigger':label}
            for i,label in enumerate(['ยืนยันเริ่มงาน','ส่งแบบหน้าจอ','ส่งส่วนจัดการข้อมูล',
                                      'ส่งระบบเพื่อทดสอบ','ส่งมอบระบบและคู่มือ'])
        ]
        case2['after_sales']['warranty']='รับประกันแก้ไขข้อผิดพลาดตามขอบเขตงานเป็นระยะเวลา 60 วันนับจากวันตรวจรับ โดยแจ้งปัญหาได้ตามช่องทางที่ตกลงร่วมกัน'
        case2['quotation']['ip_terms']='ส่งมอบซอร์สโค้ดของงานที่พัฒนาขึ้นเฉพาะโครงการเมื่อชำระเงินครบถ้วน โดยยังคงสิทธิในไลบรารีและเครื่องมือจากผู้ให้บริการภายนอกตามใบอนุญาตเดิม'
        # ภาพรวม 1 หน้า ขอบเขต 2 แผนงาน 2 งวดชำระ 2 และหลังการขาย 1
        run_case('stress',case2,8,work)
        case3=copy.deepcopy(EXAMPLE);case3['quotation']['number']='DEMO-EDGE-003'
        case3['scope']['modules']=['ระบบรายงาน']
        case3['delivery']['phases']=[{'name':'Go-Live','duration':'สัปดาห์ 8'}]
        case3['milestones']=[{'label':'ส่งมอบครบ','percent':100,'trigger':'ติดตั้งใช้งานจริงและตรวจรับ'}]
        run_case('edge',case3,5,work)
        case4=copy.deepcopy(EXAMPLE);case4['quotation']['number']='DEMO-DIAGRAM-004'
        case4['presentation_diagrams']=[{
            'type':'flow','title':'ขั้นตอนอนุมัติการจองคิว',
            'nodes':[{'id':'a','kind':'start','label':'ผู้ใช้ส่งคำขอ'},
                     {'id':'b','kind':'process','label':'เจ้าหน้าที่ตรวจสอบ'},
                     {'id':'c','kind':'decision','label':'อนุมัติหรือไม่?'},
                     {'id':'d','kind':'end','label':'แจ้งผลการพิจารณา'}],
            'edges':[{'from':'a','to':'b'},{'from':'b','to':'c'},
                     {'from':'c','to':'d','label':'ผ่าน'},
                     {'from':'c','to':'b','label':'แก้ไข'}],
            'note':'ทดสอบการแสดงขั้นตอนตามขอบเขตตัวอย่าง'
        }]
        run_case('diagram',case4,6,work)
    print('All slide/pagination tests passed')


if __name__=='__main__':main()
