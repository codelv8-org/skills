import {createStageViewer} from './gltf-viewer.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const viewNames = {front: 'ด้านหน้า', right: 'ด้านขวา', back: 'ด้านหลัง', left: 'ด้านซ้าย', three: 'มุมเฉียง ¾', free: 'หมุนอิสระ'};
const viewThai = {front: 'ด้านหน้า', right: 'ด้านขวา', back: 'ด้านหลัง', left: 'ด้านซ้าย'};
const stageNames = {HEAD: 'ศีรษะ', TORSO: 'ลำตัว', ARMS_HANDS: 'แขนและมือ', LEGS_FEET: 'ขาและเท้า', OUTFIT_GEAR: 'เสื้อผ้าและอุปกรณ์', INTEGRATION: 'โมเดลประกอบรวม'};
const statusLabels = {
  REVIEW_REQUIRED: ['รอตรวจและปรับแก้', 'ยังไม่รับรองความเหมือนหรือความพร้อมใช้งาน'],
  PROTOTYPE: ['ต้นแบบสำหรับตรวจ', 'ตรวจหลักฐานก่อนนำไปใช้งานจริง'],
  UNVERIFIED: ['ยังไม่ยืนยันผล', 'ยังไม่มีหลักฐานครบตามเกณฑ์ที่กำหนด'],
  NOT_TESTED: ['ยังไม่ได้ทดสอบ', 'ยังไม่มีผลทดสอบในขอบเขตนี้'],
  PERFORMANCE_NOT_TESTED: ['ยังไม่ได้ทดสอบประสิทธิภาพ', 'ยังไม่มีผลวัดบนเบราว์เซอร์และอุปกรณ์เป้าหมาย'],
  PASS: ['ผ่านเกณฑ์ที่ระบุ', 'สถานะตามข้อมูลที่แนบ โปรดอ่านขอบเขตและหลักฐานในรายงาน'],
  FAIL: ['ไม่ผ่านเกณฑ์', 'ตรวจรายการที่ต้องแก้ไขในรายงานก่อนประเมินใหม่'],
  BLOCKED: ['หยุดรอแก้ไข', 'ต้องแก้เงื่อนไขที่ค้างก่อนดำเนินขั้นตอนถัดไป']
};
const DEFAULT_CONFIG = {
  title: 'ตรวจรูปทรงศีรษะ', subtitle: 'เทียบภาพอ้างอิงกับโมเดล 3D เพื่อปรับรูปทรงศีรษะ', stage: 'HEAD', stageTitle: 'ตรวจรูปทรงศีรษะ', iteration: '02', status: 'REVIEW_REQUIRED',
  current: {url: './head.glb', label: 'โมเดลที่ปรับล่าสุด', description: 'ต้นแบบโมเดลนิ่ง · รอตรวจความเหมือน', tag: 'รุ่นปัจจุบัน / V02'},
  previous: {url: './previous-head.glb', label: 'โมเดลรุ่นก่อนหน้า', description: 'รุ่นก่อนหน้าสำหรับเทียบรูปทรง', tag: 'รุ่นก่อนหน้า / V01'},
  references: {front: './reference/front.png', right: './reference/right.png', back: './reference/back.png', left: './reference/left.png'},
  sourceSheet: './reference/source.png', referenceKind: 'ภาพอ้างอิงเฉพาะส่วน', renders: {}, qaUrl: null, qaReportUrl: null, diagnosticBoard: null, stateNotes: [],
  cameraPresets: {front: 0, right: 90, back: 180, left: -90, three: -35}, approximateViews: false,
  note: 'สถานะนี้ยังไม่รับรองความเหมือน โปรดตรวจทั้งด้านหน้า ด้านข้าง และด้านหลัง ก่อนผ่านไปทำส่วนถัดไป'
};
let config = DEFAULT_CONFIG, viewer = null, selectedAsset = 'current', currentView = 'front', requestNumber = 0;
const assetCache = new Map();
const dataWarnings = new Set();
const reference = {view: 'front', zoom: 1, x: 0, y: 0};
const reviewState = window.__stageReview = {configLoaded: false, qaLoaded: false, reference: {...reference}, assetKey: 'current'};
window.__viewerQA = {loaded: false, frames: 0, draws: 0, errors: [], webglError: 0, engine: 'initializing'};

