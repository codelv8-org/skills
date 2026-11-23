#!/usr/bin/env python3
"""ทดสอบ API ขององค์ประกอบ เนื้อหา PPTX ที่แก้ไขได้ และการปฏิเสธข้อมูลผิด"""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parent

CODE = r'''
const fs = require('fs');
const PptxGenJS = require('pptxgenjs');
const {SlideUI, tokens, contrast} = require(process.argv[1]);
const outfile = process.argv[2];
const assert = (flag,msg) => {if (!flag)throw new Error(msg)};
assert(contrast(tokens.color.ink,tokens.color.white)>=4.5,'Contrast fails');
const pptx = new PptxGenJS(); pptx.layout='LAYOUT_WIDE';
const ui = new SlideUI(pptx,{brand:'Sample Provider',quoteId:'TEST-001'});
const grid = ui.grid({x:.68,y:2.4,w:11.9,h:3.1},3,6,{gapX:.22,gapY:.2});
assert(grid.length===6&&grid[2].x>grid[1].x&&grid[3].y>grid[0].y,'Grid layout');
assert(grid[0].x+grid[0].w < grid[1].x,'Grid gap');
const stack=ui.stack({x:.68,y:4.8,w:11.9,h:1.0},[2,1],{gap:.2});
assert(stack[0].w>stack[1].w,'Stack ratio');
const slide=pptx.addSlide();ui.slide(slide);
ui.render(slide,{type:'Grid',columns:3,children:[
  {type:'MetricCard',label:'TOTAL',value:'69,000.00 THB',tone:'blue'},
  {type:'MetricCard',label:'DURATION',value:'8 weeks',tone:'green'},
  {type:'MetricCard',label:'INSTALLMENTS',value:'3 stages',tone:'amber'}
]},{x:.68,y:2.2,w:11.9,h:1.5});
ui.render(slide,{type:'Stack',children:[
  {type:'TextCard',title:'INCLUDED',body:'Feature delivery',tone:'green',emphasis:true},
  {type:'TextCard',title:'EXCLUDED',body:'Third-party costs',tone:'red',emphasis:true}
]},{x:.68,y:4.15,w:11.9,h:1.16});
ui.render(slide,{type:'Notice',label:'ACCEPTANCE',body:'Approved scope and UAT',tone:'blue'},
  {x:.68,y:5.62,w:11.9,h:.85});
assert(ui.used.has('Grid')&&ui.used.has('Stack')&&ui.used.has('Notice'),'Registry logging');
let rejected=false;
try{ui.render(slide,{type:'UnknownCard'},{x:1,y:1,w:3,h:1})}catch(e){rejected=true}
assert(rejected,'Unknown component not rejected');
rejected=false;
try{ui.render(slide,{type:'Diagram',nodes:[{id:'A',label:'a'},{id:'B',label:'b'}],
 edges:[{from:'A',to:'ZZZ'}]}, {x:1,y:1,w:3,h:2})}catch(e){rejected=true}
assert(rejected,'Invalid diagram not rejected');
ui.footer(slide,{index:1,total:2});
const second=pptx.addSlide();ui.slide(second);
ui.render(second,{type:'HeroPanel',eyebrow:'SAMPLE',title:'A complete native slide',
 description:'Example of a reusable hero',steps:['Plan','Build','Deliver']},
 {x:0,y:0,w:13.333333,h:4.34});
ui.render(second,{type:'TotalBanner',label:'TOTAL',amount:'69,000.00 THB'},
 {x:.68,y:5.52,w:11.9,h:.83});
ui.footer(second,{index:2,total:2});
pptx.writeFile({fileName:outfile}).then(()=>console.log(JSON.stringify({components:[...ui.used]})))
  .catch(e=>{console.error(e);process.exit(1)});
'''

def main():
    with tempfile.TemporaryDirectory(prefix='slidekit-') as tmp:
        output=Path(tmp)/'component-test.pptx'
        result=subprocess.run(['node','-e',CODE,str(ROOT/'slide_components.js'),str(output)],
                              capture_output=True,text=True,timeout=60)
        if result.returncode:
            raise AssertionError(result.stdout+'\n'+result.stderr)
        with ZipFile(output) as archive:
            names=archive.namelist()
            xml=archive.read('ppt/slides/slide1.xml').decode('utf-8')
            assert xml.count('<a:t>')>=14, 'Text missing; component may be rasterized'
            for text in ('TOTAL','DURATION','69,000.00 THB','ACCEPTANCE','INCLUDED'):
                assert text in xml, 'Native text missing: '+text
            assert not any(name.startswith('ppt/media/') and not name.endswith('/') for name in names), 'Unexpected raster media'
            assert xml.count('<p:sp>')>=15, 'Native shapes missing'
            second=archive.read('ppt/slides/slide2.xml').decode('utf-8')
            assert 'A complete native slide' in second and '69,000.00 THB' in second
        print('PASS slide component registry / grid / stack / invalid inputs / PPTX native text')
        print(result.stdout.strip())

if __name__=='__main__':main()
