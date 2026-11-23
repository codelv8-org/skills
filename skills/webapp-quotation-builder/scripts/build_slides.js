#!/usr/bin/env node
/**
 * สร้างสไลด์ข้อเสนอ 16:9 ภาษาไทยพร้อมแผนภาพและการแบ่งหน้าตามเนื้อหา
 * วิธีใช้
 *   node scripts/build_slides.js <confirmed-quote.json> <public-math.json> <out.pptx>
 * ใช้ PptxGenJS สร้างองค์ประกอบที่แก้ไขได้ แล้วส่งออก PDF ใน generate.py
 */
'use strict';
const fs = require('fs');
const path = require('path');
const child = require('child_process');
const pptxgen = require('pptxgenjs');
let helpers;
try {
  helpers = require(process.env.SLIDES_HELPERS || '/home/oai/skills/slides/pptxgenjs_helpers/index.js');
} catch (error) { throw new Error('Slide helpers unavailable; activate slides skill / set SLIDES_HELPERS: '+error.message); }
const { SlideUI } = require('./slide_components');
const { warnIfSlideElementsOutOfBounds } = helpers;
const [inputPath, mathPath, outPath] = process.argv.slice(2);
if (!inputPath || !mathPath || !outPath) throw new Error('Usage: build_slides.js <data.json> <math.json> <out.pptx>');
const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const math = JSON.parse(fs.readFileSync(mathPath, 'utf8'));
const p = data.provider, q = data.quotation, d = data.delivery, sc = data.scope, support = data.after_sales;
const milestones = math.milestones || [];
if (!p || !q || !d || !sc || !support || !milestones.length) throw new Error('Missing confirmed quote sections');
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = p.name;
pptx.company = p.name;
pptx.title = 'ข้อเสนอโครงการ ' + q.project_name;
pptx.subject = 'ภาพรวมบริการ เลขที่ ' + q.number;
pptx.lang = 'th-TH';

