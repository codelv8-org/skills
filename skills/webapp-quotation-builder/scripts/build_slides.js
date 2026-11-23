#!/usr/bin/env node
/** Customer-facing 16:9 infographic deck, output as PPTX for PDF conversion.
 *  Usage: node build_slides.js <confirmed-input.json> <math.json> <out.pptx>
 *  Requires pptxgenjs and the Slides skill helpers; does not use external images.
 */
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
let helpers;
try {
  const helperPath = process.env.SLIDES_HELPERS || '/home/oai/skills/slides/pptxgenjs_helpers/index.js';
  helpers = require(helperPath);
} catch (error) {
  throw new Error('Slide helper package not accessible. Activate the slides skill or set SLIDES_HELPERS to its index.js: ' + error.message);
}
const { autoFontSize, imageSizingContain, warnIfSlideElementsOutOfBounds } = helpers;

const [inputPath, mathPath, outPath] = process.argv.slice(2);
if (!(inputPath && mathPath && outPath)) throw new Error('Usage: node build_slides.js <input> <math> <out.pptx>');
const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const math = JSON.parse(fs.readFileSync(mathPath, 'utf8'));
const q = data.quotation;
const provider = data.provider;
const scope = data.scope;
const delivery = data.delivery;
const support = data.after_sales;
const milestones = math.milestones;
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = provider.name;
pptx.subject = 'Service overview / quotation ' + q.number;
pptx.title = 'ภาพรวมข้อเสนอโครงการ ' + q.project_name;
pptx.company = provider.name;
pptx.lang = 'th-TH';
pptx.theme = {
  headFontFace: 'Noto Sans Thai', bodyFontFace: 'Noto Sans Thai', lang: 'th-TH',
};
pptx.defineSlideMaster({title:'LIGHT', background:{color:'F7F9FD'},objects:[]});
const W=13.3333333, H=7.5, FONT='Noto Sans Thai';
const C={ navy:'102A4C', blue:'2664BF', blue2:'1E59B5', muted:'5F718D', cyan:'DDEDFC', bg:'F7F9FD', white:'FFFFFF', border:'DEE7F4', aqua:'D7F6F0', light:'EFF5FF', gold:'FFF0CE', orange:'9B5600', good:'1D7A65' };
function shape(slide, type, x,y,w,h, opts={}) {
  slide.addShape(type,{x,y,w,h,line:{color:opts.stroke||opts.fill||C.border,transparency:opts.stroke?0:100,width:opts.stroke?0.8:0},fill:{color:opts.fill||C.white},radius:opts.radius||0,...(opts.extra||{})});
}
function text(slide, value, x,y,w,h,size=15,opts={}) {
  const val=String(value??'');
  slide.addText(val,{
    ...autoFontSize(val,FONT,{x,y,w,h,fontSize:size,minFontSize:Math.max(7,size-3),maxFontSize:size,mode:'shrink'}),
    fontFace:FONT,color:opts.color||C.navy,bold:!!opts.bold,margin:0,breakLine:false,
    valign:opts.valign||'mid',align:opts.align||'left',
    lineSpacingMultiple:1.05,
    ...opts,
  });
}
function card(slide,x,y,w,h,fill=C.white,stroke=C.border){ shape(slide,pptx.ShapeType.roundRect,x,y,w,h,{fill,stroke}); }
function placeLogo(slide, x=11.45, y=0.40, w=1.18, h=0.55) {
  if (provider.logo_path && fs.existsSync(provider.logo_path)) {
    slide.addImage({path:provider.logo_path,...imageSizingContain(provider.logo_path,x,y,w,h)});
  }
}
function money(value){ return Number(value).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})+' ฿'; }
function header(slide,num,kicker,titleText,subtitle){
  shape(slide,pptx.ShapeType.rect,0,0,W,H,{fill:C.bg});
  shape(slide,pptx.ShapeType.rect,0.65,0.65,0.07,0.27,{fill:C.blue});
  placeLogo(slide);
  text(slide,kicker.toUpperCase(),0.86,0.53,9.9,0.25,10,{color:C.blue,bold:true,charSpacing:0.7});
  text(slide,titleText,0.67,1.05,11.95,0.56,27,{bold:true});
  if(subtitle) text(slide,subtitle,0.68,1.66,11.95,0.39,13,{color:C.muted});
  text(slide,provider.name,0.69,7.08,8.6,0.22,10,{color:C.muted});
  text(slide,`${q.number}    •    ${num} / 5`,10.0,7.08,2.63,0.22,10,{color:C.muted,align:'right'});
  if(data.demo){
    text(slide,'DEMO / ข้อมูลสมมติ ไม่ใช่ใบเสนอราคาจริง',5.3,7.08,4.4,0.22,9,{color:'B45B3F',align:'center'});
  }
}
function addArrow(slide,x1,y,x2){
  slide.addShape(pptx.ShapeType.chevron,{x:x1,y:y-0.11,w:Math.max(0.14,x2-x1),h:0.22,line:{color:C.blue,transparency:100},fill:{color:C.blue}});
}
// 01 — ภาพรวม
{
  const s=pptx.addSlide();
  shape(s,pptx.ShapeType.rect,0,0,W,H,{fill:C.bg});
  shape(s,pptx.ShapeType.rect,0,0,W,3.56,{fill:C.navy});
  shape(s,pptx.ShapeType.rect,0.68,0.6,0.08,0.35,{fill:'5DB3FB'});
  placeLogo(s);
  text(s,'PROPOSAL OVERVIEW  /  '+q.number,0.89,0.58,10.6,0.35,11,{color:'A4CDFB',bold:true});
  text(s,q.project_name,0.7,1.11,11.9,0.79,31,{color:C.white,bold:true});
  text(s,q.summary,0.73,2.05,11.45,0.72,17,{color:'D5E7FB'});
  const y=4.00, h=1.45, gap=0.23, w=(W-1.36-gap*2)/3;
  const tiles=[
    {label:'งบประมาณโครงการ',value:money(math.total),light:C.light},
    {label:'ระยะเวลาดำเนินการ',value:q.lead_time,light:C.aqua},
    {label:'งวดการชำระเงิน',value:String(milestones.length)+' งวดตามผลงาน',light:C.gold},
  ];
  tiles.forEach((tile,i)=>{const x=0.68+i*(w+gap); card(s,x,y,w,h,tile.light,tile.light); text(s,tile.label,x+0.18,y+0.19,w-0.36,0.27,12,{color:C.muted,bold:true}); text(s,tile.value,x+0.18,y+0.58,w-0.36,0.53,i===0?24:18,{bold:true});});
  text(s,'เป้าหมาย: ส่งมอบระบบที่ใช้งานได้จริง พร้อมตรวจรับตามขอบเขตและเงื่อนไขที่ตกลง',0.72,5.78,11.9,0.49,15,{color:C.muted});
  text(s,provider.name,0.72,7.07,9.8,0.22,10,{color:C.muted});
  text(s,'1 / 5',11.98,7.07,0.64,0.22,10,{color:C.muted,align:'right'});
  if(data.demo) text(s,'ข้อมูลสมมติ — ตัวอย่างเท่านั้น',7.5,7.07,4.0,0.22,9,{color:'B45B3F'});
}
// 02 — ขอบเขตงาน
{
  const s=pptx.addSlide('LIGHT');
  header(s,2,'Included scope','ลูกค้าจะได้รับอะไรบ้าง','ขอบเขตการทำงานหลักที่รวมอยู่ในราคาที่เสนอ');
  const modules=scope.modules;
  const gap=0.21, gridW=(12.0-gap*2)/3, cardH=1.24;
  modules.forEach((m,i)=>{const row=Math.floor(i/3),col=i%3,x=0.67+col*(gridW+gap),y=2.33+row*1.43;
    card(s,x,y,gridW,cardH,C.white,C.border);
    card(s,x+0.16,y+0.18,0.48,0.47,C.light,C.light);
    text(s,String(i+1).padStart(2,'0'),x+0.2,y+0.27,0.42,0.21,10,{color:C.blue,bold:true});
    text(s,m,x+0.79,y+0.18,gridW-0.96,0.84,17,{bold:true});
  });
  const by=5.38;
  card(s,0.67,by,5.88,1.12,'E5F7F1','E5F7F1');
  card(s,6.78,by,5.88,1.12,'FFF1EF','FFF1EF');
  text(s,'✓ งานที่รวมในราคา',0.89,by+0.13,5.42,0.28,13,{color:C.good,bold:true});
  text(s,(delivery.handover||[]).join(' • '),0.89,by+0.45,5.42,0.49,12,{color:C.navy});
  text(s,'— งานที่ไม่รวม / คิดเพิ่ม',7.00,by+0.13,5.42,0.28,13,{color:'A2453C',bold:true});
  text(s,(scope.not_included||[]).join(' • ')||'ไม่มีรายการยกเว้น',7.00,by+0.45,5.42,0.49,12,{color:C.navy});
}
// 03 — กระบวนการส่งมอบ
{
  const s=pptx.addSlide('LIGHT');
  header(s,3,'Delivery roadmap','ขั้นตอนพัฒนาและส่งมอบ','มีจุดตรวจสอบงานแต่ละช่วง เพื่อให้ผู้ว่าจ้างเห็นความคืบหน้าได้ชัดเจน');
  const phases=delivery.phases;
  const gap=0.18,w=(12.0-(phases.length-1)*gap)/phases.length,y=2.56;
  phases.forEach((phase,i)=>{
    const x=0.68+i*(w+gap);
    card(s,x,y,w,2.54,C.white,C.border);
    shape(s,pptx.ShapeType.rect,x,y,w,0.09,{fill:i===phases.length-1?C.good:C.blue});
    text(s,'STEP '+String(i+1).padStart(2,'0'),x+0.16,y+0.36,w-0.28,0.29,12,{color:C.blue,bold:true});
    text(s,phase.name,x+0.16,y+0.87,w-0.29,0.68,19,{bold:true});
    card(s,x+0.15,y+1.82,w-0.30,0.42,C.light,C.light);
    text(s,phase.duration,x+0.25,y+1.9,w-0.5,0.23,12,{color:C.blue,bold:true,align:'center'});
  });
  card(s,0.68,5.49,11.98,0.99,C.light,C.light);
  text(s,'เกณฑ์รับมอบ',0.95,5.66,1.66,0.27,14,{color:C.blue,bold:true});
  text(s,q.acceptance,2.52,5.57,9.80,0.64,13,{color:C.navy});
}
// 04 — งวดชำระและงานส่งมอบ
{
  const s=pptx.addSlide('LIGHT');
  header(s,4,'Milestone payments','จ่ายตามผลงานที่ตรวจสอบได้','ยอดแต่ละงวดคิดจากราคารวมตามใบเสนอราคา โดยไม่ใช่ส่วนลดจากภาษีหัก ณ ที่จ่าย');
  const gap=0.20, width=(11.99-(milestones.length-1)*gap)/milestones.length, y=2.33;
  milestones.forEach((m,i)=>{
    const x=0.67+i*(width+gap);
    card(s,x,y,width,2.63,i%2===0?C.white:C.light,C.border);
    text(s,'งวด '+(i+1),x+0.18,y+0.23,width-0.34,0.31,13,{color:C.blue,bold:true});
    text(s,m.percent+'%',x+0.17,y+0.68,width-0.33,0.55,28,{bold:true});
    text(s,money(m.amount),x+0.17,y+1.34,width-0.33,0.36,16,{color:C.blue,bold:true});
    text(s,m.trigger,x+0.18,y+1.85,width-0.35,0.57,12,{color:C.muted});
  });
  card(s,0.67,5.27,11.99,1.13,C.navy,C.navy);
  text(s,'ยอดรวมทั้งโครงการ',0.98,5.55,4.3,0.29,14,{color:'DAEAFC'});
  text(s,money(math.total),7.14,5.42,5.00,0.49,26,{color:C.white,bold:true,align:'right'});
  text(s,'กำหนดชำระ: '+(data.commercial?.payment_note||'ตามแต่ละงวดที่ตกลง'),0.87,6.52,11.6,0.27,11,{color:C.muted});
}
// 05 — ประกัน การขอแก้ไข และส่งต่องาน
{
  const s=pptx.addSlide('LIGHT');
  header(s,5,'Support & ownership','หลังส่งมอบ ดูแลกันอย่างไร','แยกการรับประกันแก้บั๊กออกจากงานใหม่และค่าใช้จ่ายภายนอกอย่างโปร่งใส');
  const blocks=[
    {title:'01  รับประกัน',desc:support.warranty,extra:(support.included||[]).join(' • '),fill:'E5F7F1',titleColor:C.good},
    {title:'02  ขอบเขตที่ไม่รวม',desc:(support.excluded||[]).join(' • ') || (scope.not_included||[]).join(' • '),extra:'รายการเพิ่มเติมอาจต้องทำใบเสนอราคาใหม่',fill:'FFF1EF',titleColor:'A2453C'},
    {title:'03  งานเพิ่มเติม',desc:support.change_rate,extra:q.revision_policy,fill:C.light,titleColor:C.blue},
  ];
  const w=3.86,g=0.21;
  blocks.forEach((b,i)=>{const x=0.68+i*(w+g);
    card(s,x,2.30,w,2.70,b.fill,b.fill);
    text(s,b.title,x+0.22,2.54,w-0.45,0.37,15,{color:b.titleColor,bold:true});
    text(s,b.desc,x+0.22,3.08,w-0.44,0.82,15,{bold:true});
    text(s,b.extra,x+0.22,4.13,w-0.44,0.58,11,{color:C.muted});
  });
  card(s,0.68,5.37,11.98,1.24,C.white,C.border);
  text(s,'การส่งมอบ Source Code / สิทธิการใช้งาน',0.93,5.51,6.4,0.3,13,{color:C.blue,bold:true});
  text(s,q.ip_terms,0.93,5.91,11.38,0.46,14,{color:C.navy});
}
// แจ้งเตือนเมื่อองค์ประกอบเกินขอบสไลด์ พื้นหลังและเนื้อหาบนการ์ดซ้อนกันตามแบบ
// ให้เปิดภาพเรนเดอร์ของ PDF เพื่อตรวจผลสุดท้าย
try {
  for (let i=0; i<pptx._slides.length; i++) {
    warnIfSlideElementsOutOfBounds(pptx._slides[i], pptx);
  }
} catch (error) {
  process.stderr.write('Geometry warning helper: '+error.message+'\n');
}
pptx.writeFile({fileName:path.resolve(outPath)}).then(()=>{
  process.stdout.write(path.resolve(outPath)+'\n');
}).catch(err=>{ console.error(err); process.exit(1); });
