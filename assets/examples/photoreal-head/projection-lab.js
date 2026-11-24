import * as THREE from 'three';

const VERSION='3.1.1';
const PATH=/^projection-lab\/[a-z0-9_]+\.webp$/;
const MODES=['front_only','multiview','tinted_mean','tinted_robust','reviewed_quarantine','coverage','ambiguity','uv_anisotropy','uv_density'];
const pct=x=>Number.isFinite(x)?`${(x*100).toFixed(2)}%`:'—';
const mae=x=>Number.isFinite(x)?x.toFixed(3):'—';
const num=x=>Number.isFinite(x)?x.toLocaleString('en-US'):'—';
const $=id=>document.getElementById(id);

// The baseline scan is retained. B1 textures use a separately validated atlas
// on identical geometry; never put these textures on the original UVs.
export function createProjectionLab({apply,restore,setLabel,prepare}){
  const select=$('projection-mode'), state=$('lab-status');
  let ready=false,assetReady=false,preparing=false,report=null,sequence=0;
  const loader=new THREE.TextureLoader(),cache=new Map();
  const setEnabled=()=>{select.disabled=!(ready&&assetReady&&report?.status==='B1_DIAGNOSTIC_COMPLETE');};
  const reset=()=>{sequence++;select.value='';};
  const prepareAsset=async()=>{
    if(!ready||preparing||report?.status!=='B1_DIAGNOSTIC_COMPLETE')return;
    preparing=true;
    state.textContent='กำลังตรวจโมเดลและ Atlas ของผล Benchmark…';
    try{
      await prepare(report);
      if(!ready)return;
      assetReady=true;
      state.textContent='B1 diagnostic complete · validated projection atlas · not real-photo QA';
      setEnabled();
    }catch(error){
      console.warn('Projection model:',error);
      assetReady=false;select.disabled=true;
      state.textContent='โมเดล Projection ไม่ตรงกับรายงานหรือโหลดไม่สำเร็จ — แสดง Baseline';
    }
  };
  const load=async mode=>{
    if(!cache.has(mode.id)){
      const promise=loader.loadAsync(mode.path).then(map=>{map.colorSpace=THREE.SRGBColorSpace;map.flipY=false;map.wrapS=map.wrapT=THREE.ClampToEdgeWrapping;map.needsUpdate=true;return new THREE.MeshBasicMaterial({map,color:0xffffff,toneMapped:false});});
      cache.set(mode.id,promise);promise.catch(()=>cache.delete(mode.id));
    }
    return cache.get(mode.id);
  };
  select.addEventListener('change',async()=>{
    const ticket=++sequence;
    if(!select.value){restore();return;}
    if(!ready||!assetReady||!report)return;
    const mode=report.modes.find(m=>m.id===select.value);
    if(!mode)return;
    setLabel('Loading diagnostic…');
    try{const material=await load(mode);if(ticket!==sequence)return;apply(material,mode.label);}
    catch(error){console.error('Projection texture:',error);if(ticket!==sequence)return;select.value='';restore();state.textContent='โหลด Texture ไม่สำเร็จ — กลับไปใช้พื้นผิวสแกน';}
  });
  const show=(r)=>{
    report=r;
    $('lab-version').textContent=`v${r.skillVersion}`;
    if(r.uv){$('lab-uv').textContent=r.uv.status; $('lab-uv').title=r.uv.errors?.join('; ')||'Numeric diagnostic only';}
    if(r.status!=='B1_DIAGNOSTIC_COMPLETE'){
      state.textContent=r.status==='BLOCKED'?'Benchmark BLOCKED — ยังไม่มี Texture ผลลัพธ์ที่ตรวจสอบได้':'ยังไม่มี Benchmark ของ build นี้ — พื้นผิวสแกนเดิมยังเปิดดูได้';
      return;
    }
    if(r.uv?.status!=='PASS_UV_ONLY'||r.uv.errors?.length||r.projectionMesh!=='model/projection-head.glb'||!/^[a-f0-9]{64}$/.test(r.sourceSha256)||!/^[a-f0-9]{64}$/.test(r.baselineSha256)||!r.coverage||!r.stress?.mae||!Array.isArray(r.modes)||r.modes.length!==MODES.length||new Set(r.modes.map(m=>m.id)).size!==MODES.length||r.modes.some(m=>!MODES.includes(m.id)||!PATH.test(m.path)||m.path!==`projection-lab/${m.id}.webp`||typeof m.label!=='string'))throw Error('Invalid projection manifest');
    $('lab-baseline-uv').textContent=r.baselineUV?.status||'NOT RUN';
    for(const mode of r.modes){const option=document.createElement('option');option.value=mode.id;option.textContent=mode.label;select.append(option);}
    $('lab-front').textContent=pct(r.coverage.front_only); $('lab-multi').textContent=pct(r.coverage.multiview);
    $('lab-mean').textContent=mae(r.stress.mae.tinted_mean); $('lab-robust').textContent=mae(r.stress.mae.tinted_robust); $('lab-quarantine').textContent=mae(r.stress.mae.reviewed_quarantine);
    $('lab-ambiguous').textContent=num(r.stress.ambiguity?.tinted_robust);
    $('lab-flagged').textContent=(r.stress.flaggedViews||[]).join(', ')||'None';
    $('lab-angles').textContent=(r.holdoutAngles||[]).map(a=>`${a}°`).join(', ');
    if(r.comparison==='projection-lab/comparison.jpg'){$('lab-comparison').src=r.comparison;$('lab-comparison').hidden=false;}
    $('lab-links').hidden=false;
    prepareAsset();
  };
  // Read current generated report, not stale hard-coded metrics. Fail closed on missing version.
  fetch('reports/projection_lab.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error('No projection report');return r.json();}).then(r=>{
    if(r.schemaVersion!==1||r.skillVersion!==VERSION)throw Error('Stale or invalid projection report');show(r);
  }).catch(error=>{console.warn('Projection Lab:',error);report=null;select.disabled=true;state.textContent='ยังไม่มีรายงาน Projection Lab ของ v3.1.1; แสดงสแกนต้นฉบับได้ตามปกติ';});
  return {ready(){ready=true;prepareAsset();},disable(){ready=false;assetReady=false;reset();setEnabled();},reset};
}