function resolveThaiFont() {
  const requested = (data.presentation_style && data.presentation_style.font) || 'Noto Sans Thai';
  try {
    const found = child.execFileSync('fc-match', ['-f', '%{family}', requested], {encoding:'utf8', timeout:2000});
    if (found.toLowerCase().includes(requested.toLowerCase())) return requested;
  } catch (_e) { /* ใช้ฟอนต์ค่าเริ่มต้นด้านล่างเมื่อหาไม่พบ */ }
  return 'Noto Sans Thai';
}
const FONT = resolveThaiFont();
pptx.theme = {headFontFace: FONT,bodyFontFace:FONT,lang:'th-TH'};
const W=13.333333333,H=7.5,M=0.68,INNER=W-2*M;
const S=pptx.ShapeType;
const ui = new SlideUI(pptx,{font:FONT,logoPath:p.logo_path,brand:p.name,quoteId:q.number});
const C=ui.C;
const PT={hero:35,title:29,number:29,step:19,body:18,detail:16,meta:14,footer:10};
const slides=[];
// วาดรูปทรงเวกเตอร์เฉพาะที่ต้องกำหนดเอง ส่วนองค์ประกอบซ้ำใช้ render() ของ SlideUI
function addBackground(slide,color=C.bg){ui.slide(slide,color);}
function box(slide,x,y,w,h,fill=C.white,stroke=null,radius=true){
  return ui.rect(slide,{x,y,w,h},{fill,stroke,round:radius});
}
function line(slide,x1,y1,x2,y2,color=C.line,width=1.5){ui.line(slide,x1,y1,x2,y2,color,width);}
function txt(slide,value,x,y,w,h,size=PT.body,opts={}){
  ui.text(slide,value,{x,y,w,h},{size,min:opts.minSize??null,...Object.fromEntries(
    Object.entries(opts).filter(([k])=>k!=='minSize'))});
}
function logo(slide,x=11.46,y=0.5,w=1.18,h=0.52,onDark=false){
  ui.logo(slide,{x,y,w,h},{onDark});
}
function thaiPhase(input){
  const s=String(input||'').trim();
  const map={
    uat:'\u0e17\u0e14\u0e2a\u0e2d\u0e1a\u0e23\u0e31\u0e1a\u0e21\u0e2d\u0e1a (UAT)',
    demo:'\u0e23\u0e30\u0e1a\u0e1a\u0e15\u0e31\u0e27\u0e2d\u0e22\u0e48\u0e32\u0e07 (Demo)',
    'go-live':'\u0e40\u0e23\u0e34\u0e48\u0e21\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19\u0e08\u0e23\u0e34\u0e07',
    'go live':'\u0e40\u0e23\u0e34\u0e48\u0e21\u0e43\u0e0a\u0e49\u0e07\u0e32\u0e19\u0e08\u0e23\u0e34\u0e07',
    deploy:'\u0e15\u0e34\u0e14\u0e15\u0e31\u0e49\u0e07\u0e23\u0e30\u0e1a\u0e1a (Deploy)',
    deployment:'\u0e15\u0e34\u0e14\u0e15\u0e31\u0e49\u0e07\u0e23\u0e30\u0e1a\u0e1a (Deploy)',
    development:'\u0e1e\u0e31\u0e12\u0e19\u0e32\u0e23\u0e30\u0e1a\u0e1a',
    design:'\u0e2d\u0e2d\u0e01\u0e41\u0e1a\u0e1a\u0e23\u0e30\u0e1a\u0e1a',
    discovery:'\u0e27\u0e34\u0e40\u0e04\u0e23\u0e32\u0e30\u0e2b\u0e4c\u0e04\u0e27\u0e32\u0e21\u0e15\u0e49\u0e2d\u0e07\u0e01\u0e32\u0e23'
  };
  return map[s.toLowerCase()]||s;
}
function shortDelivery(value) {
  const source=String(value||'').trim();
  const match=source.match(/^(ประมาณ\s*)?([0-9]+(?:\s*[-–]\s*[0-9]+)?\s*(?:สัปดาห์|เดือน|วัน|ปี))/);
  return match?match[0]:source;
}

function stamp(slide){
  if(data.demo)txt(slide,'\u0e15\u0e31\u0e27\u0e2d\u0e22\u0e48\u0e32\u0e07\u0e40\u0e17\u0e48\u0e32\u0e19\u0e31\u0e49\u0e19',7.25,7.04,2.24,.22,9,{color:C.red,align:'right',minSize:9});
}
function newSlide(name,meta={}){const slide=pptx.addSlide();addBackground(slide);slides.push({slide,name,meta});return slide;}
function sectionHead(slide,eyebrow,title,subtitle){ui.header(slide,{eyebrow,title,subtitle});}
function chunk(items,n){const out=[];for(let i=0;i<items.length;i+=n)out.push(items.slice(i,i+n));return out;}
function listSentence(a){return (a||[]).filter(Boolean).join('  |  ');}
function pagedLabel(section,index,total){return total>1?`${section} (${index+1}/${total})`:section;}

