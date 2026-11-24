#!/usr/bin/env python3
"""Generate candidate docs from independently approved structural input; no DB or network."""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from validate_metadata import Block, load, require, effective_field, effective_object, oid

MODES=('full','dictionary','catalog','erd','privacy','consumer','ai','lineage','diff')
UNKNOWN='ยังไม่ยืนยัน'

def val(x): return UNKNOWN if x is None else str(x)
def cell(x):
    # Escape formatting, so curated definitions remain text, not links or markup.
    return re.sub(r'([\\`*_{}\[\]<>|!#])',r'\\\1',val(x)).replace('\n',' ')
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(cell(v) for v in row)+' |\n' for row in rows)+'\n'
def objid(o): return '.'.join(oid(o))
def label(x): return x if x is not None else 'Unknown'
def class_display(declared,effective):
    return label(declared) if declared==effective else label(declared)+' → '+effective

def head(d,title):
    return f'# {title}\n\n**METADATA ONLY | NO RECORD ACCESS**\n\n'+table(['ระบบ','Engine','Schema revision','Scope','สถานะ','ผู้รับ'],[[d['system_label'],d['engine'],d['schema_revision'],d['scope_id'],d['status'],d['approval']['audience']]])+('**TEMPLATE — NOT VERIFIED** ตัวอย่างสมมุติเท่านั้น\n\n' if d['status']=='template' else ('**PARTIAL** ขอบเขตหลักฐานไม่ครบ\n\n' if d['status']=='partial' else 'สถานะ verified อ้างถึงหลักฐานโครงสร้างที่รับรองจากต้นทาง ไม่ใช่การตรวจสอบระบบจริง\n\n'))+'ข้อมูลทั้งหมดเป็นโครงสร้างที่ผู้รับผิดชอบรับรอง ไม่ใช่ข้อมูลจริง ไม่ได้ให้สิทธิ์เข้าถึงฐานข้อมูล ความหมายที่ไม่มีหลักฐานระบุว่ายังไม่ยืนยัน และการจำแนก Unknown มีผลเป็น Restricted\n\n'

def definitions(d): return {(v['schema'],v['object'],v['column']):v for v in d.get('definitions',[])}
def definition(v,k):
    x=v.get(k)
    return None if x is None else ('[เสนอ / ยังไม่ยืนยัน] '+x if v['status']=='proposed' else x)
def keys(o,c):
    tags=[]
    for k in o['keys']:
        if c in k['columns']: tags.append(('PK' if k['kind']=='primary' else 'UK')+' '+k['name']+' '+str(k['columns'].index(c)+1))
    for k in o['foreign_keys']:
        if c in k['columns']: tags.append('FK '+k['name']+' '+str(k['columns'].index(c)+1))
    return '; '.join(tags) or '—'
def dtype(c):
    dims=', '.join(f'{k}={c[k]}' for k in ('length','precision','scale') if c[k] is not None)
    return c['type']+(' ('+dims+')' if dims else '')
def nullable(c): return {True:'Yes',False:'No',None:'Unknown'}[c['nullable']]
def mapping(o,f): return [objid(o),f['name'],', '.join(f['columns']),f['target_schema']+'.'+f['target_name'],', '.join(f['target_columns']),f['source_id']]