function text(selector, value) { const element = $(selector); if (element) element.textContent = value; }
function pressGroup(selector, predicate) { for (const button of $$(selector)) { const selected = predicate(button); button.classList.toggle('selected', selected); button.setAttribute('aria-pressed', String(selected)); } }
function setRuntime(message, state = 'pending') { text('#runtime-status', message); $('#runtime-dot').className = `live-indicator ${state}`; }
function assetSize(bytes) { return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KiB` : `${(bytes / (1024 * 1024)).toFixed(2)} MiB`; }
function dataWarning(message) { dataWarnings.add(message); text('#data-warning', [...dataWarnings].join(' · ')); $('#data-warning').hidden = false; }
function readableError(message) {
  if (/[\u0E00-\u0E7F]/.test(message)) return message;
  if (/fetch|network|load failed/i.test(message)) return 'โหลดไฟล์โมเดลไม่สำเร็จ โปรดตรวจลิงก์ไฟล์และการเชื่อมต่อ';
  if (/static export|skin deformation/i.test(message)) return 'ตัวแสดงผลนี้รองรับโมเดลนิ่ง โปรดส่งออก GLB ที่นำผลจากโครงกระดูกมาใช้กับรูปทรงแล้ว';
  if (/morph targets/i.test(message)) return 'ต้องนำผลการเปลี่ยนรูป (morph targets) มาใช้กับโมเดลก่อนส่งออกเป็น GLB ท่านิ่ง';
  if (/opaque materials/i.test(message)) return 'ตัวแสดงผลนี้รองรับวัสดุทึบแสงเท่านั้น โปรดปรับวัสดุแล้วส่งออกใหม่';
  if (/unsupported|not supported|only .*supported/i.test(message)) return 'ไฟล์ใช้คุณสมบัติที่ตัวแสดงผลนี้ยังไม่รองรับ โปรดตรวจรายละเอียดและส่งออกในรูปแบบที่รองรับ';
  if (/texture|base-color image/i.test(message)) return 'เปิดภาพพื้นผิวของโมเดลไม่ได้ โปรดฝังภาพไว้ใน GLB และตรวจรูปแบบพื้นผิวที่รองรับ';
  if (/32-bit mesh indices/i.test(message)) return 'เบราว์เซอร์นี้ไม่รองรับดัชนีเมชแบบ 32 บิต โปรดตรวจด้วยเบราว์เซอร์หรือโปรแกรม 3D ที่รองรับ';
  if (/WebGL|shader/i.test(message)) return 'เกิดข้อผิดพลาดในการวาดภาพ 3 มิติ โปรดดูรายละเอียด หรือใช้ภาพเรนเดอร์นิ่งตรวจประกอบ';
  return 'อ่านรูปทรงจาก GLB ไม่สำเร็จ โปรดตรวจความสมบูรณ์ของไฟล์และรายละเอียดทางเทคนิคด้านล่าง';
}
function readableWarning(message) {
  if (message.startsWith('Normal, occlusion,')) return 'ยังไม่แสดงแผนที่พื้นผิว normal, occlusion, emissive และ metallic/roughness โปรดใช้สีจุดยอดหรือค่าวัสดุสำหรับตรวจขั้นนี้';
  if (message.startsWith('Animation tracks')) return 'ตัวแสดงผลนี้ไม่เล่นแอนิเมชัน แสดงเฉพาะท่านิ่งที่ส่งออกไว้ในไฟล์';
  if (message.startsWith('Software 3D:')) return 'โหมดซอฟต์แวร์ตรวจความลึกของผิวทึบแสงและเส้นโครง แสงเป็นภาพประมาณ ยังไม่ได้ยืนยัน WebGL, GPU, PBR หรือประสิทธิภาพ';
  return `ข้อจำกัดจากตัวแสดงผล: ${message}`;
}
function renderNotes(selector, entries, numbered = false) {
  const list = $(selector); list.replaceChildren();
  const notes = Array.isArray(entries) ? entries.filter(entry => typeof entry?.title === 'string' && typeof entry.description === 'string') : [];
  notes.forEach((entry, i) => {
    const li = document.createElement('li'), body = document.createElement('div'), title = document.createElement('strong'), description = document.createElement('p');
    if (numbered) { const number = document.createElement('span'); number.textContent = String(i + 1).padStart(2, '0'); li.append(number); }
    title.textContent = entry.title; description.textContent = entry.description; body.append(title, description); li.append(body); list.append(li);
  });
  return notes.length;
}
function showError(error) {
  const message = error?.message || String(error);
  const explanation = readableError(message);
  $('#loading-state').hidden = true; $('#model-error').hidden = false; text('#model-error-message', explanation);
  text('#model-error-detail', message); $('#model-error-details').hidden = explanation === message;
  $('#model-live-badge').innerHTML = '<i></i> เปิดโมเดลไม่สำเร็จ';
  text('#engine-label', viewer?.engine || '—'); setRuntime('เปิดโมเดล 3 มิติไม่สำเร็จ', 'failed');
  const qa = window.__viewerQA; qa.loaded = false; if (!qa.errors.includes(message)) qa.errors.push(message);
  $('#still-views').open = true;
}
function applyConfig() {
  document.title = `${config.title} · Character Web Studio`;
  $('#project-title').replaceChildren(document.createTextNode(config.title));
  const dot = document.createElement('span'); dot.className = 'title-dot'; dot.textContent = '.'; $('#project-title').append(dot);
  const stageName = stageNames[config.stage] || config.stageTitle;
  text('#project-subtitle', config.subtitle); text('#stage-title', config.stageTitle); text('#stage-breadcrumb', `${stageName} (${config.stage})`); text('#stage-chip', `${stageName} · ต้นแบบ`);
  const canonicalStatus = String(config.status || 'REVIEW_REQUIRED');
  const [statusLabel, statusDescription] = statusLabels[canonicalStatus] || ['สถานะจากรายงาน', 'โปรดตรวจความหมายของรหัสและหลักฐานในรายงานที่แนบ'];
  text('#iteration', config.iteration); text('#review-status', statusLabel); text('#review-status-code', canonicalStatus); text('#review-status-description', statusDescription); text('#review-note', config.note);
  $('#review-status').dataset.status = canonicalStatus; reviewState.status = canonicalStatus;
  $('#source-link').hidden = !config.sourceSheet; if (config.sourceSheet) $('#source-link').href = config.sourceSheet;
  const qaLink = config.qaReportUrl || config.qaUrl;
  $('#qa-link').hidden = !qaLink; if (qaLink) $('#qa-link').href = qaLink;
  text('#qa-link-label', config.qaReportUrl ? 'รายงาน QA' : 'ข้อมูล QA (JSON)');
  $('#diagnostic-link').hidden = !config.diagnosticBoard; if (config.diagnosticBoard) $('#diagnostic-link').href = config.diagnosticBoard;
  $('[data-asset="previous"]').disabled = !config.previous?.url;
  if (!config.previous?.url) $('[data-asset="previous"]').title = 'ยังไม่มีรุ่นก่อนหน้าแนบมา';
  if (Array.isArray(config.focus)) $('.focus-section').hidden = renderNotes('#focus-list', config.focus, true) === 0;
  $('#state-notes').hidden = renderNotes('#state-notes-list', config.stateNotes) === 0;
  const stillGrid = $('#still-grid'); stillGrid.replaceChildren(); let available = 0;
  for (const view of ['front', 'right', 'back', 'left']) {
    const url = config.renders?.[view]; if (!url) continue; available++;
    const a = document.createElement('a'), img = document.createElement('img'), caption = document.createElement('span'), badge = document.createElement('em');
    a.className = 'still-card'; a.href = url; a.target = '_blank'; a.rel = 'noopener'; a.setAttribute('aria-label', `เปิดภาพเรนเดอร์นิ่ง${viewThai[view]}`);
    img.src = url; img.alt = `ภาพเรนเดอร์นิ่งโมเดล${viewThai[view]}`; img.loading = 'lazy'; badge.textContent = 'ภาพนิ่ง'; caption.append(document.createTextNode(viewNames[view]), badge); a.append(img, caption); stillGrid.append(a);
    img.addEventListener('error', () => { a.hidden = true; available--; $('#still-empty').hidden = available > 0; });
  }
  $('#still-empty').hidden = available > 0; $('#fallback-link').hidden = !available && !config.diagnosticBoard;
  if (config.approximateViews) text('#project-subtitle', config.subtitle + ' · มุมกล้องอิงภาพโดยประมาณ');
}
function updateReferenceTransform() {
  $('#reference-image').style.transform = `translate(${reference.x}px, ${reference.y}px) scale(${reference.zoom})`;
  $('#reference-zoom').value = Math.round(reference.zoom * 100); text('#reference-zoom-value', `${Math.round(reference.zoom * 100)}%`);
  reviewState.reference = {...reference};
}
function setReferenceView(view) {
  if (!viewThai[view]) return;
  reference.view = view; reference.x = reference.y = 0; reference.zoom = 1; updateReferenceTransform();
  $('#reference-view').value = view;
  const image = $('#reference-image'), src = config.references?.[view];
  image.hidden = !src; $('#reference-missing').hidden = !!src;
  image.alt = `ภาพอ้างอิง${viewThai[view]} แสดงภาพที่ได้รับเต็มกรอบ`;
  const referenceKind = config.referenceKind === 'HEAD CROP' ? 'ภาพอ้างอิงศีรษะ' : config.referenceKind;
  text('#reference-caption', `${referenceKind} · ${viewNames[view]}`); text('#reference-dimensions', '—');
  if (src) image.src = src;
}
$('#reference-image').addEventListener('load', () => { $('#reference-missing').hidden = true; $('#reference-image').hidden = false; text('#reference-dimensions', `${$('#reference-image').naturalWidth} × ${$('#reference-image').naturalHeight}`); });
$('#reference-image').addEventListener('error', () => { $('#reference-missing').hidden = false; $('#reference-image').hidden = true; text('#reference-dimensions', 'เปิดภาพไม่ได้'); });

function onViewerChange(instance) {
  text('#model-zoom-value', `${Math.round(instance.camera.zoom * 100)}%`);
  const view = instance.camera.view;
  pressGroup('[data-view]', b => b.dataset.view === view);
  const projection = instance.camera.projection === 'orthographic' ? 'ฉายขนาน' : 'ทัศนียภาพ';
  text('#camera-label', `${projection} · ${viewNames[view] || viewNames.free}${config.approximateViews && ['left', 'right'].includes(view) ? ' ≈' : ''}`);
  text('#model-render-label', `${instance.qa.softwareFallback ? 'ซอฟต์แวร์ · ' : ''}${{material: 'สีและวัสดุ', clay: 'วัสดุสีเดียว', wireframe: 'เส้นโครง'}[instance.mode]}`);
  if (view !== currentView && viewThai[view] && $('#link-views').checked) setReferenceView(view);
  currentView = view; window.__viewerQA = instance.qa; instance.qa.assetKey = selectedAsset;
}
async function selectAsset(key) {
  const entry = config[key]; if (!entry?.url || !viewer) return;
  const request = ++requestNumber; selectedAsset = key; reviewState.assetKey = key;
  pressGroup('[data-asset]', b => b.dataset.asset === key);
  $('#loading-state').hidden = false; $('#model-error').hidden = true; setRuntime('กำลังอ่านไฟล์ GLB');
  $('#model-live-badge').innerHTML = '<i></i> กำลังโหลด';
  const tag = entry.tag || (key === 'current' ? 'รุ่นปัจจุบัน' : 'รุ่นก่อนหน้า');
  text('#version-name', entry.label); text('#version-description', entry.description); text('#model-version', tag.replace(/^CURRENT\b/, 'รุ่นปัจจุบัน').replace(/^PREVIOUS\b/, 'รุ่นก่อนหน้า'));
  for (const id of ['#stat-triangles', '#stat-vertices', '#stat-primitives', '#stat-size']) text(id, '—');
  try {
    if (!assetCache.has(key)) assetCache.set(key, fetch(entry.url).then(response => { if (!response.ok) throw new Error(`ไม่พบไฟล์โมเดล ${entry.url} (${response.status})`); return response.arrayBuffer(); }).catch(error => { assetCache.delete(key); throw error; }));
    const bytes = await assetCache.get(key); if (request !== requestNumber) return;
    const scene = await viewer.loadBytes(bytes, {preserveView: viewer.qa.loaded}); if (request !== requestNumber) return;
    text('#stat-triangles', scene.stats.triangles.toLocaleString('th-TH')); text('#stat-vertices', scene.stats.vertices.toLocaleString('th-TH')); text('#stat-primitives', scene.stats.primitives.toLocaleString('th-TH')); text('#stat-size', assetSize(scene.stats.fileBytes));
    $('#download-model').href = entry.url; $('#download-model').download = entry.url.split('/').at(-1);
    $('#download-model').setAttribute('aria-label', `ดาวน์โหลด GLB ${entry.label}`);
    $('#loading-state').hidden = true; $('#model-live-badge').innerHTML = viewer.qa.softwareFallback ? '<i></i> 3D ผ่านซอฟต์แวร์' : '<i></i> หมุนตรวจได้'; text('#engine-label', viewer.qa.softwareFallback ? 'Canvas 2D' : viewer.engine.toUpperCase());
    setRuntime(viewer.qa.softwareFallback ? 'โหมดซอฟต์แวร์ 3D พร้อมตรวจ' : 'โมเดล 3 มิติพร้อมตรวจ', 'ready'); viewer.qa.assetKey = key;
    $('#software-note').hidden = !viewer.qa.softwareFallback;
    $('#viewer-warnings').hidden = scene.warnings.length === 0; text('#viewer-warnings', scene.warnings.map(readableWarning).join(' '));
    reviewState.assetStats = scene.stats;
  } catch (error) { if (request === requestNumber) showError(error); }
}

for (const button of $$('[data-asset]')) button.addEventListener('click', () => selectAsset(button.dataset.asset));
for (const button of $$('[data-view]')) button.addEventListener('click', () => {
  const view = button.dataset.view;
  if (viewer) viewer.setPreset(view); else { pressGroup('[data-view]', b => b === button); currentView = view; }
  if ($('#link-views').checked && viewThai[view]) setReferenceView(view);
});
for (const button of $$('[data-mode]')) button.addEventListener('click', () => { if (!viewer) return; viewer.setMode(button.dataset.mode); pressGroup('[data-mode]', b => b === button); });
$('#fit-model').addEventListener('click', () => viewer?.fit()); $('#zoom-out').addEventListener('click', () => viewer?.zoom(1 / 1.15)); $('#zoom-in').addEventListener('click', () => viewer?.zoom(1.15));
$('#reference-view').addEventListener('change', e => setReferenceView(e.target.value));
$('#link-views').addEventListener('change', () => { if ($('#link-views').checked && viewThai[currentView]) setReferenceView(currentView); });
$('#reference-zoom').addEventListener('input', e => { reference.zoom = Number(e.target.value) / 100; updateReferenceTransform(); });
$('#reference-reset').addEventListener('click', () => { reference.zoom = 1; reference.x = reference.y = 0; updateReferenceTransform(); });
const referenceViewport = $('#reference-viewport'), referencePointers = new Map(); let lastPinch = null;
const referenceDistance = () => { const p = [...referencePointers.values()]; return p.length < 2 ? null : Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); };
referenceViewport.addEventListener('pointerdown', e => { if (e.target.closest('select,button,a') || e.button !== 0) return; referencePointers.set(e.pointerId, {x: e.clientX, y: e.clientY}); referenceViewport.setPointerCapture(e.pointerId); lastPinch = referenceDistance(); });
referenceViewport.addEventListener('pointermove', e => {
  const old = referencePointers.get(e.pointerId); if (!old) return;
  referencePointers.set(e.pointerId, {x: e.clientX, y: e.clientY});
  if (referencePointers.size > 1) { const distance = referenceDistance(); if (distance && lastPinch) reference.zoom = Math.max(0.5, Math.min(3, reference.zoom * distance / lastPinch)); lastPinch = distance; }
  else { reference.x += e.clientX - old.x; reference.y += e.clientY - old.y; }
  updateReferenceTransform();
});
const releaseReference = e => { referencePointers.delete(e.pointerId); lastPinch = referenceDistance(); };
referenceViewport.addEventListener('pointerup', releaseReference); referenceViewport.addEventListener('pointercancel', releaseReference); referenceViewport.addEventListener('lostpointercapture', releaseReference);
referenceViewport.addEventListener('wheel', e => { e.preventDefault(); reference.zoom = Math.max(0.5, Math.min(3, reference.zoom * Math.exp(-e.deltaY * 0.001))); updateReferenceTransform(); }, {passive: false});
referenceViewport.addEventListener('keydown', e => {
  if (e.target !== referenceViewport) return;
  if (e.key === 'Home') { reference.zoom = 1; reference.x = reference.y = 0; }
  else if (['+', '='].includes(e.key)) reference.zoom = Math.min(3, reference.zoom * 1.1);
  else if (['-', '_'].includes(e.key)) reference.zoom = Math.max(0.5, reference.zoom / 1.1);
  else if (e.key === 'ArrowLeft') reference.x -= 15;
  else if (e.key === 'ArrowRight') reference.x += 15;
  else if (e.key === 'ArrowUp') reference.y -= 15;
  else if (e.key === 'ArrowDown') reference.y += 15;
  else return;
  e.preventDefault(); updateReferenceTransform();
});

async function start() {
  try {
    const response = await fetch('./review-config.json');
    if (!response.ok) throw new Error(`Review config unavailable (${response.status})`);
    const supplied = await response.json();
    if (!supplied || typeof supplied !== 'object' || Array.isArray(supplied)) throw new Error('Review config must be an object');
    config = {...DEFAULT_CONFIG, ...supplied, cameraPresets: {...DEFAULT_CONFIG.cameraPresets, ...supplied.cameraPresets}}; reviewState.configLoaded = true;
  } catch (error) { reviewState.configWarning = String(error); dataWarning('เปิดการตั้งค่าหน้าพรีวิวไม่ได้ กำลังใช้ค่าเริ่มต้น'); }
  reviewState.config = config; applyConfig(); setReferenceView('front');
  if (config.qaUrl) fetch(config.qaUrl).then(response => { if (!response.ok) throw new Error(`QA JSON unavailable (${response.status})`); return response.json(); }).then(report => { reviewState.qaLoaded = true; reviewState.qaReport = report; }).catch(error => { reviewState.qaWarning = String(error); dataWarning('เปิดข้อมูล QA ไม่สำเร็จ จึงยังอ่านหลักฐานการตรวจจากไฟล์ JSON ไม่ได้'); });
  try { viewer = createStageViewer($('#model-canvas'), {onChange: onViewerChange, onError: showError, presets: config.cameraPresets}); window.__viewerQA = viewer.qa; await selectAsset('current'); }
  catch (error) { showError(error); }
}
start();
