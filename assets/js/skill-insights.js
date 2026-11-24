/* Skill comparison and evidence-based quality analytics. */
(function insightsBrowser(){
  'use strict';
  let state=null, catalog=[];
  const repo='https://github.com/codelv8-org/skills';
  const dims={quality:'คุณภาพผลลัพธ์',accuracy:'ความถูกต้อง',ease:'ความง่ายในการใช้งาน',efficiency:'ประสิทธิภาพ',consistency:'ความสม่ำเสมอ'};
  const agents={codex:'Codex','claude-code':'Claude Code',antigravity:'Antigravity',other:'Other'};
  const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
  const fmt=n=>Number.isFinite(n)?n.toFixed(1):'—';
  const get=(s)=>state?.skills?.[s.id]?.versions?.[s.version];
  const bench=(s)=>state?.benchmarks?.[s.id];
  function table(headers,rows){
    const wrapper=el('div','si-table-wrap'),t=el('table','si-table'),thead=el('thead'),hr=el('tr'),tbody=el('tbody');
    for(const h of headers){const cell=el('th','',h);cell.scope='col';hr.append(cell);}thead.append(hr);
    for(const row of rows){const tr=el('tr');row.forEach((v,i)=>{const cell=el(i===0?'th':'td','',v);if(i===0)cell.scope='row';tr.append(cell);});tbody.append(tr);}
    t.append(thead,tbody);wrapper.append(t);return wrapper;
  }
  function renderDashboard(root){
    const h=el('h3','si-title','Skill Intelligence · เปรียบเทียบและวิเคราะห์');
    const subtitle=el('p','sr-muted','คะแนนชุมชนและผลตรวจโครงสร้าง Repository แยกจากกัน · ไม่ใช่ผลทดสอบคุณภาพงานที่ Agent สร้าง');
    const panels=el('div','si-dashboard-grid');
    const comparison=el('section','si-dashboard-card'),analytics=el('section','si-dashboard-card');
    comparison.append(el('h4','','Skill Comparison'));
    const ctr=el('div','sr-filter'),sels=[];
    for(let i=0;i<3;i++){
      const label=el('label','sr-select-label','Skill '+(i+1)+(i===2?' (ไม่บังคับ)':'')),s=el('select');
      if(i===2){const opt=el('option','','ไม่เลือก');opt.value='';s.append(opt);}
      for(const c of catalog){const opt=el('option','',(c.nameTh||c.name)+' · v'+c.version);opt.value=c.id;s.append(opt);}
      s.value=i<2?(catalog[i]?.id||''):'';s.addEventListener('change',draw);label.append(s);ctr.append(label);sels.push(s);
    }
    const result=el('div','si-result');comparison.append(ctr,result);
    function draw(){
      const ids=sels.map(s=>s.value).filter(Boolean),unique=[...new Set(ids)],selected=unique.map(id=>catalog.find(s=>s.id===id)).filter(Boolean);
      result.replaceChildren();
      if(selected.length<2||ids.length!==unique.length){result.append(el('p','sr-muted','เลือก Skill ที่ไม่ซ้ำกันอย่างน้อย 2 รายการ'));return;}
      const row=(label,fn)=>[label,...selected.map(fn)];
      const rows=[row('Version',s=>s.version),row('หมวดหมู่',s=>s.category),row('Community rating',s=>fmt(get(s)?.average)+' / 5'),row('จำนวนรีวิว',s=>state?(get(s)?.count||0):'—'),...Object.entries(dims).map(([key,label])=>row(label,s=>fmt(get(s)?.dimensions?.[key]))),row('Helpful votes',s=>state?(get(s)?.helpful||0):'—'),row('Static benchmark',s=>bench(s)?bench(s).passed+'/'+bench(s).total+' checks':'—'),row('Tool regression',s=>bench(s)?.toolTests?.status||'not_run'),row('AI Agent',s=>(s.supportedAgents||[]).map(a=>agents[a]||a).join(', '))];
      result.append(table(['Metric',...selected.map(s=>s.name)],rows));
    }
    analytics.append(el('h4','','Quality Analytics'));
    if(!state){analytics.append(el('p','sr-muted','ข้อมูล Analytics ยังไม่พร้อม · เปรียบเทียบ metadata ได้ แต่ไม่แสดงคะแนนสมมุติ'));}
    else{
      const all=catalog.map(s=>({s,m:get(s),b:bench(s)})),rated=all.filter(x=>x.m?.count),total=all.reduce((a,x)=>a+(x.m?.count||0),0);
      const stats=el('div','si-kpis');
      for(const [label,value] of [['Skills with reviews',rated.length+'/'+catalog.length],['Current-version reviews',total],['Helpful votes',all.reduce((a,x)=>a+(x.m?.helpful||0),0)],['Static checks fully passed',all.filter(x=>x.b&&x.b.passed===x.b.total).length+'/'+catalog.length]]){
        const card=el('div','si-kpi');card.append(el('strong','',value),el('span','sr-muted',label));stats.append(card);
      }
      analytics.append(stats,table(['Skill','คะแนน','รีวิว','Benchmark'],all.sort((a,b)=>(b.m?.average??-1)-(a.m?.average??-1)||(b.m?.count||0)-(a.m?.count||0)).map(({s,m,b})=>[s.name,fmt(m?.average),m?.count||0,b?b.passed+'/'+b.total:'—'])),el('p','sr-muted','อัปเดต '+(state.generatedAt||'ยังไม่เผยแพร่')+' · คะแนนเฉพาะเวอร์ชันปัจจุบัน'));
    }
    panels.append(comparison,analytics);const details=el('details','si-disclosure');const summary=el('summary');summary.append(h);details.append(summary,subtitle,panels);root.replaceChildren(details);draw();
  }
  async function init(skills,root){
    catalog=skills;
    if(location.protocol.startsWith('http'))try{
      const [response,rr]=await Promise.all([fetch('data/skill-insights.json',{cache:'no-cache'}),fetch('data/reviews.json',{cache:'no-cache'})]);
      if(!response.ok||!rr.ok)throw Error('Unavailable');
      const j=await response.json(),r=await rr.json();if(j.schemaVersion!==1||!j.generatedAt||j.generatedAt!==r.generatedAt||!j.skills||!j.benchmarks)throw Error('Snapshot mismatch');state=j;
    }catch{state=null;}
    if(root)renderDashboard(root);
  }
  function render(skill,root){
    if(!root)return;
    const heading=el('h4','modal-bento-title','Skill Quality · Benchmark & Review Insights');heading.id='siHeading';
    root.replaceChildren(heading);
    const s=state?.skills?.[skill.id],b=bench(skill);
    if(!s||!b){root.append(el('p','sr-muted','ข้อมูล Benchmark และ Analytics ยังไม่พร้อม'));return;}
    const summary=el('section','si-block');summary.append(el('h5','','Review Summary · เวอร์ชันปัจจุบัน v'+skill.version));
    const x=s.summary;
    if(x.mode==='ai'&&x.status==='ready'){
      summary.append(el('p','sr-muted','AI-generated · '+x.model+' · จาก '+x.sampledComments+' ความคิดเห็นที่อนุมัติแล้ว'));
      for(const item of x.points){const p=el('p','si-point',item.text+' ');for(const issue of item.issues){const a=el('a','','#'+issue+' ');a.href=repo+'/issues/'+Number(issue);a.target='_blank';a.rel='noopener noreferrer';p.append(a);}summary.append(p);}
    }else{
      const reason={insufficient_reviews:'ต้องมีความคิดเห็นที่อนุมัติแล้วอย่างน้อย 3 รายการ',not_configured:'ยังไม่ได้ตั้งค่า AI API',api_unavailable:'AI API ไม่พร้อมใช้งาน',budget_limit:'ถึงขีดจำกัดการประมวลผล',pending:'ยังไม่ได้สร้างสรุป AI'}[x.status]||'ไม่มีข้อมูล AI';
      summary.append(el('p','sr-muted','Statistical summary (ไม่ใช่ AI) · '+reason));
      if(x.count)summary.append(el('p','','จำนวน '+x.count+' รีวิว · ด้านคะแนนสูงสุด: '+(dims[x.strongest]||'—')+' · ด้านคะแนนต่ำสุด: '+(dims[x.weakest]||'—')));
    }
    const history=el('section','si-block');history.append(el('h5','','Version history & Agent breakdown'));
    const entries=Object.entries(s.versions).sort(([a],[b])=>b.localeCompare(a,undefined,{numeric:true}));
    history.append(table(['Version','คะแนนเฉลี่ย','รีวิว','Helpful'],entries.map(([v,m])=>['v'+v+(v===skill.version?' (ปัจจุบัน)':''),fmt(m.average),m.count,m.helpful])));
    const current=s.versions[skill.version];
    if(current&&Object.keys(current.agents).length)history.append(table(['AI Agent','คะแนนเฉลี่ย','รีวิว'],Object.entries(current.agents).map(([a,m])=>[agents[a]||a,fmt(m.average),m.count])));
    const checks=el('section','si-block');checks.append(el('h5','','Automated repository benchmark'));
    checks.append(el('p','si-bench-value',b.passed+' / '+b.total+' checks · '+b.score+'%'));
    checks.append(el('p','sr-muted','ตรวจโครงสร้างจาก source commit '+String(state.sourceCommit||'').slice(0,8)+' · ไม่ได้รัน Agent หรือวัดผลลัพธ์จริง (NOT RUN)'));
    const list=el('div','si-check-list');for(const c of b.checks){const item=el('div','si-check');item.append(el('span',c.pass?'si-pass':'si-fail',c.pass?'PASS':'FAIL'),el('span','',c.label),el('span','sr-muted',c.detail));list.append(item);}checks.append(list);
    const tool=b.toolTests||{status:'not_run',suites:[]};
    checks.append(el('h5','','Functional tool regression · '+String(tool.status).toUpperCase()));
    if(tool.suites.length)checks.append(table(['Suite','สถานะ','Tests','เวลารัน (ms)'],tool.suites.map(t=>[t.suite,t.status,t.tests??'—',t.durationMs])));
    else checks.append(el('p','sr-muted','ยังไม่มีชุดทดสอบแบบ allowlist สำหรับ Skill นี้ หรือยังไม่ได้รัน'));
    checks.append(el('p','sr-muted','ชุดทดสอบใช้ synthetic fixtures จาก Repository ไม่ใช่การประเมินผลงานของ Agent หรือข้อมูลจริงของผู้ใช้'));
    root.append(summary,history,checks);
  }
  window.SkillInsights={init,render};
})();