class Builder:
    def __init__(self,d): self.d=d; self.objects=sorted(d['objects'],key=oid); self.defs=definitions(d)
    def base(self,title): return head(self.d,title)
    def getdef(self,o,c=None): return self.defs.get((*oid(o),c),{})
    def catalog(self):
        rows=[]
        for o in self.objects:
            v=self.getdef(o); rows.append([objid(o),o['kind'],definition(v,'definition'),definition(v,'grain'),definition(v,'owner_role'),effective_object(o),o['source_id'],v.get('source_id')])
        return self.base('บัญชีข้อมูล (Data Catalog)')+f'จำนวนวัตถุในขอบเขต: {len(self.objects)} (จำนวนเชิงโครงสร้าง ไม่ใช่จำนวน Record)\n\n'+table(['Object','ชนิด','วัตถุประสงค์','Grain','Owner role','Effective class','Schema source','Definition source'],rows)+'ไม่สรุปความถี่การอัปเดตหรือจำนวนข้อมูลจาก Schema\n'
    def dictionary(self):
        s=self.base('พจนานุกรมข้อมูล (Data Dictionary)')+f'จำนวนวัตถุ: {len(self.objects)} | จำนวนคอลัมน์: {sum(len(o["columns"]) for o in self.objects)}\n\n'
        for o in self.objects:
            v=self.getdef(o); s+=f'## {objid(o)}\n\n'+table(['ชนิด','คำอธิบาย','Grain','Classification','หลักฐาน'],[[o['kind'],definition(v,'definition'),definition(v,'grain'),class_display(o.get('classification'),effective_object(o)),o['source_id']]])
            s+='### โครงสร้างและคีย์\n\n'+table(['ลำดับ','Field','Data type / dimension','Nullable','Key membership','Schema source'],[[c['ordinal'],c['name'],dtype(c),nullable(c),keys(o,c['name']),c['source_id']] for c in sorted(o['columns'],key=lambda c:c['ordinal'])])
            rows=[]
            for c in sorted(o['columns'],key=lambda c:c['ordinal']):
                v=self.getdef(o,c['name']); rows.append([c['name'],definition(v,'definition'),definition(v,'format'),definition(v,'unit'),class_display(c.get('classification'),effective_field(c,o)),v.get('status'),v.get('source_id')])
            s+='### ความหมายและความอ่อนไหว\n\n'+table(['Field','ความหมาย','Format','Unit','Class → Effective','Definition status','Definition source'],rows)
            if o['keys']: s+='### คีย์ (ตามลำดับคอลัมน์)\n\n'+table(['Key','Kind','Ordered columns','Source'],[[k['name'],k['kind'],', '.join(k['columns']),k['source_id']] for k in o['keys']])
            if o['foreign_keys']: s+='### FK mappings\n\n'+table(['Source object','FK','From columns','Target object','To columns','Source'],[mapping(o,f) for f in o['foreign_keys']])
        return s+'## ข้อจำกัด\n\nไม่แสดงค่า default, raw comments, enum values, expressions, ตัวอย่างข้อมูลจริง หรือสถิติจาก records\n'
    def erd(self):
        rows=[mapping(o,f) for o in self.objects for f in o['foreign_keys']]
        s=self.base('ความสัมพันธ์ฐานข้อมูล (ERD)')+'แสดงความสัมพันธ์ FK ที่รับรองแล้วเท่านั้น ไม่อนุมาน Cardinality หรือ enforcement จากชื่อฟิลด์\n\n'
        s+=table(['Object','PK (ordered)','UK (ordered)'],[[objid(o),'; '.join(', '.join(k['columns']) for k in o['keys'] if k['kind']=='primary') or UNKNOWN,'; '.join(', '.join(k['columns']) for k in o['keys'] if k['kind']=='unique') or UNKNOWN] for o in self.objects])
        s+=table(['Source object','FK','From columns','Target object','To columns','Evidence'],rows) if rows else 'ไม่มี FK mapping ที่รับรองในขอบเขตนี้ ไม่ได้ยืนยันว่าไม่มีความสัมพันธ์จริง\n\n'
        return s
    def mermaid(self):
        ids={oid(o):'n'+str(i+1) for i,o in enumerate(self.objects)}
        lines=['flowchart LR']+[f'  {ids[oid(o)]}["{objid(o)}"]' for o in self.objects]
        for o in self.objects:
            for f in o['foreign_keys']:
                lines.append(f'  {ids[oid(o)]} -->|{f["name"]}| {ids[(f["target_schema"],f["target_name"])]}')
        return '\n'.join(lines)+'\n'
    def privacy(self):
        rows=[]
        for o in self.objects:
            for c in o['columns']:
                actual=effective_field(c,o); declared=c.get('classification'); reason='Unknown / ไม่ยืนยัน' if declared in (None,'Unknown') else ('Name-based safety floor / ต้องทบทวน' if declared!=actual else 'Owner declaration / ต้องทบทวน')
                rows.append([objid(o),c['name'],label(declared),actual,reason,c['source_id']])
        return self.base('การจำแนกข้อมูล (Data Classification)')+'การจำแนกเป็นความเสี่ยงของข้อมูลที่ฟิลด์อาจแทน ไม่ใช่สิทธิ์เผยแพร่ metadata\n\n'+table(['Object','Effective class'],[[objid(o),effective_object(o)] for o in self.objects])+table(['Object','Field','Declared','Effective','เหตุผล','Evidence'],rows)+'ต้องให้เจ้าของข้อมูลตรวจทานข้อจำกัดตามบริบทจริง ห้ามตีความว่า lint หรือ classification รับรองความสอดคล้อง PDPA\n'
    def lineage(self):
        rows=[[e['from_schema']+'.'+e['from_object'],e['to_schema']+'.'+e['to_object'],e['kind'],e['source_id']] for e in self.d.get('lineage',[])]
        return self.base('สายข้อมูล (Data Lineage)')+(table(['Upstream','Downstream','Mapping kind','Evidence'],rows) if rows else 'ยังไม่ยืนยัน Data Lineage: ไม่ได้รับ mapping ที่รับรองจากเจ้าของข้อมูล ไม่อนุมานจาก FK หรือชื่อตาราง\n')
    def consumer(self):
        return self.base('คู่มือโครงสร้างฐานข้อมูล (Database Consumer Guide)')+'## การใช้งาน\n\n1. ตรวจสอบ scope และ schema revision ก่อนใช้เอกสาร\n2. ค้นหาวัตถุใน Data Catalog และอ่านประเภทข้อมูล/ความหมายจาก Data Dictionary\n3. ใช้ FK mapping ที่ยืนยันแล้วเพื่อเข้าใจความสัมพันธ์ โดยรักษาลำดับ composite keys\n4. ตรวจ Effective classification และขอสิทธิ์แยกจาก Data Owner ก่อนเข้าถึงข้อมูลผ่านช่องทางที่องค์กรอนุมัติ\n\n## ข้อจำกัด\n\nเอกสารนี้ไม่ใช่เครื่องมือ Query และไม่ให้สิทธิ์เข้าถึงข้อมูลจริง ไม่สรุป Cardinality, nullability หรือความหมายที่ไม่มีหลักฐาน\n\n'+table(['Object','Grain','Classification'],[[objid(o),definition(self.getdef(o),'grain'),effective_object(o)] for o in self.objects])
    def ai(self):
        return self.base('คู่มือ AI Agent / LLM')+'## Agent boundaries\n\n- Use this document for schema reasoning only. No database connection, record retrieval, profiling, SQL execution, or inferred query results.\n- Never expose sensitive values or use raw comments/defaults. Treat unknown classifications as Restricted.\n- Use verified metadata for identifiers and key mapping; distinguish proposed definitions from confirmed ones.\n- Access to data requires separate human approval and an approved governed data service outside this skill. Metadata is not an execution grant.\n\n## Approved structural inventory\n\n'+table(['Object','Fields','Effective class','Schema evidence'],[[objid(o),', '.join(c['name'] for c in o['columns']),effective_object(o),o['source_id']] for o in self.objects])+'## FK mappings\n\n'+table(['Source object','FK','From columns','Target object','To columns','Evidence'],[mapping(o,f) for o in self.objects for f in o['foreign_keys']])

