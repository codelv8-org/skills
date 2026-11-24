import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { createProjectionLab } from './projection-lab.js?v=3.1.1';

const canvas = document.querySelector('#viewer');
const stage = canvas.parentElement;
const status = document.querySelector('#status');
const rotateButton = document.querySelector('#rotate');
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const viewButtons = [...document.querySelectorAll('[data-view]')];
const allControls = [...modeButtons, ...viewButtons, rotateButton, document.querySelector('#reset')];
const number = new Intl.NumberFormat('th-TH');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
let renderer, controls, camera, scene, model;
const originals = new Map();
let radius = .3;
let modelSize;
const labels = {skin: 'พื้นผิวสแกน', clay: 'Clay · ปิดแผนที่พื้นผิว', wire: 'Wireframe · โครงสร้างสามเหลี่ยม'};
const clay = new THREE.MeshStandardMaterial({ color: 0xa6b0b8, roughness: .8, metalness: 0 });
const wire = new THREE.MeshBasicMaterial({ color: 0x9be2ce, wireframe: true });
const setLabel = label => { document.querySelector('#mode-label').textContent = label; status.textContent = label; };
function setStandardMode(mode) {
  originals.forEach((original, mesh) => { mesh.material = mode === 'skin' ? original : mode === 'clay' ? clay : wire; });
  modeButtons.forEach(other => other.setAttribute('aria-pressed', String(other.dataset.mode === mode)));
  setLabel(labels[mode]); render();
}
const lab = createProjectionLab({
  setLabel,
  restore: () => setStandardMode('skin'),
  apply: (material, label) => {
    originals.forEach((original, mesh) => { mesh.material = material; });
    modeButtons.forEach(other => other.setAttribute('aria-pressed', 'false'));
    setLabel(label); render();
  }
});

function setAvailable(available) { allControls.forEach(button => { button.disabled = !available; }); }
function fail(error) {
  console.error('Head viewer:', error);
  document.querySelector('#error').hidden = false;
  status.textContent = 'ใช้ภาพจาก Blender ด้านล่างแทนการแสดงผล 3D ได้';
  setAvailable(false);
  document.querySelector('#projection-mode').disabled = true;
}
function render() { if (renderer && model) renderer.render(scene, camera); }
function stopRotation() { controls.autoRotate = false; rotateButton.setAttribute('aria-pressed', 'false'); }
function fitCamera() {
  if (!modelSize) return;
  const zoomRatio = camera.position.length() / radius || 1;
  const fitHeight = Math.max(modelSize.y, Math.hypot(modelSize.x, modelSize.z) / camera.aspect);
  radius = fitHeight / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) * 1.25;
  controls.minDistance = radius * .45;
  controls.maxDistance = radius * 2.1;
  camera.position.setLength(radius * Math.min(2.1, Math.max(.45, zoomRatio)));
}
function setView(view) {
  const angle = { front: 0, threequarter: Math.PI / 5, left: Math.PI / 2, right: -Math.PI / 2 }[view];
  stopRotation();
  camera.position.set(Math.sin(angle) * radius, radius * .04, Math.cos(angle) * radius);
  controls.target.set(0, 0, 0); controls.update(); render();
  viewButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
}

