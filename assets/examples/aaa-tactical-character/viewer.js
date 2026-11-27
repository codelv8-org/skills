// Specialized, offline-compatible CPU renderer for this benchmark GLB.
// No external libraries, network dependencies, image overlays or WebGL.
const canvas=document.querySelector('#view'),ctx=canvas.getContext('2d'),status=document.querySelector('#err');
let angle=Math.PI/6,tilt=0,zoom=1,mode=0,mesh=null,queued=false;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function fail(e){status.hidden=false;status.textContent='Preview unavailable: '+e.message;console.error(e)}
async function load(){
 if(!ctx)throw Error('Canvas 2D unavailable');
 const res=await fetch('operator.glb');if(!res.ok)throw Error('GLB HTTP '+res.status);
 const buf=await res.arrayBuffer(),d=new DataView(buf);
 if(d.getUint32(0,true)!==0x46546c67||d.getUint32(4,true)!==2||d.getUint32(8,true)!==buf.byteLength)throw Error('Invalid GLB header');
 const len=d.getUint32(12,true),g=JSON.parse(new TextDecoder().decode(new Uint8Array(buf,20,len))),base=28+len;
 const view=i=>{const v=g.bufferViews[i];return [buf,base+v.byteOffset,v.byteLength]};
 const typed=(i,C)=>{const [b,o,n]=view(i);return new C(b,o,n/C.BYTES_PER_ELEMENT)};
 const position=typed(0,Float32Array),normal=typed(1,Float32Array),uv=typed(2,Float32Array),idx=typed(3,Uint32Array);
 const [b,o,n]=view(4),image=await createImageBitmap(new Blob([new Uint8Array(b,o,n)],{type:'image/jpeg'}));
 const texCanvas=document.createElement('canvas');texCanvas.width=image.width;texCanvas.height=image.height;
 const tc=texCanvas.getContext('2d');tc.drawImage(image,0,0);image.close();
 const tex=tc.getImageData(0,0,texCanvas.width,texCanvas.height);
 if(normal.length!==position.length||uv.length/2!==position.length/3||idx.length%3||idx.some(i=>i>=position.length/3))throw Error('Invalid mesh arrays');
 mesh={position,normal,uv,idx,tex};
 document.querySelector('#triangles').textContent=(idx.length/3).toLocaleString()+' tris';
 document.querySelector('#vertices').textContent=(position.length/3).toLocaleString();
 document.querySelector('#size').textContent=(buf.byteLength/1024).toFixed(0)+' KiB';
 document.querySelector('#modelstats').textContent='Actual GLB / CPU rasterizer / '+(idx.length/3).toLocaleString()+' triangles';
 status.hidden=true;render();canvas.dataset.loaded='true';window.addEventListener('resize',requestRender);
}
function render(){
 if(!mesh)return;
 const W=Math.max(1,Math.min(900,Math.round(canvas.clientWidth))),H=Math.max(1,Math.min(660,Math.round(canvas.clientHeight)));
 canvas.width=W;canvas.height=H;
 const frame=ctx.createImageData(W,H),rgba=frame.data,zbuf=new Float32Array(W*H);zbuf.fill(-Infinity);
 const {position,normal,uv,idx,tex}=mesh,count=position.length/3;
 const sx=new Float32Array(count),sy=new Float32Array(count),sz=new Float32Array(count),light=new Float32Array(count);
 const c=Math.cos(angle),s=Math.sin(angle),ct=Math.cos(tilt),st=Math.sin(tilt),scale=Math.min(H*.88/1.8,W*.91/1.1)*zoom;
 for(let i=0;i<count;i++){
  const x=position[3*i],y=position[3*i+1]-.9,z=position[3*i+2],a=c*x-s*z,b=s*x+c*z;
  sx[i]=W/2+a*scale;sy[i]=H/2-(ct*y-st*b)*scale;sz[i]=st*y+ct*b;
  const nx=normal[3*i],ny=normal[3*i+1],nz=normal[3*i+2],na=c*nx-s*nz,nb=s*nx+c*nz;
  light[i]=.30+.70*Math.max(0,na*.42+(ct*ny-st*nb)*.67+(st*ny+ct*nb)*.61);
 }
 const texW=tex.width,texH=tex.height,px=tex.data;
 for(let i=0;i<idx.length;i+=3){
  const a=idx[i],b=idx[i+1],c0=idx[i+2],ax=sx[a],ay=sy[a],bx=sx[b],by=sy[b],cx=sx[c0],cy=sy[c0];
  const den=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);if(Math.abs(den)<1e-7)continue;
  const x0=clamp(Math.floor(Math.min(ax,bx,cx)),0,W-1),x1=clamp(Math.ceil(Math.max(ax,bx,cx)),0,W-1),y0=clamp(Math.floor(Math.min(ay,by,cy)),0,H-1),y1=clamp(Math.ceil(Math.max(ay,by,cy)),0,H-1);
  const h0=Math.abs(den)/Math.max(1e-6,Math.hypot(bx-cx,by-cy)),h1=Math.abs(den)/Math.max(1e-6,Math.hypot(ax-cx,ay-cy)),h2=Math.abs(den)/Math.max(1e-6,Math.hypot(ax-bx,ay-by));
  for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
   const u=((by-cy)*(x+.5-cx)+(cx-bx)*(y+.5-cy))/den,v=((cy-ay)*(x+.5-cx)+(ax-cx)*(y+.5-cy))/den,t=1-u-v;
   if(u<-.0001||v<-.0001||t<-.0001)continue;
   const dep=sz[a]*u+sz[b]*v+sz[c0]*t,k=y*W+x;if(dep<=zbuf[k])continue;zbuf[k]=dep;const o=k*4;
   if(mode===0){
    const tx=clamp((uv[2*a]*u+uv[2*b]*v+uv[2*c0]*t)*(texW-1),0,texW-1),ty=clamp((uv[2*a+1]*u+uv[2*b+1]*v+uv[2*c0+1]*t)*(texH-1),0,texH-1);
    const ix=Math.floor(tx),iy=Math.floor(ty),dx=tx-ix,dy=ty-iy,ix1=Math.min(ix+1,texW-1),iy1=Math.min(iy+1,texH-1);
    for(let j=0;j<3;j++)rgba[o+j]=(px[(iy*texW+ix)*4+j]*(1-dx)+px[(iy*texW+ix1)*4+j]*dx)*(1-dy)+(px[(iy1*texW+ix)*4+j]*(1-dx)+px[(iy1*texW+ix1)*4+j]*dx)*dy;
   }else{
    const q=light[a]*u+light[b]*v+light[c0]*t;
    if(mode===2&&Math.min(u*h0,v*h1,t*h2)<.65){rgba[o]=91;rgba[o+1]=139;rgba[o+2]=124;}
    else{rgba[o]=194*q;rgba[o+1]=199*q;rgba[o+2]=192*q;}
   }rgba[o+3]=255;
  }
 }
 ctx.putImageData(frame,0,0);
}
function requestRender(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;render()})}
for(const b of document.querySelectorAll('[data-mode]'))b.onclick=()=>{mode=Number(b.dataset.mode);for(const x of document.querySelectorAll('[data-mode]'))x.setAttribute('aria-pressed',String(x===b));requestRender()};
for(const b of document.querySelectorAll('[data-angle]'))b.onclick=()=>{angle=Number(b.dataset.angle)*Math.PI/180;tilt=0;requestRender()};
document.querySelector('#reset').onclick=()=>{angle=Math.PI/6;tilt=0;zoom=1;requestRender()};
let drag=null;canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId)});
canvas.addEventListener('pointermove',e=>{if(!drag)return;angle+=(e.clientX-drag[0])*.009;tilt=clamp(tilt+(e.clientY-drag[1])*.006,-.65,.65);drag=[e.clientX,e.clientY];requestRender()});
for(const type of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(type,()=>drag=null);
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=clamp(zoom*Math.exp(-e.deltaY*.001),.65,3);requestRender()},{passive:false});
canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','='].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')angle-=.15;if(e.key==='ArrowRight')angle+=.15;if(e.key==='ArrowUp')tilt=clamp(tilt+.1,-.65,.65);if(e.key==='ArrowDown')tilt=clamp(tilt-.1,-.65,.65);if(e.key==='+'||e.key==='=')zoom=Math.min(3,zoom*1.1);if(e.key==='-')zoom=Math.max(.65,zoom/1.1);requestRender()});
load().catch(fail);