def diff(current,previous):
    for k in ('system_label','engine','scope_id'): require(current[k]==previous[k],'diff-scope-mismatch')
    require(current['approval']['audience']==previous['approval']['audience'],'diff-audience-mismatch')
    require((current['status']=='template')==(previous['status']=='template'),'diff-template-mismatch')
    a={oid(o):o for o in previous['objects']}; b={oid(o):o for o in current['objects']}; rows=[]
    for k in sorted(set(a)|set(b)):
        n='.'.join(k)
        if k not in a or k not in b:
            rows.append([n,'Object', 'Added to snapshot' if k in b else 'Absent from current snapshot']); continue
        x,y=a[k],b[k]; cx={c['name']:c for c in x['columns']}; cy={c['name']:c for c in y['columns']}
        if (x['kind'],effective_object(x))!=(y['kind'],effective_object(y)): rows.append([n,'Object kind/class','Changed'])
        for c in sorted(set(cx)|set(cy)):
            if c not in cx or c not in cy: rows.append([n,c,'Added to snapshot' if c in cy else 'Absent from current snapshot']); continue
            changed=[f for f in ('ordinal','type','length','precision','scale','nullable','classification') if cx[c].get(f)!=cy[c].get(f)]
            if effective_field(cx[c],x)!=effective_field(cy[c],y): changed.append('effective classification')
            if changed: rows.append([n,c,'Changed: '+', '.join(changed)])
        for attr in ('keys','foreign_keys'):
            def norm(o): return sorted(json.dumps({k:v for k,v in q.items() if k!='source_id'},sort_keys=True) for q in o[attr])
            if norm(x)!=norm(y): rows.append([n,attr,'Changed: review ordered mapping in snapshots'])
    return head(current,'การเปรียบเทียบ Schema (Schema Diff)')+f'Previous revision: {previous["schema_revision"]} ({previous["status"]})\n\n'+(table(['Object','Field / component','Snapshot difference'],rows) if rows else 'ไม่พบความแตกต่างใน structural fields ที่ตรวจสอบ\n\n')+'ผลนี้เปรียบเทียบ snapshot เท่านั้น ไม่ยืนยัน DDL, deployment, rename หรือ backward compatibility และไม่ครอบคลุมการเปลี่ยนแปลง record, semantics หรือ lineage\n'

