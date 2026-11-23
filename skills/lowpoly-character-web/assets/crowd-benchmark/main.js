/** Actual WebGL benchmark. No pretend FPS result; measurements are made in user's browser. */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

const renderer=new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
renderer.setSize(window.innerWidth,Math.max(200,window.innerHeight-140));
renderer.shadowMap.enabled=false;
document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#dfe4ed');
const camera=new THREE.PerspectiveCamera(43,window.innerWidth/Math.max(200,window.innerHeight-140),0.05,500);
camera.position.set(0,10,25);camera.lookAt(0,1,0);
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(7,15,8);light.castShadow=true;scene.add(light);
scene.add(new THREE.HemisphereLight(0xf4f7ff,0x6b7184,2));
const ground=new THREE.Mesh(new THREE.PlaneGeometry(220,220),new THREE.MeshStandardMaterial({color:'#bdc6d2',roughness:.9}));ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
const asset=await new GLTFLoader().loadAsync('/model.glb');
const base=asset.scene;
// Skinned meshes must be cloned with the correct bone references.
const crowd=[];const mixers=[];const clock=new THREE.Clock();let frameWindow=[];let lastFrameTimestamp=null;let frames=0;
const getClip=()=>asset.animations.find(a=>a.name===document.querySelector('#clip').value);
function rebuild(){
  for(const o of crowd){scene.remove(o)}
  crowd.length=0;mixers.length=0;frameWindow=[];
  const count=Number(document.querySelector('#count').value);
  const columns=Math.ceil(Math.sqrt(count));
  for(let i=0;i<count;i++){
    const model=cloneSkinned(base);
    model.position.set((i%columns-(columns-1)/2)*2.3,0,(Math.floor(i/columns)-Math.floor((count-1)/columns)/2)*2.3);
    model.traverse(o=>{if(o.isMesh){o.castShadow=true}});
    scene.add(model);crowd.push(model);
    const clip=getClip();
    if(clip){const mixer=new THREE.AnimationMixer(model);mixer.clipAction(clip).play();mixers.push(mixer)}
  }
  renderer.shadowMap.enabled=document.querySelector('#shadows').checked;
  camera.position.set(0,Math.max(7,columns*.8),Math.max(16,columns*3));camera.lookAt(0,1,0);
}
function stats(){
 const draws=renderer.info.render.calls;
 const tris=renderer.info.render.triangles;
 const recent=frameWindow.slice(-180).sort((a,b)=>a-b);
 const mean=frameWindow.length?frameWindow.reduce((a,b)=>a+b,0)/frameWindow.length:0;
 const p95=recent.length?recent[Math.min(recent.length-1,Math.floor(recent.length*.95))]:0;
 return {visible_instances:crowd.length,active_mixers:mixers.length,draw_calls:draws,triangles:tris,
  mean_frame_ms:+mean.toFixed(2),p95_frame_ms:+p95.toFixed(2),fps_from_mean_frame_ms:mean?+(1000/mean).toFixed(1):null,
  dpr:renderer.getPixelRatio(),shadow_enabled:renderer.shadowMap.enabled,webgl_renderer:renderer.getContext().getParameter(renderer.getContext().RENDERER),
  note:'Frame times include RAF scheduling and render/mixer update. FPS depends on hardware and other scene work.'};
}
function tick(){requestAnimationFrame(tick);const dt=Math.min(.05,clock.getDelta());mixers.forEach(m=>m.update(dt));
 const timestamp=performance.now();renderer.render(scene,camera);
 if(lastFrameTimestamp!==null){frameWindow.push(timestamp-lastFrameTimestamp);if(frameWindow.length>300)frameWindow.shift()};
 lastFrameTimestamp=timestamp;frames++;
 if(frames%20===0)document.querySelector('#results').textContent=JSON.stringify(stats(),null,2);
}
document.querySelector('#reset').addEventListener('click',rebuild);
document.querySelector('#clip').addEventListener('change',rebuild);
document.querySelector('#export').addEventListener('click',async()=>{
 const delay=ms=>new Promise(r=>setTimeout(r,ms));frameWindow=[];await delay(10000);
 const data={...stats(),measured_at:new Date().toISOString(),model:'model.glb'};
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
 a.download=`character-benchmark-${crowd.length}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
});
window.addEventListener('resize',()=>{const height=Math.max(200,window.innerHeight-140);renderer.setSize(window.innerWidth,height);camera.aspect=window.innerWidth/height;camera.updateProjectionMatrix()});
rebuild();tick();
