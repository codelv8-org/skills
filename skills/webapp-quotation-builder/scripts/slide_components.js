#!/usr/bin/env node
/**
 * ประกอบสไลด์ด้วยองค์ประกอบใช้ซ้ำและ design tokens
 * ใช้ PptxGenJS สร้างรูปทรงและข้อความที่แก้ไขได้ใน PowerPoint
 *
 * render(slide, {type:'Grid', columns:3, gapX:.2, children:[
 *   {type:'MetricCard', label:'...', value:'...', tone:'blue'}, ...
 * ]}, {x:.7,y:4.7,w:11.9,h:1.5})
 */
'use strict';
const fs=require('fs');
const helpers=require(process.env.SLIDES_HELPERS || '/home/oai/skills/slides/pptxgenjs_helpers/index.js');
const {autoFontSize,imageSizingContain,warnIfSlideElementsOutOfBounds}=helpers;
const W=40/3, H=7.5;
const tokens=Object.freeze({
  canvas:{w:W,h:H,margin:.68,footerY:6.95},
  space:{xs:.08,sm:.16,md:.24,lg:.32,xl:.48},
  radius:{small:.08,card:.16},
  type:{hero:35,title:29,metric:29,heading:20,body:18,detail:16,label:15,caption:14,footer:10},
  color:{bg:'F7F9FD',white:'FFFFFF',navy:'112D50',navy2:'193F69',ink:'193652',
    muted:'4C637A',line:'DCE5F0',blue:'245CB4',blueLight:'EAF2FD',
    green:'116652',greenLight:'E8F5F0',amber:'80510C',amberLight:'FFF3E0',
    red:'8C3944',redLight:'FFF1F1',purple:'7651A6',teal:'177D8A',
    dim:'B5C9E2',softWhite:'F3F7FC'}
});
function position(r){if(!r||![r.x,r.y,r.w,r.h].every(Number.isFinite)||r.w<=0||r.h<=0)
  throw new Error('Component must receive a valid frame');return r;}
