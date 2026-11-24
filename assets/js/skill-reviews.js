/* Skill Catalog community reviews; no tokens or user HTML. */
(function browserModule(){
  'use strict';
  const repo='https://github.com/codelv8-org/skills';
  const criteria=[['quality','Output Quality','คุณภาพผลลัพธ์'],['accuracy','Accuracy','ความถูกต้อง'],['ease','Ease of Use','ความง่ายในการใช้งาน'],['efficiency','Efficiency','ประสิทธิภาพ'],['consistency','Consistency','ความสม่ำเสมอ']];
  const agents={'codex':'OpenAI Codex','claude-code':'Anthropic Claude Code','antigravity':'Google Antigravity','other':'Other'};
  let records=[], ratings={}, status='loading';
  const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=String(txt);return n;};
  const read=async path=>{const res=await fetch(path,{cache:'no-cache'});if(!res.ok)throw Error('HTTP '+res.status);return res.json();};
  async function init(){
    const label=document.getElementById('skillReviewStatus');
    try {
      if(!location.protocol.startsWith('http')) {status='offline';return;}
      const [r,s]=await Promise.all([read('data/reviews.json'),read('data/ratings.json')]);
      if(r.schemaVersion!==1||s.schemaVersion!==1||!Array.isArray(r.reviews)||!s.skills||r.generatedAt!==s.generatedAt)throw Error('Invalid or mismatched review data');
      records=r.reviews;ratings=s.skills;status='ready';
    } catch { status='unavailable'; }
    finally {if(label)label.textContent=status==='ready'?'คะแนนจากรีวิวที่อนุมัติแล้ว':status==='offline'?'เปิดแบบออฟไลน์ · ไม่มีคะแนนออนไลน์':'ไม่สามารถโหลดคะแนนได้ในขณะนี้';}
  }
  function summarize(list){
    const n=list.length, distribution=[0,0,0,0,0], dimensions=Object.fromEntries(criteria.map(([k])=>[k,0]));let total=0;
    for(const r of list){total+=r.overall;distribution[Math.max(0,Math.min(4,Math.round(r.overall)-1))]++;for(const [k] of criteria)dimensions[k]+=r.ratings[k];}
    return {count:n,average:n?total/n:0,distribution,dimensions:Object.fromEntries(criteria.map(([k])=>[k,n?dimensions[k]/n:0]))};
  }
  function stat(skill){const s=ratings[skill.id];return s&&s.versions&&Object.prototype.hasOwnProperty.call(s.versions,skill.version)?s.versions[skill.version]:null;}
  function badge(skill){
    if(status!=='ready')return '<span class="sr-badge sr-muted">★ คะแนนยังไม่พร้อม</span>';
    const s=stat(skill);
    if(!s||!s.count)return '<span class="sr-badge sr-muted">☆ ยังไม่มีรีวิวสำหรับเวอร์ชันนี้</span>';
    return '<span class="sr-badge"><span class="sr-star" aria-hidden="true">★</span> <strong>'+Number(s.average).toFixed(1)+'</strong><span class="sr-muted"> / 5 · '+Number(s.count)+' รีวิว</span></span>';
  }
  function sort(skills,mode){
    const result=[...skills];if(status!=='ready')return result;
    if(mode==='rated')result.sort((a,b)=>(stat(b)?.average||0)-(stat(a)?.average||0)||(stat(b)?.count||0)-(stat(a)?.count||0));
    if(mode==='reviewed')result.sort((a,b)=>(stat(b)?.count||0)-(stat(a)?.count||0)||(stat(b)?.average||0)-(stat(a)?.average||0));
    if(mode==='updated')result.sort((a,b)=>String(ratings[b.id]?.updatedAt||'').localeCompare(String(ratings[a.id]?.updatedAt||'')));
    return result;
  }
  function option(select,value,label){const n=el('option','',label);n.value=value;select.append(n);}
  function selectControl(labelText){const label=el('label','sr-select-label',labelText),select=el('select');label.append(select);return [label,select];}
  function render(skill,root){
    if(!root)return;
    const heading=el('h4','modal-bento-title','Ratings & Reviews · คะแนนและรีวิว');heading.id='srHeading';
    const intro=el('p','sr-muted','คะแนนแสดงเฉพาะรีวิวที่ผ่านการอนุมัติ และแยกตามเวอร์ชันของ Skill');
    const controls=el('div','sr-filter');
    const [versionLabel,versionSelect]=selectControl('เวอร์ชันที่รีวิว');
    const [agentLabel,agentSelect]=selectControl('AI Agent');
    const [orderLabel,orderSelect]=selectControl('เรียงรีวิว');
    const all=records.filter(r=>r.skillId===skill.id);
    const versions=[...new Set([skill.version,...all.map(r=>r.version)])];
    for(const v of versions)option(versionSelect,v,'v'+v+(v===skill.version?' (ปัจจุบัน)':''));
    option(agentSelect,'all','ทุก Agent');for(const [k,name] of Object.entries(agents))option(agentSelect,k,name);
    option(orderSelect,'recent','ล่าสุด');option(orderSelect,'high','คะแนนสูงสุด');option(orderSelect,'low','คะแนนต่ำสุด');
    controls.append(versionLabel,agentLabel,orderLabel);
    const summary=el('div','sr-summary'),list=el('div','sr-list');
    function draw(){
      summary.replaceChildren();list.replaceChildren();
      if(status!=='ready'){summary.append(el('p','sr-muted',status==='offline'?'เปิดแบบออฟไลน์ ไม่สามารถโหลดรีวิวได้':'ข้อมูลรีวิวยังไม่พร้อม โปรดลองใหม่ภายหลัง'));return;}
      const filtered=all.filter(r=>r.version===versionSelect.value&&(agentSelect.value==='all'||r.agent===agentSelect.value));
      const s=summarize(filtered);
      if(!s.count){summary.append(el('p','sr-muted','ยังไม่มีรีวิวที่ได้รับอนุมัติสำหรับตัวเลือกนี้'));return;}
      const score=el('div','sr-score');score.append(el('strong','',s.average.toFixed(1)),el('span','sr-star','★'.repeat(Math.round(s.average))+'☆'.repeat(5-Math.round(s.average))),el('span','sr-muted',s.count+' รีวิว'));
      const hist=el('div','sr-hist');
      for(let i=5;i>=1;i--){const row=el('div','sr-bar-row');const meter=el('progress');meter.max=s.count;meter.value=s.distribution[i-1];meter.setAttribute('aria-label',i+' ดาว');row.append(el('span','',i+' ★'),meter,el('span','',s.distribution[i-1]));hist.append(row);}
      const detail=el('div','sr-dimensions');
      for(const [k,,label] of criteria){const row=el('div','sr-dimension');row.append(el('span','',label),el('strong','',s.dimensions[k].toFixed(1)+' / 5'));detail.append(row);}
      summary.append(score,hist,detail);
      filtered.sort((a,b)=>orderSelect.value==='high'?b.overall-a.overall:orderSelect.value==='low'?a.overall-b.overall:String(b.approvedAt).localeCompare(String(a.approvedAt)));
      for(const r of filtered){
        const article=el('article','sr-review');
        const header=el('div','sr-review-head');const author=el('strong','',r.author);
        const link=el('a','', 'GitHub #'+r.issueNumber);link.href=repo+'/issues/'+Number(r.issueNumber);link.target='_blank';link.rel='noopener noreferrer';
        header.append(author,link);article.append(header,el('div','sr-star','★'.repeat(Math.round(r.overall))+'☆'.repeat(5-Math.round(r.overall))+' '+Number(r.overall).toFixed(1)),el('p','sr-muted',(agents[r.agent]||'Other')+' · v'+r.version+' · '+String(r.approvedAt).slice(0,10)));
        if(r.comment)article.append(el('p','sr-comment',r.comment));list.append(article);
      }
    }
    for(const c of [versionSelect,agentSelect,orderSelect])c.addEventListener('change',draw);
    const disclosure=el('details','sr-write');const toggle=el('summary','','เขียนรีวิวเวอร์ชัน v'+skill.version);disclosure.append(toggle);
    const form=el('form','sr-form');const notice=el('p','sr-muted','คุณจะไปยัง GitHub เพื่อเข้าสู่ระบบและยืนยันการส่ง Issue สาธารณะ รีวิวจะขึ้นบน Catalog หลังผู้ดูแลอนุมัติเท่านั้น ห้ามใส่ข้อมูลส่วนบุคคล ข้อมูลผู้ป่วย รหัสผ่าน หรือข้อมูลลับ');
    const [aLabel,aSelect]=selectControl('AI Agent ที่ใช้จริง');aSelect.name='agent';aSelect.required=true;option(aSelect,'','เลือก AI Agent');for(const [k,name] of Object.entries(agents))option(aSelect,k,name);
    form.append(notice,aLabel);
    const liveScore=el('output','sr-live','ให้คะแนนครบทั้ง 5 ด้านเพื่อคำนวณคะแนนรวม');liveScore.setAttribute('aria-live','polite');
    for(const [key,,label] of criteria){
      const field=el('fieldset','sr-field');field.append(el('legend','',label));const row=el('div','sr-stars');
      for(let i=1;i<=5;i++){const l=el('label','sr-choice');const input=el('input');input.type='radio';input.name=key;input.value=String(i);input.required=true;input.setAttribute('aria-label',i+' ดาว');const star=el('span','','★');star.setAttribute('aria-hidden','true');l.append(input,star);row.append(l);}
      field.append(row);form.append(field);
    }
    form.append(liveScore);
    function updateScore(){const values=new FormData(form);const nums=criteria.map(([k])=>Number(values.get(k)||0));for(const [key] of criteria){const selected=Number(values.get(key)||0);for(const radio of form.querySelectorAll('input[name="'+key+'"]'))radio.parentElement.classList.toggle('selected',Number(radio.value)<=selected);}liveScore.textContent=nums.every(n=>n>0)?'คะแนนรวม '+(nums.reduce((a,b)=>a+b,0)/5).toFixed(1)+' / 5':'ให้คะแนนครบทั้ง 5 ด้านเพื่อคำนวณคะแนนรวม';}
    form.addEventListener('change',updateScore);
    const commentLabel=el('label','sr-select-label','ความคิดเห็น / สิ่งที่ควรปรับปรุง (ไม่บังคับ)');const textarea=el('textarea');textarea.name='comment';textarea.maxLength=500;textarea.rows=4;textarea.placeholder='แชร์ประสบการณ์จริง ไม่เกิน 500 ตัวอักษร';commentLabel.append(textarea);form.append(commentLabel);
    const submit=el('button','btn-detail sr-submit','ดำเนินการต่อบน GitHub ↗');submit.type='submit';form.append(submit);
    const warning=el('p','sr-muted');warning.setAttribute('role','alert');form.append(warning);
    form.addEventListener('submit',e=>{
      e.preventDefault();warning.textContent='';
      const values=new FormData(form);const rows=['<!-- codelv8-skill-review:v1 -->','Skill: '+skill.id,'Version: '+skill.version,'Agent: '+values.get('agent'),...criteria.map(([k,name])=>name+': '+values.get(k)),'---',String(values.get('comment')||'').trim()];
      const url=new URL(repo+'/issues/new');url.searchParams.set('title','[Skill Review] '+skill.id+' v'+skill.version);url.searchParams.set('body',rows.join('\n'));
      if(url.href.length>7800){warning.textContent='ความคิดเห็นยาวเกินขนาดลิงก์ GitHub กรุณาลดข้อความแล้วลองใหม่';return;}
      window.location.assign(url.href);
    });
    disclosure.append(form);
    const existing=el('a','sr-existing','เปิดรายการรีวิวบน GitHub ↗');existing.href=repo+'/issues?q='+encodeURIComponent('is:issue "[Skill Review] '+skill.id+'"');existing.target='_blank';existing.rel='noopener noreferrer';
    root.replaceChildren(heading,intro,controls,summary,list,disclosure,existing);draw();
  }
  window.SkillReviews={init,badge,sort,render};
})();