setAvailable(false);
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(33, 1, .001, 100);
  scene.add(new THREE.HemisphereLight(0xd8eaf2, 0x28303b, 2));
  const key = new THREE.DirectionalLight(0xffe2cb, 3); key.position.set(-1, 1, 2); scene.add(key);
  const fill = new THREE.DirectionalLight(0x9fcfff, 1.1); fill.position.set(1, .3, 1); scene.add(fill);
  const rim = new THREE.DirectionalLight(0xbee8f5, 2); rim.position.set(1, 1, -1); scene.add(rim);
  controls = new OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.enableDamping = false;
  controls.autoRotateSpeed = .7;
  controls.minPolarAngle = .25;
  controls.maxPolarAngle = Math.PI - .25;
  controls.addEventListener('change', render);
  controls.addEventListener('start', () => { stopRotation(); viewButtons.forEach(button => button.setAttribute('aria-pressed', 'false')); });
  new ResizeObserver(() => {
    const { width, height } = stage.getBoundingClientRect();
    camera.aspect = width / height; camera.updateProjectionMatrix(); renderer.setSize(width, height, false); fitCamera(); controls.update(); render();
  }).observe(stage);
  new GLTFLoader().load('model/head.glb', gltf => {
    model = gltf.scene;
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center);
    modelSize = box.getSize(new THREE.Vector3());
    fitCamera();
    model.traverse(object => { if (object.isMesh) originals.set(object, object.material); });
    scene.add(model); setView('threequarter'); setAvailable(true); lab.ready();
    status.textContent = 'โหลดแล้ว · ลากหมุนหรือใช้ปุ่มมุมกล้องเพื่อดูรูปทรง';
  }, undefined, fail);
  let lastTime;
  renderer.setAnimationLoop(time => {
    const delta = lastTime === undefined ? 0 : Math.min((time - lastTime) / 1000, .05); lastTime = time;
    if (controls.autoRotate && !document.hidden) { controls.update(delta); render(); }
  });
  canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); fail(new Error('WebGL context lost; reload the page to restore.')); });
  canvas.addEventListener('keydown', event => {
    if (!model) return;
    const offset = camera.position.clone().sub(controls.target);
    const spherical = new THREE.Spherical().setFromVector3(offset);
    const actions = {
      ArrowLeft: () => { spherical.theta -= .12; }, ArrowRight: () => { spherical.theta += .12; },
      ArrowUp: () => { spherical.phi = Math.max(.25, spherical.phi - .12); }, ArrowDown: () => { spherical.phi = Math.min(Math.PI - .25, spherical.phi + .12); },
      '+': () => { spherical.radius = Math.max(controls.minDistance, spherical.radius * .9); },
      '=': () => { spherical.radius = Math.max(controls.minDistance, spherical.radius * .9); },
      '-': () => { spherical.radius = Math.min(controls.maxDistance, spherical.radius * 1.1); }
    };
    if (event.key === 'Home') { event.preventDefault(); setView('threequarter'); return; }
    if (!actions[event.key]) return;
    event.preventDefault(); stopRotation(); actions[event.key]();
    camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));
    viewButtons.forEach(button => button.setAttribute('aria-pressed', 'false')); controls.update(); render();
  });
} catch (error) { fail(error); }

modeButtons.forEach(button => button.addEventListener('click', () => { lab.reset(); setStandardMode(button.dataset.mode); }));
viewButtons.forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
document.querySelector('#reset').addEventListener('click', () => setView('threequarter'));
rotateButton.addEventListener('click', () => {
  controls.autoRotate = !controls.autoRotate; rotateButton.setAttribute('aria-pressed', String(controls.autoRotate));
  status.textContent = controls.autoRotate ? 'กำลังหมุนอัตโนมัติ · กดปุ่มเดิมเพื่อหยุด' : 'หยุดหมุนแล้ว';
});
reducedMotion.addEventListener('change', () => { if (reducedMotion.matches && controls) stopRotation(); });
Promise.all([fetch('reports/glb_qa.json'), fetch('reports/build.json')]).then(async responses => {
  if (responses.some(response => !response.ok)) throw new Error('Missing QA report');
  const [qa] = await Promise.all(responses.map(response => response.json()));
  document.querySelector('#triangles').textContent = number.format(qa.triangles);
  document.querySelector('#size').textContent = new Intl.NumberFormat('th-TH', { maximumFractionDigits: 2 }).format(qa.size_mb) + ' MB';
  document.querySelector('#uv').textContent = `${number.format(qa.uv0_primitives)} / ${number.format(qa.primitive_count)} primitive`;
  document.querySelector('#structure').textContent = qa.status === 'PASS' ? 'โครงสร้าง GLB และ UV0' : 'ผลตรวจไฟล์ต้องทบทวน';
  const badge = document.querySelector('.qa-summary .pass');
  badge.textContent = qa.status === 'PASS' ? 'ผ่าน' : 'ต้องทบทวน';
}).catch(error => {
  console.error('QA report:', error);
  ['triangles', 'size', 'uv'].forEach(id => { document.getElementById(id).textContent = 'อ่านข้อมูลไม่ได้'; });
  document.querySelector('#structure').textContent = 'อ่านรายงานไม่ได้';
  document.querySelector('.qa-summary .pass').textContent = 'ไม่ยืนยัน';
});

const robustMetric = document.getElementById('lab-robust');
new MutationObserver(() => { document.querySelector('[data-robust-copy]').textContent = robustMetric.textContent; }).observe(robustMetric,{childList:true,characterData:true,subtree:true});