function textValue(v){return String(v??'').trim();}
function rgb(hex){return [0,2,4].map(i=>parseInt(hex.slice(i,i+2),16)/255);}
function luminance(hex){const a=rgb(hex).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4);return .2126*a[0]+.7152*a[1]+.0722*a[2];}
function contrast(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
class SlideUI {
  constructor(pptx, options={}){
    this.pptx=pptx;this.S=pptx.ShapeType;this.font=options.font||'Noto Sans Thai';
    this.logoPath=options.logoPath||'';this.brand=options.brand||'';this.quoteId=options.quoteId||'';
    this.C={...tokens.color,...(options.colors||{})};
    this.used=new Set();this.maxDepth=7;
    const checks=[[this.C.ink,this.C.white],[this.C.muted,this.C.white],[this.C.blue,this.C.blueLight],
      [this.C.green,this.C.greenLight],[this.C.red,this.C.redLight]];
    for(const [fg,bg] of checks){if(contrast(fg,bg)<4.5)throw new Error('Design tokens fail contrast target: '+fg+'/'+bg);}
  }
  get T(){return tokens.type;}
  get canvas(){return tokens.canvas;}
  slide(slide,color){slide.background={color:color||this.C.bg};}
  rect(slide,r,{fill='FFFFFF',stroke=null,round=true,width=.8}={}){
    position(r);slide.addShape(round?this.S.roundRect:this.S.rect,{x:r.x,y:r.y,w:r.w,h:r.h,
      rectRadius:.12,fill:{color:fill},line:stroke?{color:stroke,width}:{color:fill,transparency:100,width:0}});
    return r;
  }
  line(slide,x1,y1,x2,y2,color=this.C.line,width=1.5,arrow=false){
    slide.addShape(this.S.line,{x:x1,y:y1,w:x2-x1,h:y2-y1,
      line:{color,width,beginArrowType:'none',endArrowType:arrow?'triangle':'none'}});
  }
  text(slide,value,r,{size=18,min=null,bold=false,color=this.C.ink,align='left',valign='mid',...other}={}){
    position(r);const s=textValue(value);if(!s)return;
    if(s.includes('\ufffd'))throw new Error('Unicode replacement glyph in slide text');
    const lower=min===null?(size>=26?24:(size>=17?16:(size>=14?13:9))):min;
    const sizes=autoFontSize(s,this.font,{x:r.x,y:r.y,w:r.w,h:r.h,fontSize:size,
      minFontSize:lower,maxFontSize:size,mode:'shrink'});
    const config={...sizes,fontFace:this.font,color,bold,align,valign,margin:0,
      breakLine:false,lineSpacingMultiple:1.15,lang:'th-TH',...other};
    delete config.charSpacing;
    slide.addText(s,config);
  }
  badge(slide,{text,rect,variant='soft',tone='blue',size=14}={}){
    const r=position(rect),colors={blue:[this.C.blue,this.C.blueLight],green:[this.C.green,this.C.greenLight],
      red:[this.C.red,this.C.redLight],amber:[this.C.amber,this.C.amberLight],neutral:[this.C.muted,this.C.softWhite]};
    const [ink,bg]=colors[tone]||colors.blue;
    this.rect(slide,r,{fill:variant==='outline'?this.C.white:bg,stroke:variant==='outline'?ink:null});
    this.text(slide,text,{x:r.x+.09,y:r.y+.01,w:r.w-.18,h:r.h-.02},
      {size,min:Math.min(size,13),color:ink,bold:true,align:'center'});
  }
  logo(slide,r,{onDark=false}={}){
    if(this.logoPath&&fs.existsSync(this.logoPath)){
      if(onDark)this.rect(slide,{x:r.x-.08,y:r.y-.08,w:r.w+.16,h:r.h+.16},{fill:this.C.white});
      slide.addImage({path:this.logoPath,...imageSizingContain(this.logoPath,r.x,r.y,r.w,r.h)});
    }
  }
  grid(rect,columns,count,{gapX=.22,gapY=.20}={}){
    const r=position(rect),rows=Math.ceil(count/columns),cw=(r.w-gapX*(columns-1))/columns,
      rh=(r.h-gapY*(rows-1))/rows;
    if(cw<=0||rh<=0)throw new Error('Grid cannot fit items');
    return Array.from({length:count},(_,i)=>({x:r.x+(i%columns)*(cw+gapX),
      y:r.y+Math.floor(i/columns)*(rh+gapY),w:cw,h:rh}));
  }
  stack(rect,ratios,{direction='row',gap=.2}={}){
    const r=position(rect),total=ratios.reduce((a,b)=>a+b,0);
    const size=(direction==='row'?r.w:r.h)-gap*(ratios.length-1);
    if(total<=0||size<=0)throw new Error('Stack cannot fit items');
    let pos=direction==='row'?r.x:r.y;
    return ratios.map(weight=>{let length=size*weight/total;
      const out=direction==='row'?{x:pos,y:r.y,w:length,h:r.h}:{x:r.x,y:pos,w:r.w,h:length};
      pos+=length+gap;return out;});
  }
  header(slide,{eyebrow,title,subtitle,pageLabel}={}){
    const m=this.canvas.margin;
    this.rect(slide,{x:m,y:.58,w:.075,h:.32},{fill:this.C.blue,round:false});
    this.text(slide,eyebrow,{x:m+.17,y:.56,w:8.5,h:.36},{size:this.T.label,color:this.C.blue,bold:true});
    if(pageLabel)this.badge(slide,{text:pageLabel,rect:{x:10.25,y:.53,w:1.34,h:.39},tone:'neutral'});
    this.logo(slide,{x:11.65,y:.52,w:1.0,h:.46});
    this.text(slide,title,{x:m,y:.99,w:11.93,h:.76},{size:30,min:26,bold:true});
    if(subtitle)this.text(slide,subtitle,{x:m,y:1.73,w:11.92,h:.38},{size:this.T.detail,color:this.C.muted});
  }
  footer(slide,{index,total,demo=false}={}){
    const m=this.canvas.margin;
    this.line(slide,m,6.96,W-m,6.96,this.C.line,.85);
    this.text(slide,this.brand,{x:m,y:7.04,w:6,h:.23},{size:10,min:9,color:this.C.muted});
    this.text(slide,`${this.quoteId}  |  ${index} / ${total}`,{x:10.02,y:7.04,w:2.62,h:.23},
      {size:10,min:9,align:'right',color:this.C.muted});
    if(demo)this.text(slide,'\u0e15\u0e31\u0e27\u0e2d\u0e22\u0e48\u0e32\u0e07\u0e40\u0e17\u0e48\u0e32\u0e19\u0e31\u0e49\u0e19',{x:8.25,y:7.04,w:1.47,h:.23},
      {size:10,min:9,align:'right',color:this.C.red});
    warnIfSlideElementsOutOfBounds(slide,this.pptx);
  }
  render(slide,node,rect,depth=0){
    if(depth>this.maxDepth)throw new Error('Component tree depth exceeded');
    const r=position(rect);
    if(!node||!node.type)throw new Error('Component type missing');
    if(node.type==='Grid'){
      this.used.add(node.type);
      const children=node.children||[];const frames=this.grid(r,node.columns||3,children.length,{gapX:node.gapX??.2,gapY:node.gapY??.2});
      children.forEach((child,i)=>this.render(slide,child,frames[i],depth+1));return;
    }
    if(node.type==='Stack'){
      this.used.add(node.type);
      const children=node.children||[];const frames=this.stack(r,node.ratios||children.map(()=>1),
        {direction:node.direction||'row',gap:node.gap??.2});
      children.forEach((child,i)=>this.render(slide,child,frames[i],depth+1));return;
    }
    const map={HeroPanel:'heroPanel',TotalBanner:'totalBanner',MetricCard:'metricCard',FeatureCard:'featureCard',TextCard:'textCard',
      PaymentCard:'paymentCard',ServiceCard:'serviceCard',Notice:'notice',
      ProgressSegments:'progressSegments',Stepper:'stepper',Diagram:'diagram'};
    if(!(node.type in map))throw new Error('Unregistered component: '+node.type);
    this.used.add(node.type);
    this[map[node.type]](slide,{...node,rect:r});
  }
  heroPanel(slide,{rect:r,eyebrow,title,description,steps=[]}){
    this.rect(slide,r,{fill:this.C.navy,round:false});
    this.rect(slide,{x:r.x+.68,y:r.y+.63,w:.08,h:.34},{fill:'64B5E9',round:false});
    this.text(slide,eyebrow,{x:r.x+.88,y:r.y+.62,w:7.30,h:.37},
      {size:14,min:13,color:'C6E0FF',bold:true});
    this.logo(slide,{x:r.x+r.w-1.9,y:r.y+.59,w:1.15,h:.50},{onDark:true});
    this.text(slide,title,{x:r.x+.68,y:r.y+1.18,w:7.6,h:1.15},
      {size:35,min:29,color:this.C.white,bold:true});
    this.text(slide,description,{x:r.x+.68,y:r.y+2.55,w:7.60,h:.90},
      {size:18,min:17,color:'E5EEF9'});
    const px=r.x+r.w-4.63,py=r.y+1.30,pw=3.91,ph=2.63;
    this.rect(slide,{x:px,y:py,w:pw,h:ph},{fill:this.C.navy2});
    this.text(slide,'\u0e41\u0e19\u0e27\u0e17\u0e32\u0e07\u0e43\u0e2b\u0e49\u0e1a\u0e23\u0e34\u0e01\u0e32\u0e23',
      {x:px+.29,y:py+.26,w:3.24,h:.35},{size:14,min:13,color:'CAE4FF',bold:true});
    if(steps.length>3)throw new Error('HeroPanel supports 3 or fewer steps');
    steps.forEach((step,i)=>{
      const cy=py+.81+i*.55;
      if(i<steps.length-1)this.line(slide,px+.60,cy+.17,px+.60,cy+.55,'7EA8D5',1.8);
      slide.addShape(this.S.ellipse,{x:px+.42,y:cy,w:.36,h:.36,
        fill:{color:'E4F2FE'},line:{color:'E4F2FE',transparency:100}});
      this.text(slide,String(i+1),{x:px+.42,y:cy,w:.36,h:.36},
        {size:15,min:14,color:this.C.navy,bold:true,align:'center'});
      this.text(slide,step,{x:px+.93,y:cy-.03,w:2.65,h:.44},
        {size:16,min:15,color:this.C.white,bold:true});
    });
  }
  totalBanner(slide,{rect:r,label,amount}){
    this.rect(slide,r,{fill:this.C.navy,stroke:this.C.navy});
    this.text(slide,label,{x:r.x+.26,y:r.y+.17,w:4.7,h:r.h-.32},
      {size:18,min:17,color:'E7F1FF',bold:true});
    this.text(slide,amount,{x:r.x+r.w-5.62,y:r.y+.11,w:5.32,h:r.h-.20},
      {size:26,min:20,color:this.C.white,bold:true,align:'right'});
  }
  metricCard(slide,{rect:r,label,value,tone='blue',support=''}){
    const tones={blue:[this.C.blue,this.C.blueLight],green:[this.C.green,this.C.greenLight],
      amber:[this.C.amber,this.C.amberLight]};const [accent,bg]=tones[tone]||tones.blue;
    this.rect(slide,r,{fill:this.C.white,stroke:this.C.line});
    this.rect(slide,{x:r.x+.20,y:r.y+.20,w:.08,h:r.h-.40},{fill:accent,round:false});
    this.text(slide,label,{x:r.x+.40,y:r.y+.20,w:r.w-.66,h:.34},{size:this.T.label,color:accent,bold:true});
    this.text(slide,value,{x:r.x+.40,y:r.y+.61,w:r.w-.62,h:.54},{size:this.T.metric,min:18,color:this.C.navy,bold:true});
    if(support)this.text(slide,support,{x:r.x+.40,y:r.y+r.h-.35,w:r.w-.64,h:.25},{size:13,min:12,color:this.C.muted});
  }
  featureCard(slide,{rect:r,label,index,tag='IN SCOPE'}){
    this.rect(slide,r,{fill:this.C.white,stroke:this.C.line});
    this.badge(slide,{text:String(index).padStart(2,'0'),rect:{x:r.x+.21,y:r.y+.28,w:.52,h:.46},tone:'blue',size:15});
    this.text(slide,label,{x:r.x+.85,y:r.y+.19,w:r.w-1.11,h:r.h-.40},
      {size:19,min:16,bold:true});
    // เว้นขอบล่างของการ์ดให้ข้อความอ่านง่าย
    this.rect(slide,{x:r.x+.20,y:r.y+r.h-.12,w:r.w-.40,h:.025},{fill:this.C.blueLight,round:false});
  }
  textCard(slide,{rect:r,title,body,tone='blue',emphasis=false}){
    const tones={blue:[this.C.blue,this.C.blueLight],green:[this.C.green,this.C.greenLight],
      red:[this.C.red,this.C.redLight],amber:[this.C.amber,this.C.amberLight]};
    const [ink,bg]=tones[tone]||tones.blue;
    this.rect(slide,r,{fill:emphasis?bg:this.C.white,stroke:emphasis?bg:this.C.line});
    this.text(slide,title,{x:r.x+.21,y:r.y+.17,w:r.w-.42,h:.36},
      {size:18,bold:true,color:ink});
    this.text(slide,body,{x:r.x+.21,y:r.y+.60,w:r.w-.43,h:r.h-.78},
      {size:16,min:14,color:this.C.ink});
  }
  notice(slide,{rect:r,label,body,tone='blue',labelWidth=2.15}){
    const colors={blue:[this.C.blue,this.C.blueLight],green:[this.C.green,this.C.greenLight],
      red:[this.C.red,this.C.redLight],amber:[this.C.amber,this.C.amberLight]};
    const [ink,bg]=colors[tone]||colors.blue;
    this.rect(slide,r,{fill:bg,stroke:bg});
    this.rect(slide,{x:r.x,y:r.y,w:.075,h:r.h},{fill:ink,round:false});
    this.text(slide,label,{x:r.x+.22,y:r.y+.16,w:labelWidth-.20,h:r.h-.28},
      {size:17,min:15,bold:true,color:ink});
    this.text(slide,body,{x:r.x+labelWidth+.12,y:r.y+.11,w:r.w-labelWidth-.34,h:r.h-.22},
      {size:16,min:15,color:this.C.ink});
  }
  progressSegments(slide,{rect:r,segments=[],palette=[]}){
    if(!segments.length)return;
    const total=segments.reduce((a,s)=>a+Number(s.value||0),0);
    if(!(total>0))throw new Error('Invalid percent progress segments');
    const colors=palette.length?palette:[this.C.blue,this.C.green,this.C.purple,this.C.amber,this.C.teal,this.C.navy];
    let x=r.x;
    segments.forEach((seg,i)=>{const w=r.w*Number(seg.value||0)/total;
      if(w<=0)return;this.rect(slide,{x,y:r.y,w,h:r.h},{fill:colors[i%colors.length],round:false});x+=w;});
  }
  paymentCard(slide,{rect:r,index,percent,amount,trigger}){
    this.rect(slide,r,{fill:this.C.white,stroke:this.C.line});
    this.badge(slide,{text:`\u0e07\u0e27\u0e14\u0e17\u0e35\u0e48 ${index}`,
      rect:{x:r.x+.20,y:r.y+.19,w:1.13,h:.41},tone:'blue',size:14});
    this.text(slide,`${percent}%`,{x:r.x+.23,y:r.y+.72,w:r.w-.46,h:.65},
      {size:34,min:26,color:this.C.navy,bold:true});
    this.text(slide,amount,{x:r.x+.23,y:r.y+1.43,w:r.w-.46,h:.60},
      {size:22,min:20,color:this.C.blue,bold:true});
    this.text(slide,trigger,{x:r.x+.23,y:r.y+2.05,w:r.w-.46,h:r.h-2.25},
      {size:16,min:15,color:this.C.muted});
  }
  stepper(slide,{rect:r,steps=[],startIndex=1}){
    const n=steps.length;if(!n||n>5)throw new Error('Stepper accepts 1..5 items');
    const frames=this.grid(r,n,n,{gapX:.16});
    const cy=r.y+.34;
    if(n>1)this.line(slide,frames[0].x+frames[0].w/2,cy,frames[n-1].x+frames[n-1].w/2,cy,this.C.dim,2.2);
    frames.forEach((f,i)=>{
      this.rect(slide,{x:f.x,y:f.y+.73,w:f.w,h:f.h-.73},{fill:this.C.white,stroke:this.C.line});
      const dot={x:f.x+(f.w-.58)/2,y:f.y+.05,w:.58,h:.58};
      slide.addShape(this.S.ellipse,{...dot,fill:{color:this.C.blueLight},line:{color:this.C.blue,width:1.5}});
      this.text(slide,String(startIndex+i),{...dot,y:dot.y+.015,h:.54},{size:19,bold:true,color:this.C.blue,align:'center'});
      this.text(slide,steps[i].name,{x:f.x+.17,y:f.y+.97,w:f.w-.34,h:.68},
        {size:19,min:16,bold:true,align:'center'});
      this.badge(slide,{text:steps[i].duration||'-',
        rect:{x:f.x+.17,y:f.y+f.h-.76,w:f.w-.34,h:.43},tone:'blue',size:14});
    });
  }
  serviceCard(slide,{rect:r,title,description,items=[],tone='green'}){
    const [ink,bg]=tone==='red'?[this.C.red,this.C.redLight]:[this.C.green,this.C.greenLight];
    this.rect(slide,r,{fill:bg,stroke:bg});
    this.badge(slide,{text:title,rect:{x:r.x+.24,y:r.y+.19,w:2.13,h:.44},tone, size:15});
    this.text(slide,description,{x:r.x+.23,y:r.y+.76,w:r.w-.48,h:.82},
      {size:18,min:16,bold:true,color:this.C.ink});
    if(items.length)this.text(slide,items.join('  |  '),{x:r.x+.23,y:r.y+1.67,w:r.w-.48,h:r.h-1.85},
      {size:15,min:14,color:this.C.muted});
  }
  diagram(slide,{rect:r,nodes=[],edges=[],diagramType='flow'}){
    if(nodes.length<2||nodes.length>5)throw new Error('Diagram accepts 2..5 nodes');
    const ids=nodes.map(n=>n.id);if(new Set(ids).size!==nodes.length)throw new Error('Duplicate diagram id');
    const byId=new Map(nodes.map((n,i)=>[n.id,i]));let back=0;
    for(const edge of edges){
      if(!byId.has(edge.from)||!byId.has(edge.to))throw new Error('Diagram has unknown endpoints');
      const delta=byId.get(edge.to)-byId.get(edge.from);
      if(delta===-1){back++;if(diagramType!=='flow'||nodes[byId.get(edge.from)].kind!=='decision')throw new Error('Revision edge must return from a decision to prior node');}
      else if(delta!==1)throw new Error('Complex relationships require a different diagram renderer');
      if(back>1)throw new Error('Only one revision loop per diagram');
    }
    const gap=.32,fw=(r.w-gap*(nodes.length-1))/nodes.length,fy=r.y+.20,fh=1.52;
    const centers=nodes.map((_,i)=>r.x+i*(fw+gap)+fw/2);
    edges.forEach(edge=>{
      const i=byId.get(edge.from),j=byId.get(edge.to),ax=r.x+i*(fw+gap),bx=r.x+j*(fw+gap);
      if(j===i+1){
        this.line(slide,ax+fw+.02,fy+fh/2,bx-.05,fy+fh/2,this.C.blue,1.8,true);
        if(edge.label)this.text(slide,edge.label,{x:ax+fw-.02,y:fy-.45,w:gap+.05,h:.31},
          {size:13,min:12,color:this.C.blue,align:'center'});
      }else{
        const loop=fy+fh+1.0;
        this.line(slide,centers[i],fy+fh,centers[i],loop,this.C.amber,1.8);
        this.line(slide,centers[i],loop,centers[j],loop,this.C.amber,1.8);
        this.line(slide,centers[j],loop,centers[j],fy+fh+.17,this.C.amber,1.8);
        slide.addShape(this.S.triangle,{x:centers[j]-.10,y:fy+fh+.09,w:.20,h:.17,
          fill:{color:this.C.amber},line:{color:this.C.amber,width:.2}});
        this.text(slide,edge.label||'',{x:Math.min(centers[i],centers[j])+.10,y:loop+.13,
          w:Math.abs(centers[i]-centers[j])-.20,h:.34},
          {size:13,min:12,color:this.C.amber,align:'center'});
      }
    });
    nodes.forEach((node,i)=>{
      const x=r.x+i*(fw+gap),decision=node.kind==='decision',data=node.kind==='data';
      const fill=decision?this.C.amberLight:(data?this.C.greenLight:this.C.white);
      const border=decision?this.C.amber:(data?this.C.green:this.C.line);
      if(decision)slide.addShape(this.S.diamond,{x:x+.12,y:fy+.04,w:fw-.24,h:fh-.09,
        fill:{color:fill},line:{color:border,width:1.2}});
      else this.rect(slide,{x,y:fy,w:fw,h:fh},{fill,stroke:border});
      this.text(slide,node.label,{x:x+(decision?.43:.18),y:fy+.34,w:fw-(decision?.86:.36),h:.75},
        {size:18,min:15,bold:true,align:'center'});
      if(node.caption)this.text(slide,node.caption,{x:x+.08,y:fy+fh+.24,w:fw-.16,h:.40},
        {size:14,min:13,color:this.C.muted,align:'center'});
    });
  }
}
module.exports={SlideUI,tokens,contrast};