function amount(v){return Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' บาท';}
// หน้าแรกแสดงผลลัพธ์โครงการและตัวเลขจากใบเสนอราคา
{
  const s=newSlide('ภาพรวมโครงการ');
  ui.render(s,{type:'HeroPanel',eyebrow:'ข้อเสนอการพัฒนาเว็บแอปพลิเคชัน',title:q.project_name,
    description:q.summary,steps:['วิเคราะห์ความต้องการ','พัฒนาและทดสอบ','ตรวจรับและส่งมอบ']},{x:0,y:0,w:W,h:4.34});
  ui.render(s,{type:'Grid',columns:3,gapX:.20,children:[
    {type:'MetricCard',label:'\u0e21\u0e39\u0e25\u0e04\u0e48\u0e32\u0e42\u0e04\u0e23\u0e07\u0e01\u0e32\u0e23',value:amount(math.total),tone:'blue'},
    {type:'MetricCard',label:'\u0e23\u0e30\u0e22\u0e30\u0e40\u0e27\u0e25\u0e32\u0e14\u0e33\u0e40\u0e19\u0e34\u0e19\u0e07\u0e32\u0e19',value:shortDelivery(q.lead_time),tone:'green'},
    {type:'MetricCard',label:'\u0e40\u0e07\u0e37\u0e48\u0e2d\u0e19\u0e44\u0e02\u0e01\u0e32\u0e23\u0e0a\u0e33\u0e23\u0e30',value:`${milestones.length} \u0e07\u0e27\u0e14\u0e15\u0e32\u0e21\u0e1c\u0e25\u0e07\u0e32\u0e19`,tone:'amber'}
  ]},{x:M,y:4.70,w:INNER,h:1.51});
  txt(s,`\u0e01\u0e33\u0e2b\u0e19\u0e14\u0e40\u0e27\u0e25\u0e32: ${q.lead_time}`,M,6.40,INNER,.34,PT.meta,{color:C.muted,minSize:13});
}

// หน้าขอบเขตงานแสดงสูงสุด 6 การ์ดต่อหน้า
const modules = Array.isArray(sc.modules)&&sc.modules.length?sc.modules:['รายละเอียดงานตามขอบเขตที่ตกลง'];
const modulePages=chunk(modules,6);
modulePages.forEach((page,pageIndex)=>{
  const s=newSlide('ขอบเขตงานที่ได้รับ');
  sectionHead(s,'ขอบเขตงาน',pagedLabel('สิ่งที่ลูกค้าจะได้รับ',pageIndex,modulePages.length),'แสดงรายการระบบและความสามารถหลักที่รวมอยู่ในข้อเสนอ');
  ui.render(s,{type:'Grid',columns:3,gapX:.22,gapY:.21,
    children:page.map((label,i)=>({type:'FeatureCard',label:thaiPhase(label),index:pageIndex*6+i+1}))
  },{x:M,y:2.27,w:INNER,h:page.length>3?3.12:1.43});
  ui.render(s,{type:'Stack',direction:'row',gap:.23,children:[
    {type:'TextCard',title:'\u0e2a\u0e34\u0e48\u0e07\u0e17\u0e35\u0e48\u0e08\u0e30\u0e2a\u0e48\u0e07\u0e21\u0e2d\u0e1a',body:listSentence(d.handover),tone:'green',emphasis:true},
    {type:'TextCard',title:'\u0e2a\u0e34\u0e48\u0e07\u0e17\u0e35\u0e48\u0e44\u0e21\u0e48\u0e23\u0e27\u0e21\u0e43\u0e19\u0e23\u0e32\u0e04\u0e32',body:listSentence(sc.not_included),tone:'red',emphasis:true}
  ]},{x:M,y:5.63,w:INNER,h:1.08});
});