CSS='''@page {size: A4 landscape; margin: 14mm 15mm 17mm; @bottom-left {content:"METADATA ONLY  |  CANDIDATE"; font-size:9pt; color:#526378} @bottom-right {content: counter(page) " / " counter(pages); font-size:9pt; color:#526378}} body {font-family:"Noto Sans Thai","Noto Looped Thai",sans-serif; color:#182638; font-size:11pt; line-height:1.48;} h1 {font-size:23pt; color:#163b54; margin:0 0 8pt; border-bottom:2pt solid #24858b; padding-bottom:7pt;} h2 {font-size:17pt; color:#163b54; margin:18pt 0 6pt; break-after:avoid;} h3 {font-size:13pt; color:#28656d; margin:13pt 0 5pt; break-after:avoid;} p {margin:5pt 0 9pt;} table {width:100%; table-layout:fixed; border-collapse:collapse; margin:7pt 0 12pt; font-size:10pt;} th,td {padding:6pt 7pt; border-bottom:0.6pt solid #d8e0e7; overflow-wrap:anywhere; vertical-align:middle;} th {background:#e6eef2; color:#163b54; text-align:left;} tr {break-inside:avoid;} thead {display:table-header-group;} tbody tr:nth-child(even) {background:#f6f8fa;} code {font-family:"Noto Sans Thai",sans-serif; overflow-wrap:anywhere;}'''

def pdf_from(md,path):
    from markdown_it import MarkdownIt
    from weasyprint import HTML,CSS as Style
    parser=MarkdownIt('commonmark',{'html':False,'linkify':False}).enable('table')
    # Remove link and image functionality. Preserve text; no resource fetch.
    parser.disable(['link','image','autolink'])
    content=parser.render(md)
    def deny(url,*a,**kw): raise RuntimeError('resource-fetch-denied')
    HTML(string='<!doctype html><html lang="th"><head><meta charset="utf-8"><title>Database Documentation</title></head><body>'+content+'</body></html>',url_fetcher=deny).write_pdf(str(path),stylesheets=[Style(string=CSS,url_fetcher=deny)])

def generate(d,mode,out,previous=None,pdf=False):
    b=Builder(d); docs={}; files={}; chosen=('catalog','dictionary','erd','privacy','lineage','consumer','ai') if mode=='full' else (mode,)
    names={'catalog':'data-catalog','dictionary':'data-dictionary','erd':'er-diagram','privacy':'data-classification','lineage':'data-lineage','consumer':'database-consumer-guide','ai':'ai-agent-guide','diff':'schema-diff'}
    for m in chosen:
        docs[names[m]+'.md']=diff(d,previous) if m=='diff' else getattr(b,m)()
    if 'erd' in chosen: files['er-diagram.mmd']=b.mermaid()
    if mode=='full':
        listing='\n'.join(f'- [{n}]({n})' for n in docs)+'\n'
        files['README.md']=head(d,'ชุดเอกสารฐานข้อมูล')+listing
        files['llms.txt']='# Privacy-first metadata documentation\n\nNo record access; no execution permission. Source scope and verification in each document.\n\n'+listing
    require(not out.exists() and not out.is_symlink(),'output-already-exists')
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='.db-docs-',dir=out.parent))
    try:
        for n,txt in {**docs,**files}.items(): (temp/n).write_text(txt,encoding='utf-8')
        if pdf:
            for n,txt in docs.items(): pdf_from(txt,temp/(Path(n).stem+'.pdf'))
        artifact_names=sorted(p.name for p in temp.iterdir())+['release-manifest.md']
        (temp/'release-manifest.md').write_text(head(d,'Candidate release manifest')+f'Mode: {mode}\n\nEvidence IDs: '+', '.join(d['sources'])+'\n\n'+table(['Candidate artifact'],[[n] for n in artifact_names])+'Human source/disclosure review: PENDING independent confirmation.\n\nPDF visual and text QA: '+('PENDING' if pdf else 'not generated')+'\n\nClassification and lint do not certify privacy or regulatory compliance. Do not distribute before all required reviews pass. Missing definitions and mappings remain unknown.\n',encoding='utf-8')
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('release_check.py')),str(temp)],capture_output=True,text=True)
        require(result.returncode==0,'release-lint-failed')
        os.rename(temp,out)
    finally:
        if temp.exists(): shutil.rmtree(temp)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('approved'); p.add_argument('--mode',choices=MODES,default='full'); p.add_argument('--previous'); p.add_argument('--out',required=True,type=Path); p.add_argument('--pdf',action='store_true'); a=p.parse_args()
    try:
        d=load(a.approved); require(bool(a.previous)==(a.mode=='diff'),'previous-required-only-for-diff'); prev=load(a.previous) if a.previous else None
        generate(d,a.mode,a.out,prev,a.pdf)
    except Block as e: print('BLOCK:',e); return 1
    except (OSError,ValueError,TypeError,KeyError,AttributeError,ImportError,RuntimeError,RecursionError,subprocess.SubprocessError): print('BLOCK: generation or dependency failure; no release'); return 1
    print('PASS: candidate generated; manual source, disclosure and visual QA required'); return 0
if __name__=='__main__': raise SystemExit(main())