// ใช้โหนดและเส้นเชื่อมที่ยืนยันแล้ว ไล่จากซ้ายไปขวาและย้อนจากจุดตัดสินใจได้หนึ่งเส้น
const optionalDiagrams = Array.isArray(data.presentation_diagrams)?data.presentation_diagrams:[];
if(optionalDiagrams.length>2)throw new Error('Maximum two extra customer-facing diagrams; combine detail externally');
optionalDiagrams.forEach((diagram,diagramIndex)=>{
  const nodes=diagram.nodes||[], edges=diagram.edges||[];
  if(!['flow','architecture'].includes(diagram.type)||nodes.length<2||nodes.length>5||!Array.isArray(edges))
    throw new Error('Invalid presentation_diagrams['+diagramIndex+']: supported type + 2..5 nodes required');
  const ids=nodes.map(n=>n.id);
  if(new Set(ids).size!==ids.length || ids.some(id=>typeof id!=='string'||!id)) throw new Error('Diagram node ids must be non-empty and unique');
  const byId=new Map(nodes.map((n,i)=>[n.id,i]));
  let backEdges=0;
  for(const e of edges){
    if(!byId.has(e.from)||!byId.has(e.to))throw new Error('Diagram edge refers to an unknown node');
    const delta=byId.get(e.to)-byId.get(e.from);
    if(delta===-1){backEdges++;if(diagram.type!=='flow'||nodes[byId.get(e.from)].kind!=='decision')throw new Error('Back edge allowed only from decision to prior step');}
    else if(delta!==1)throw new Error('Diagram only supports direct forward steps and one-step decision revision loops; use custom renderer for complex graph');
    if(backEdges>1) throw new Error('Only one backward revision loop per diagram');
  }
  const s=newSlide('diagram');
  sectionHead(s,'\u0e20\u0e32\u0e1e\u0e1b\u0e23\u0e30\u0e01\u0e2d\u0e1a\u0e02\u0e2d\u0e1a\u0e40\u0e02\u0e15\u0e07\u0e32\u0e19',
    diagram.title,diagram.subtitle||'\u0e41\u0e2a\u0e14\u0e07\u0e40\u0e09\u0e1e\u0e32\u0e30\u0e04\u0e27\u0e32\u0e21\u0e2a\u0e31\u0e21\u0e1e\u0e31\u0e19\u0e18\u0e4c\u0e17\u0e35\u0e48\u0e22\u0e37\u0e19\u0e22\u0e31\u0e19\u0e41\u0e25\u0e49\u0e27');
  ui.render(s,{type:'Diagram',nodes,edges,diagramType:diagram.type},{x:M,y:2.72,w:INNER,h:2.95});
  ui.render(s,{type:'Notice',label:'\u0e2b\u0e21\u0e32\u0e22\u0e40\u0e2b\u0e15\u0e38',
    body:diagram.note||'\u0e41\u0e1c\u0e19\u0e20\u0e32\u0e1e\u0e2a\u0e23\u0e38\u0e1b\u0e02\u0e2d\u0e1a\u0e40\u0e02\u0e15\u0e07\u0e32\u0e19\u0e17\u0e35\u0e48\u0e22\u0e37\u0e19\u0e22\u0e31\u0e19',tone:'blue'},
    {x:M,y:5.89,w:INNER,h:.79});
});

// แสดงเลขขั้นตามลำดับแผนงานที่ยืนยัน
const phases = Array.isArray(d.phases)&&d.phases.length?d.phases:[{name:'พัฒนาและส่งมอบ',duration:q.lead_time}];
const phasePages=chunk(phases,5);
phasePages.forEach((page,pageIndex)=>{
  const s=newSlide('แผนดำเนินงานและส่งมอบ');
  sectionHead(s,'ขั้นตอนการให้บริการ',pagedLabel('จากเริ่มงานจนถึงใช้งานจริง',pageIndex,phasePages.length),'แต่ละขั้นดำเนินการตามแผนงาน และมีจุดตรวจรับตามเงื่อนไขที่ยืนยันแล้ว');
  ui.render(s,{type:'Stepper',steps:page.map(p=>({name:thaiPhase(p.name),duration:p.duration})),
    startIndex:pageIndex*5+1},{x:M,y:2.54,w:INNER,h:2.97});
  ui.render(s,{type:'Notice',label:'\u0e40\u0e01\u0e13\u0e11\u0e4c\u0e01\u0e32\u0e23\u0e15\u0e23\u0e27\u0e08\u0e23\u0e31\u0e1a',
    body:q.acceptance,tone:'blue',labelWidth:2.47},{x:M,y:5.70,w:INNER,h:.95});
});

// แสดงสัดส่วน ยอด และเงื่อนไขของแต่ละงวดชำระ
const paymentPages=chunk(milestones,3);
paymentPages.forEach((page,pageIndex)=>{
  const s=newSlide('การชำระเงินตามงวดงาน');
  sectionHead(s,'เงื่อนไขการชำระเงิน',pagedLabel('จ่ายตามผลงานที่ตรวจสอบได้',pageIndex,paymentPages.length),'สัดส่วนในแถบด้านบนคือสัดส่วนเงินตามงวด ไม่ใช่เปอร์เซ็นต์ความก้าวหน้างาน');
  ui.render(s,{type:'ProgressSegments',segments:milestones.map(m=>({value:Number(m.percent)}))},
    {x:M,y:2.28,w:INNER,h:.25});
  ui.render(s,{type:'Grid',columns:page.length,gapX:.20,children:page.map((m,i)=>({
    type:'PaymentCard',index:pageIndex*3+i+1,percent:m.percent,
    amount:amount(m.amount),trigger:m.trigger
  }))},{x:M,y:2.82,w:INNER,h:2.57});
  ui.render(s,{type:'TotalBanner',label:'\u0e22\u0e2d\u0e14\u0e23\u0e27\u0e21\u0e17\u0e31\u0e49\u0e07\u0e42\u0e04\u0e23\u0e07\u0e01\u0e32\u0e23',amount:amount(math.total)},
    {x:M,y:5.58,w:INNER,h:.83});
  txt(s,`\u0e01\u0e33\u0e2b\u0e19\u0e14\u0e0a\u0e33\u0e23\u0e30: ${data.commercial?.payment_note||'-'}`,
    M+.05,6.55,INNER-.10,.31,14,{color:C.muted,minSize:13});
});

// หน้าสุดท้ายแสดงบริการหลังการขาย สิทธิ์ในงาน และเงื่อนไขเปลี่ยนงาน
{
  const s=newSlide('การดูแลหลังส่งมอบ');
  sectionHead(s,'บริการหลังการขาย','ส่งมอบแล้ว ดูแลกันอย่างไร','แยกงานรับประกัน งานนอกขอบเขต และงานเพิ่มเติมที่มีค่าใช้จ่ายให้ชัดเจน');
  ui.render(s,{type:'Stack',direction:'row',gap:.24,children:[
    {type:'ServiceCard',title:'\u0e07\u0e32\u0e19\u0e17\u0e35\u0e48\u0e23\u0e31\u0e1a\u0e1b\u0e23\u0e30\u0e01\u0e31\u0e19',description:support.warranty,items:support.included,tone:'green'},
    {type:'ServiceCard',title:'\u0e07\u0e32\u0e19\u0e17\u0e35\u0e48\u0e44\u0e21\u0e48\u0e23\u0e27\u0e21',description:listSentence(support.excluded)||listSentence(sc.not_included),items:[],tone:'red'}
  ]},{x:M,y:2.25,w:INNER,h:2.40});
  ui.render(s,{type:'Notice',label:'\u0e07\u0e32\u0e19\u0e40\u0e1e\u0e34\u0e48\u0e21\u0e40\u0e15\u0e34\u0e21',body:support.change_rate,tone:'blue',labelWidth:2.27},
    {x:M,y:4.86,w:INNER,h:.81});
  ui.render(s,{type:'Notice',label:'\u0e2a\u0e34\u0e17\u0e18\u0e34\u0e41\u0e25\u0e30\u0e01\u0e32\u0e23\u0e2a\u0e48\u0e07\u0e21\u0e2d\u0e1a',body:q.ip_terms,tone:'green',labelWidth:2.71},
    {x:M,y:5.85,w:INNER,h:.82});
}

// ใส่เลขหน้าและส่วนท้ายหลังทราบจำนวนหน้าทั้งหมด
const count=slides.length;
if(count>12) throw new Error(`Slide deck has ${count} pages; simplify scope or review layout instead of shrinking fonts`);
slides.forEach(({slide},i)=>{ui.footer(slide,{index:i+1,total:count,demo:!!data.demo});});

pptx.writeFile({fileName:path.resolve(outPath)}).then(()=>{
  console.log(JSON.stringify({pptx:path.resolve(outPath),pages:count,font:FONT,components:[...ui.used].sort(),modules:modules.length,phases:phases.length,milestones:milestones.length},null,2));
}).catch(e=>{console.error(e);process.exit(1);});
