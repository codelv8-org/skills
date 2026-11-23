/* Static, self-contained glTF 2.0 review renderer. No CDN/runtime dependencies.
 * Uses only selected-scene mesh instances, transformed vertices/normals, linear
 * COLOR_0/baseColorFactor, sRGB textures/output, metallic/roughness direct light.
 * Studio illumination is approximate (no IBL, shadows, or normal maps).
 * Unsupported skin/morph/compressed geometry fails visibly instead of lying.
 */
const IDENTITY = () => new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
const COMPONENTS = {5120: ['getInt8', 1], 5121: ['getUint8', 1], 5122: ['getInt16', 2], 5123: ['getUint16', 2], 5125: ['getUint32', 4], 5126: ['getFloat32', 4]};
const DIMS = {SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16};
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const sub = (a, b) => a.map((v, i) => v - b[i]);
const dot = (a, b) => a.reduce((sum, v, i) => sum + v * b[i], 0);
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const normalize = a => { const n = Math.hypot(...a) || 1; return a.map(x => x / n); };
const transformPoint = (m, x, y, z) => [m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14]];
function multiply(a, b) {
  const o = new Float32Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return o;
}
function compose(node) {
  if (node.matrix) return new Float32Array(node.matrix);
  const [x, y, z, w] = node.rotation || [0, 0, 0, 1], [sx, sy, sz] = node.scale || [1, 1, 1], t = node.translation || [0, 0, 0];
  const xx = x * x, yy = y * y, zz = z * z, xy = x * y, xz = x * z, yz = y * z, wx = w * x, wy = w * y, wz = w * z;
  return new Float32Array([(1 - 2 * yy - 2 * zz) * sx, 2 * (xy + wz) * sx, 2 * (xz - wy) * sx, 0, 2 * (xy - wz) * sy, (1 - 2 * xx - 2 * zz) * sy, 2 * (yz + wx) * sy, 0, 2 * (xz + wy) * sz, 2 * (yz - wx) * sz, (1 - 2 * xx - 2 * yy) * sz, 0, ...t, 1]);
}
function normalTransform(m) {
  const a = [m[0], m[1], m[2]], b = [m[4], m[5], m[6]], c = [m[8], m[9], m[10]];
  const bc = cross(b, c), ca = cross(c, a), ab = cross(a, b), det = dot(a, bc);
  if (Math.abs(det) < 1e-12) throw new Error('A mesh node has a non-invertible transform.');
  return {matrix: [...bc, ...ca, ...ab].map(x => x / det), mirrored: det < 0};
}
function lookAt(eye, center) {
  const z = normalize(sub(eye, center)), x = normalize(cross([0, 1, 0], z)), y = cross(z, x);
  return new Float32Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, eye), -dot(y, eye), -dot(z, eye), 1]);
}
function perspective(fov, aspect, near, far) {
  const f = 1 / Math.tan(fov / 2), a = new Float32Array(16);
  a[0] = f / aspect; a[5] = f; a[10] = (far + near) / (near - far); a[11] = -1; a[14] = 2 * far * near / (near - far); return a;
}
function orthographic(height, aspect, near, far) {
  const a = IDENTITY(); a[0] = 2 / (height * aspect); a[5] = 2 / height; a[10] = -2 / (far - near); a[14] = -(far + near) / (far - near); return a;
}
function cameraMatrices(scene, camera, width, height) {
  const c = camera, size = scene.bounds.size, extent = Math.max(...size, 0.001), aspect = width / height;
  const fitWidth = Math.abs(Math.cos(c.fitYaw)) * size[0] + Math.abs(Math.sin(c.fitYaw)) * size[2];
  const fitDepth = Math.abs(Math.sin(c.fitYaw)) * size[0] + Math.abs(Math.cos(c.fitYaw)) * size[2];
  const fitHeight = Math.abs(Math.cos(c.fitPitch)) * size[1] + Math.abs(Math.sin(c.fitPitch)) * fitDepth;
  const viewHeight = Math.max(fitHeight * 1.28, fitWidth * 1.16 / aspect) / c.zoom;
  const distance = c.projection === 'perspective' ? viewHeight / (2 * Math.tan(0.56 / 2)) : extent * 4;
  const eye = [c.target[0] + distance * Math.cos(c.pitch) * Math.sin(c.yaw), c.target[1] + distance * Math.sin(c.pitch), c.target[2] + distance * Math.cos(c.pitch) * Math.cos(c.yaw)];
  const near = Math.max(extent * 0.001, distance - extent * 3), far = distance + extent * 6;
  const projection = c.projection === 'perspective' ? perspective(0.56, aspect, near, far) : orthographic(viewHeight, aspect, near, far);
  return {vp: multiply(projection, lookAt(eye, c.target)), eye};
}

export function parseGLB(bytes) {
  if (bytes.byteLength < 20) throw new Error('GLB file is truncated.');
  const view = new DataView(bytes);
  if (view.getUint32(0, true) !== 0x46546c67 || view.getUint32(4, true) !== 2) throw new Error('Expected a binary glTF 2.0 (.glb) file.');
  if (view.getUint32(8, true) !== bytes.byteLength) throw new Error('GLB header length does not match the file.');
  let json = null, binary = null, offset = 12;
  while (offset < bytes.byteLength) {
    if (offset + 8 > bytes.byteLength) throw new Error('Truncated GLB chunk header.');
    const length = view.getUint32(offset, true), type = view.getUint32(offset + 4, true); offset += 8;
    if (length % 4 || offset + length > bytes.byteLength) throw new Error('Invalid GLB chunk length.');
    if (type === 0x4e4f534a) json = JSON.parse(new TextDecoder().decode(new Uint8Array(bytes, offset, length)));
    if (type === 0x004e4942) binary = bytes.slice(offset, offset + length);
    offset += length;
  }
  if (!json || !binary) throw new Error('GLB must contain JSON and a binary buffer.');
  if (json.asset?.version !== '2.0') throw new Error('Only glTF 2.0 is supported.');
  const required = (json.extensionsRequired || []).filter(x => x !== 'KHR_materials_unlit');
  if (required.length) throw new Error(`Unsupported required glTF extensions: ${required.join(', ')}.`);
  if ((json.buffers || []).some((b, i) => i > 0 || b.uri)) throw new Error('Use a self-contained GLB with one internal binary buffer.');
  return {json, binary, data: new DataView(binary), cache: new Map(), fileBytes: bytes.byteLength};
}

function normalized(value, type) {
  if (type === 5120) return Math.max(value / 127, -1);
  if (type === 5121) return value / 255;
  if (type === 5122) return Math.max(value / 32767, -1);
  if (type === 5123) return value / 65535;
  return value;
}
export function readAccessor(asset, index) {
  if (asset.cache.has(index)) return asset.cache.get(index);
  const a = asset.json.accessors?.[index], comp = COMPONENTS[a?.componentType], dim = DIMS[a?.type];
  if (!a || !comp || !dim || !Number.isSafeInteger(a.count) || a.count < 0) throw new Error(`Invalid accessor ${index}.`);
  if (a.count > 20_000_000) throw new Error('Accessor exceeds the review viewer budget.');
  const output = a.componentType === 5125 ? new Float64Array(a.count * dim) : new Float32Array(a.count * dim);
  function copy(viewIndex, byteOffset, count, dimensions, componentType, callback) {
    const bv = asset.json.bufferViews?.[viewIndex], [getter, size] = COMPONENTS[componentType];
    if (!bv || (bv.buffer ?? 0) !== 0) throw new Error('Accessor uses a missing or external bufferView.');
    const stride = bv.byteStride || dimensions * size, start = (bv.byteOffset || 0) + (byteOffset || 0);
    const end = start + Math.max(0, count - 1) * stride + (count ? dimensions * size : 0);
    if (end > asset.binary.byteLength || end > (bv.byteOffset || 0) + bv.byteLength) throw new Error('Accessor reads past its bufferView.');
    for (let i = 0; i < count; i++) for (let k = 0; k < dimensions; k++) callback(i, k, asset.data[getter](start + i * stride + k * size, true));
  }
  if (a.bufferView !== undefined) copy(a.bufferView, a.byteOffset, a.count, dim, a.componentType, (i, k, v) => { output[i * dim + k] = a.normalized ? normalized(v, a.componentType) : v; });
  if (a.sparse) {
    const s = a.sparse, indices = new Uint32Array(s.count);
    if (![5121, 5123, 5125].includes(s.indices.componentType)) throw new Error('Invalid sparse index component.');
    copy(s.indices.bufferView, s.indices.byteOffset, s.count, 1, s.indices.componentType, (i, k, v) => { if (v >= a.count) throw new Error('Sparse index is outside accessor.'); indices[i] = v; });
    copy(s.values.bufferView, s.values.byteOffset, s.count, dim, a.componentType, (i, k, v) => { output[indices[i] * dim + k] = a.normalized ? normalized(v, a.componentType) : v; });
  }
  asset.cache.set(index, output); return output;
}

function generateNormals(positions, indices) {
  const normals = new Float32Array(positions.length);
  for (let i = 0; i < indices.length; i += 3) {
    const a = indices[i] * 3, b = indices[i + 1] * 3, c = indices[i + 2] * 3;
    const n = cross(sub(Array.from(positions.subarray(b, b + 3)), positions.subarray(a, a + 3)), sub(Array.from(positions.subarray(c, c + 3)), positions.subarray(a, a + 3)));
    for (const vertex of [a, b, c]) for (let k = 0; k < 3; k++) normals[vertex + k] += n[k];
  }
  for (let i = 0; i < normals.length; i += 3) normals.set(normalize(Array.from(normals.subarray(i, i + 3))), i);
  return normals;
}
export function prepareScene(asset) {
  const doc = asset.json, nodes = doc.nodes || [], primitives = [], warnings = new Set();
  const bounds = {min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity]};
  const children = new Set(nodes.flatMap(n => n.children || []));
  const roots = doc.scenes?.[doc.scene ?? 0]?.nodes || nodes.map((_, i) => i).filter(i => !children.has(i));
  const visited = new Set(); let vertices = 0, triangles = 0;
  function visit(index, parent, path) {
    if (path.has(index)) throw new Error('Cycle in glTF scene hierarchy.');
    if (visited.has(index)) throw new Error('A node is used more than once in the selected scene.');
    visited.add(index); const node = nodes[index]; if (!node) throw new Error('Missing scene node.');
    const world = multiply(parent, compose(node)), next = new Set(path).add(index);
    if (node.mesh !== undefined) {
      if (node.skin !== undefined) throw new Error('This stage viewer needs an evaluated static export. Export the selected head with skin deformation applied.');
      const mesh = doc.meshes?.[node.mesh]; if (!mesh) throw new Error('Missing glTF mesh.');
      const nt = normalTransform(world);
      for (const p of mesh.primitives || []) {
        if ((p.mode ?? 4) !== 4) throw new Error('Stage review currently supports triangle primitives only.');
        if (p.targets?.length) throw new Error('Apply morph targets before exporting a static review GLB.');
        if (p.extensions?.KHR_draco_mesh_compression) throw new Error('Draco compressed geometry is not supported by this standalone viewer.');
        if (doc.accessors?.[p.attributes?.POSITION]?.type !== 'VEC3') throw new Error('Mesh POSITION must be VEC3.');
        const localPositions = readAccessor(asset, p.attributes.POSITION), count = localPositions.length / 3;
        const rawIndices = p.indices !== undefined ? readAccessor(asset, p.indices) : Array.from({length: count}, (_, i) => i);
        if (rawIndices.length % 3) throw new Error('Triangle indices are not a multiple of three.');
        let maxIndex = 0;
        for (const n of rawIndices) { if (!Number.isInteger(n) || n < 0 || n >= count) throw new Error('Mesh index is out of range.'); maxIndex = Math.max(maxIndex, n); }
        const IndexType = maxIndex <= 65535 ? Uint16Array : Uint32Array, indices = new IndexType(rawIndices);
        const localNormals = p.attributes.NORMAL !== undefined ? readAccessor(asset, p.attributes.NORMAL) : generateNormals(localPositions, indices);
        if (localNormals.length !== localPositions.length) throw new Error('NORMAL and POSITION counts differ.');
        const positions = new Float32Array(localPositions.length), normals = new Float32Array(localPositions.length);
        for (let i = 0; i < count; i++) {
          const at = i * 3, pos = transformPoint(world, localPositions[at], localPositions[at + 1], localPositions[at + 2]);
          if (pos.some(v => !Number.isFinite(v))) throw new Error('Mesh contains a non-finite transformed position.');
          positions.set(pos, at);
          for (let k = 0; k < 3; k++) { bounds.min[k] = Math.min(bounds.min[k], pos[k]); bounds.max[k] = Math.max(bounds.max[k], pos[k]); }
          const m = nt.matrix, x = localNormals[at], y = localNormals[at + 1], z = localNormals[at + 2];
          normals.set(normalize([m[0] * x + m[3] * y + m[6] * z, m[1] * x + m[4] * y + m[7] * z, m[2] * x + m[5] * y + m[8] * z]), at);
        }
        const colors = new Float32Array(count * 4).fill(1);
        if (p.attributes.COLOR_0 !== undefined) {
          const colorType = doc.accessors[p.attributes.COLOR_0].type, cd = DIMS[colorType], input = readAccessor(asset, p.attributes.COLOR_0);
          if (![3, 4].includes(cd) || input.length !== count * cd) throw new Error('COLOR_0 must have VEC3/VEC4 per vertex.');
          for (let i = 0; i < count; i++) for (let k = 0; k < cd; k++) colors[i * 4 + k] = input[i * cd + k];
        }
        const uv = p.attributes.TEXCOORD_0 !== undefined ? new Float32Array(readAccessor(asset, p.attributes.TEXCOORD_0)) : new Float32Array(count * 2);
        if (uv.length !== count * 2) throw new Error('TEXCOORD_0 count differs from POSITION.');
        const mat = p.material !== undefined ? doc.materials?.[p.material] || {} : {}, pbr = mat.pbrMetallicRoughness || {};
        const texInfo = pbr.baseColorTexture;
        if (texInfo && (texInfo.texCoord ?? 0) !== 0) throw new Error('Only TEXCOORD_0 base-color textures are supported.');
        if (texInfo?.extensions?.KHR_texture_transform) throw new Error('Bake the base-color texture transform for this review export.');
        if ((mat.alphaMode || 'OPAQUE') !== 'OPAQUE') throw new Error('Stage review requires opaque materials.');
        if (mat.normalTexture || mat.occlusionTexture || pbr.metallicRoughnessTexture || mat.emissiveTexture) warnings.add('Normal, occlusion, emissive, and metallic/roughness texture maps are not rendered; use baked vertex colors or scalar materials for this stage.');
        const edges = new Set(), edgeIndices = [];
        for (let i = 0; i < indices.length; i += 3) for (let j = 0; j < 3; j++) {
          const a = indices[i + j], b = indices[i + (j + 1) % 3], key = Math.min(a, b) + ':' + Math.max(a, b);
          if (!edges.has(key)) { edges.add(key); edgeIndices.push(a, b); }
        }
        primitives.push({positions, normals, colors, uv, indices, edgeIndices: new IndexType(edgeIndices), mirrored: nt.mirrored, doubleSided: !!mat.doubleSided,
          material: {base: pbr.baseColorFactor || [1, 1, 1, 1], metallic: pbr.metallicFactor ?? 1, roughness: pbr.roughnessFactor ?? 1, textureIndex: texInfo?.index, unlit: !!mat.extensions?.KHR_materials_unlit, emissive: mat.emissiveFactor || [0, 0, 0]}, name: mesh.name || node.name || 'Mesh'});
        vertices += count; triangles += indices.length / 3;
      }
    }
    for (const child of node.children || []) visit(child, world, next);
  }
  for (const root of roots) visit(root, IDENTITY(), new Set());
  if (!primitives.length || !Number.isFinite(bounds.min[0])) throw new Error('The selected glTF scene has no visible triangle geometry.');
  if (doc.animations?.length) warnings.add('Animation tracks are not played; this review uses the exported static node pose.');
  bounds.center = bounds.min.map((v, i) => (v + bounds.max[i]) / 2); bounds.size = sub(bounds.max, bounds.min);
  return {asset, primitives, bounds, stats: {triangles, vertices, primitives: primitives.length, fileBytes: asset.fileBytes}, warnings: [...warnings]};
}

const VERTEX_SHADER = `
precision highp float;
attribute vec3 aPosition;
attribute vec3 aNormal;
attribute vec4 aColor;
attribute vec2 aUV;
uniform mat4 uViewProjection;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec4 vColor;
varying vec2 vUV;
void main(){vNormal=aNormal;vPosition=aPosition;vColor=aColor;vUV=aUV;gl_Position=uViewProjection*vec4(aPosition,1.0);}`;
const FRAGMENT_SHADER = `
precision highp float;
varying vec3 vNormal;
varying vec3 vPosition;
varying vec4 vColor;
varying vec2 vUV;
uniform vec4 uBase;
uniform vec3 uEye;
uniform vec3 uEmissive;
uniform float uMetallic;
uniform float uRoughness;
uniform int uMode;
uniform bool uUnlit;
uniform bool uHasTexture;
uniform sampler2D uTexture;
const float PI=3.14159265;
vec3 srgbToLinear(vec3 c){return mix(c/12.92,pow((c+0.055)/1.055,vec3(2.4)),step(vec3(0.04045),c));}
vec3 linearToSrgb(vec3 c){c=max(c,vec3(0.0));return mix(c*12.92,1.055*pow(c,vec3(1.0/2.4))-0.055,step(vec3(0.0031308),c));}
vec3 fresnel(float cosTheta,vec3 f0){return f0+(1.0-f0)*pow(1.0-cosTheta,5.0);}
vec3 light(vec3 n,vec3 v,vec3 l,vec3 base,float metallic,float roughness,vec3 radiance){
  vec3 h=normalize(v+l);float nl=max(dot(n,l),0.0),nv=max(dot(n,v),0.001),nh=max(dot(n,h),0.0),hv=max(dot(h,v),0.0);
  float a=roughness*roughness,a2=a*a,den=nh*nh*(a2-1.0)+1.0;float d=a2/max(PI*den*den,0.0001);
  float k=(roughness+1.0)*(roughness+1.0)/8.0;float g=(nv/(nv*(1.0-k)+k))*(nl/(nl*(1.0-k)+k));
  vec3 f=fresnel(hv,mix(vec3(0.04),base,metallic));vec3 spec=d*g*f/max(4.0*nv*nl,0.001);
  return ((1.0-f)*(1.0-metallic)*base/PI+spec)*radiance*nl;
}
void main(){
  if(uMode==3){gl_FragColor=vec4(0.26,0.39,0.37,1.0);return;}
  vec3 base=uBase.rgb*vColor.rgb;
  if(uHasTexture)base*=srgbToLinear(texture2D(uTexture,vUV).rgb);
  float metallic=clamp(uMetallic,0.0,1.0),roughness=clamp(uRoughness,0.12,1.0);
  if(uMode==1){base=vec3(0.55,0.57,0.54);metallic=0.0;roughness=0.88;}
  if(uMode==2){base=vec3(0.71,0.76,0.72);metallic=0.0;roughness=1.0;}
  if(uUnlit&&uMode==0){gl_FragColor=vec4(linearToSrgb(base),1.0);return;}
  vec3 n=normalize(vNormal);if(!gl_FrontFacing)n=-n;vec3 v=normalize(uEye-vPosition);
  vec3 viewRight=normalize(cross(vec3(0.0,1.0,0.0),v));
  vec3 key=normalize(v*0.7-viewRight*0.55+vec3(0.0,0.85,0.0));
  vec3 fill=normalize(v*0.5+viewRight*0.8+vec3(0.0,0.1,0.0));
  vec3 radiance=base*(0.42+0.10*n.y)*(1.0-metallic)+mix(vec3(0.04),base,metallic)*0.14;
  radiance+=light(n,v,key,base,metallic,roughness,vec3(1.55,1.52,1.45));
  radiance+=light(n,v,fill,base,metallic,roughness,vec3(0.52,0.59,0.62));
  if(uMode==0)radiance+=uEmissive;
  gl_FragColor=vec4(linearToSrgb(radiance),1.0);
}`;

export class StaticGLBViewer {
  constructor(canvas, {onChange = () => {}, onError = () => {}, presets = {front: 0, right: 90, back: 180, left: -90, three: -35}} = {}) {
    this.canvas = canvas; this.onChange = onChange; this.onError = onError; this.presets = presets;
    this.gl = canvas.getContext('webgl2', {alpha: true, antialias: true, preserveDrawingBuffer: true}) || canvas.getContext('webgl', {alpha: true, antialias: true, preserveDrawingBuffer: true});
    if (!this.gl) throw new Error('WebGL ไม่พร้อมใช้งานในเบราว์เซอร์นี้ โปรดดูภาพเรนเดอร์นิ่งหรือดาวน์โหลด GLB');
    this.webgl2 = typeof WebGL2RenderingContext !== 'undefined' && this.gl instanceof WebGL2RenderingContext;
    this.uint32 = this.webgl2 || this.gl.getExtension('OES_element_index_uint');
    this.engine = this.webgl2 ? 'WebGL 2' : 'WebGL 1'; this.scene = null; this.resources = []; this.textures = new Map(); this.mode = 'material';
    this.camera = {yaw: 0, pitch: 0, fitYaw: 0, fitPitch: 0, zoom: 1, projection: 'orthographic', view: 'front', target: [0, 0, 0]};
    this.qa = {loaded: false, frames: 0, draws: 0, errors: [], webglError: 0, engine: this.engine, softwareFallback: false, gpuVerified: false};
    this.drawPending = false; this.program = this.makeProgram(); this.locations = {};
    const gl = this.gl;
    for (const name of ['uViewProjection', 'uBase', 'uEye', 'uEmissive', 'uMetallic', 'uRoughness', 'uMode', 'uUnlit', 'uHasTexture', 'uTexture']) this.locations[name] = gl.getUniformLocation(this.program, name);
    this.attributes = ['aPosition', 'aNormal', 'aColor', 'aUV'].map(name => gl.getAttribLocation(this.program, name));
    this.whiteTexture = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, this.whiteTexture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([255, 255, 255, 255]));
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.enable(gl.DEPTH_TEST); gl.depthFunc(gl.LEQUAL); gl.clearColor(0, 0, 0, 0);
    this.bindControls(); this.resizeObserver = new ResizeObserver(() => this.requestDraw()); this.resizeObserver.observe(canvas);
    canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); this.qa.loaded = false; this.onError(new Error('WebGL context was lost. Reload the page to restore the 3D view.')); });
  }
  makeProgram() {
    const gl = this.gl;
    const compile = (kind, source) => {
      if (this.webgl2) {
        source = '#version 300 es\n' + source;
        if (kind === gl.VERTEX_SHADER) source = source.replaceAll('attribute ', 'in ').replaceAll('varying ', 'out ');
        else source = source.replaceAll('varying ', 'in ').replace('precision highp float;', 'precision highp float;\nout vec4 fragmentColor;').replaceAll('texture2D(', 'texture(').replaceAll('gl_FragColor', 'fragmentColor');
      }
      const s = gl.createShader(kind); gl.shaderSource(s, source); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { const message = gl.getShaderInfoLog(s); gl.deleteShader(s); throw new Error(message); } return s;
    };
    const p = gl.createProgram(), vs = compile(gl.VERTEX_SHADER, VERTEX_SHADER), fs = compile(gl.FRAGMENT_SHADER, FRAGMENT_SHADER);
    gl.attachShader(p, vs); gl.attachShader(p, fs); gl.linkProgram(p); gl.deleteShader(vs); gl.deleteShader(fs);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p)); return p;
  }
  async makeTexture(asset, index) {
    const gl = this.gl, texture = asset.json.textures?.[index], source = asset.json.images?.[texture?.source];
    if (!source) throw new Error('Missing embedded base-color image.');
    let blob;
    if (source.bufferView !== undefined) { const bv = asset.json.bufferViews[source.bufferView]; blob = new Blob([asset.binary.slice(bv.byteOffset || 0, (bv.byteOffset || 0) + bv.byteLength)], {type: source.mimeType || 'image/png'}); }
    else if (source.uri?.startsWith('data:')) blob = await (await fetch(source.uri)).blob();
    else throw new Error('Base-color image must be embedded in the GLB.');
    const bitmap = await createImageBitmap(blob, {imageOrientation: 'none', premultiplyAlpha: 'none', colorSpaceConversion: 'none'});
    const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, bitmap);
    const sampler = asset.json.samplers?.[texture.sampler] || {}, powerOfTwo = n => (n & (n - 1)) === 0;
    const mipmaps = this.webgl2 || (powerOfTwo(bitmap.width) && powerOfTwo(bitmap.height));
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, mipmaps ? sampler.wrapS || gl.REPEAT : gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, mipmaps ? sampler.wrapT || gl.REPEAT : gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, sampler.magFilter || gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, mipmaps ? sampler.minFilter || gl.LINEAR_MIPMAP_LINEAR : gl.LINEAR);
    if (mipmaps) gl.generateMipmap(gl.TEXTURE_2D); bitmap.close(); return tex;
  }
  async loadBytes(bytes, {preserveView = false} = {}) {
    const scene = prepareScene(parseGLB(bytes)), gl = this.gl, newTextures = new Map(), resources = [];
    for (const p of scene.primitives) if (p.material.textureIndex !== undefined && !newTextures.has(p.material.textureIndex)) newTextures.set(p.material.textureIndex, await this.makeTexture(scene.asset, p.material.textureIndex));
    try {
      for (const p of scene.primitives) {
        if (p.indices instanceof Uint32Array && !this.uint32) throw new Error('This browser cannot draw 32-bit mesh indices.');
        const buffers = [p.positions, p.normals, p.colors, p.uv].map(array => { const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, array, gl.STATIC_DRAW); return b; });
        const ibo = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ibo); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, p.indices, gl.STATIC_DRAW);
        const edgeIbo = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, edgeIbo); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, p.edgeIndices, gl.STATIC_DRAW);
        resources.push({...p, buffers, ibo, edgeIbo, indexType: p.indices instanceof Uint32Array ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT});
      }
    } catch (error) { for (const r of resources) for (const b of [...r.buffers, r.ibo, r.edgeIbo]) gl.deleteBuffer(b); for (const t of newTextures.values()) gl.deleteTexture(t); throw error; }
    for (const r of this.resources) for (const b of [...r.buffers, r.ibo, r.edgeIbo]) gl.deleteBuffer(b);
    for (const t of this.textures.values()) gl.deleteTexture(t);
    this.resources = resources; this.textures = newTextures; this.scene = scene; this.camera.target = [...scene.bounds.center];
    if (!preserveView) { this.camera.zoom = 1; this.setPreset('front'); }
    this.qa.loaded = true; this.qa.stats = scene.stats; this.qa.bounds = scene.bounds; this.qa.warnings = scene.warnings;
    this.requestDraw(); this.notify(); return scene;
  }
  setPreset(view) { if (this.presets[view] === undefined) return; this.camera.yaw = this.presets[view] * Math.PI / 180; this.camera.pitch = view === 'three' ? 0.09 : 0; this.camera.fitYaw = this.camera.yaw; this.camera.fitPitch = this.camera.pitch; this.camera.view = view; this.camera.projection = view === 'three' ? 'perspective' : 'orthographic'; this.requestDraw(); this.notify(); }
  setMode(mode) { this.mode = mode; this.requestDraw(); this.notify(); }
  zoom(factor) { this.camera.zoom = clamp(this.camera.zoom * factor, 0.45, 3.5); this.requestDraw(); this.notify(); }
  fit() { this.camera.zoom = 1; this.camera.fitYaw = this.camera.yaw; this.camera.fitPitch = this.camera.pitch; if (this.scene) this.camera.target = [...this.scene.bounds.center]; this.requestDraw(); this.notify(); }
  notify() { this.qa.camera = {...this.camera, target: [...this.camera.target]}; this.qa.mode = this.mode; this.onChange(this); }
  requestDraw() { if (this.drawPending) return; this.drawPending = true; requestAnimationFrame(() => { this.drawPending = false; try { this.draw(); } catch (error) { this.qa.errors.push(String(error)); this.onError(error); } }); }
  draw() {
    const gl = this.gl, canvas = this.canvas, dpr = Math.min(devicePixelRatio || 1, 2), rect = canvas.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width * dpr)), height = Math.max(1, Math.floor(rect.height * dpr));
    if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
    gl.viewport(0, 0, width, height); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); if (!this.scene) return;
    const {vp, eye} = cameraMatrices(this.scene, this.camera, width, height);
    gl.useProgram(this.program); gl.uniformMatrix4fv(this.locations.uViewProjection, false, vp); gl.uniform3fv(this.locations.uEye, eye);
    const mode = this.mode === 'clay' ? 1 : this.mode === 'wireframe' ? 2 : 0;
    let draws = 0;
    for (const r of this.resources) {
      for (let i = 0; i < r.buffers.length; i++) { const location = this.attributes[i]; if (location < 0) continue; gl.bindBuffer(gl.ARRAY_BUFFER, r.buffers[i]); gl.enableVertexAttribArray(location); gl.vertexAttribPointer(location, [3, 3, 4, 2][i], gl.FLOAT, false, 0, 0); }
      if (r.doubleSided) gl.disable(gl.CULL_FACE); else gl.enable(gl.CULL_FACE);
      gl.frontFace(r.mirrored ? gl.CW : gl.CCW);
      gl.uniform4fv(this.locations.uBase, r.material.base); gl.uniform3fv(this.locations.uEmissive, r.material.emissive); gl.uniform1f(this.locations.uMetallic, r.material.metallic); gl.uniform1f(this.locations.uRoughness, r.material.roughness); gl.uniform1i(this.locations.uUnlit, r.material.unlit); gl.uniform1i(this.locations.uMode, mode);
      const tex = this.textures.get(r.material.textureIndex); gl.uniform1i(this.locations.uHasTexture, !!tex); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex || this.whiteTexture); gl.uniform1i(this.locations.uTexture, 0);
      if (mode === 2) { gl.enable(gl.POLYGON_OFFSET_FILL); gl.polygonOffset(1, 1); }
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, r.ibo); gl.drawElements(gl.TRIANGLES, r.indices.length, r.indexType, 0); draws++;
      if (mode === 2) { gl.disable(gl.POLYGON_OFFSET_FILL); gl.uniform1i(this.locations.uMode, 3); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, r.edgeIbo); gl.depthMask(false); gl.drawElements(gl.LINES, r.edgeIndices.length, r.indexType, 0); gl.depthMask(true); draws++; }
    }
    this.qa.frames++; this.qa.draws = draws; this.qa.webglError = gl.getError();
    if (this.qa.webglError) throw new Error(`WebGL draw error ${this.qa.webglError}.`);
    this.qa.gpuVerified = true;
  }
  bindControls() {
    const pointers = new Map(), canvas = this.canvas;
    let lastPinch = null;
    const touchDistance = () => { const p = [...pointers.values()]; return p.length < 2 ? null : Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); };
    canvas.addEventListener('pointerdown', e => { if (e.button !== 0) return; pointers.set(e.pointerId, {x: e.clientX, y: e.clientY}); canvas.setPointerCapture(e.pointerId); lastPinch = touchDistance(); canvas.focus({preventScroll: true}); });
    canvas.addEventListener('pointermove', e => {
      const previous = pointers.get(e.pointerId); if (!previous) return;
      const dx = e.clientX - previous.x, dy = e.clientY - previous.y; pointers.set(e.pointerId, {x: e.clientX, y: e.clientY});
      if (pointers.size > 1) { const pinch = touchDistance(); if (lastPinch && pinch) this.zoom(pinch / lastPinch); lastPinch = pinch; }
      else { this.camera.yaw -= dx * 0.007; this.camera.pitch = clamp(this.camera.pitch + dy * 0.006, -1.40, 1.40); this.camera.view = 'free'; this.requestDraw(); this.notify(); }
    });
    const release = e => { pointers.delete(e.pointerId); lastPinch = touchDistance(); };
    canvas.addEventListener('pointerup', release); canvas.addEventListener('pointercancel', release); canvas.addEventListener('lostpointercapture', release);
    canvas.addEventListener('wheel', e => { e.preventDefault(); this.zoom(Math.exp(-e.deltaY * 0.001)); }, {passive: false});
    canvas.addEventListener('keydown', e => {
      const views = {'1': 'front', '2': 'right', '3': 'back', '4': 'left', '5': 'three'};
      if (views[e.key]) { this.setPreset(views[e.key]); e.preventDefault(); return; }
      if (['+', '='].includes(e.key)) this.zoom(1.1);
      else if (['-', '_'].includes(e.key)) this.zoom(1 / 1.1);
      else if (e.key === 'Home') this.fit();
      else if (e.key.startsWith('Arrow')) { const step = e.shiftKey ? 0.25 : 0.09; if (e.key === 'ArrowLeft') this.camera.yaw -= step; if (e.key === 'ArrowRight') this.camera.yaw += step; if (e.key === 'ArrowUp') this.camera.pitch = clamp(this.camera.pitch + step, -1.4, 1.4); if (e.key === 'ArrowDown') this.camera.pitch = clamp(this.camera.pitch - step, -1.4, 1.4); this.camera.view = 'free'; this.requestDraw(); this.notify(); }
      else return;
      e.preventDefault();
    });
  }
}

/* Clip before the perspective divide. This keeps triangles crossing the near
 * plane finite, while retaining the same six clip planes as the WebGL path. */
function clipSoftwareTriangle(vertices) {
  let polygon = vertices;
  for (const [axis, sign] of [[0, 1], [0, -1], [1, 1], [1, -1], [2, 1], [2, -1]]) {
    if (!polygon.length) break;
    const output = [];
    let previous = polygon[polygon.length - 1], previousDistance = previous[3] + sign * previous[axis];
    for (const current of polygon) {
      const currentDistance = current[3] + sign * current[axis];
      if ((previousDistance >= 0) !== (currentDistance >= 0)) {
        const t = previousDistance / (previousDistance - currentDistance);
        output.push(previous.map((v, k) => v + (current[k] - v) * t));
      }
      if (currentDistance >= 0) output.push(current);
      previous = current; previousDistance = currentDistance;
    }
    polygon = output;
  }
  return polygon;
}

/* Keep projection/rasterization independent of the DOM so opaque occlusion can
 * be checked against analytic intersections, including reversed submission
 * order. Depth is NDC z, which interpolates linearly in screen space. */
export function projectSoftwareTriangles(scene, camera, width, height, mode = 'material') {
  const {vp, eye} = cameraMatrices(scene, camera, width, height), triangles = [];
  const srgb = x => Math.round(clamp(x <= 0.0031308 ? x * 12.92 : 1.055 * Math.pow(Math.max(0, x), 1 / 2.4) - 0.055, 0, 1) * 255);
  for (const primitive of scene.primitives) {
    const p = primitive.positions, n = primitive.normals, colors = primitive.colors, count = p.length / 3, clips = new Float64Array(count * 4);
    for (let i = 0; i < count; i++) {
      const at = i * 3, out = i * 4, x = p[at], y = p[at + 1], z = p[at + 2];
      for (let k = 0; k < 4; k++) clips[out + k] = vp[k] * x + vp[4 + k] * y + vp[8 + k] * z + vp[12 + k];
    }
    for (let i = 0; i < primitive.indices.length; i += 3) {
      const ia = primitive.indices[i], ib = primitive.indices[i + 1], ic = primitive.indices[i + 2], a = ia * 3, b = ib * 3, c = ic * 3;
      const center = [0, 1, 2].map(k => (p[a + k] + p[b + k] + p[c + k]) / 3), view = normalize(sub(eye, center));
      const faceNormal = cross([p[b] - p[a], p[b + 1] - p[a + 1], p[b + 2] - p[a + 2]], [p[c] - p[a], p[c + 1] - p[a + 1], p[c + 2] - p[a + 2]]);
      const front = dot(faceNormal, view) * (primitive.mirrored ? -1 : 1) > 0;
      if (!front && !primitive.doubleSided) continue;
      const clipped = clipSoftwareTriangle([ia, ib, ic].map(index => Array.from(clips.subarray(index * 4, index * 4 + 4))));
      if (clipped.length < 3) continue;
      let normal = normalize([0, 1, 2].map(k => n[a + k] + n[b + k] + n[c + k]));
      if (!front) normal = normal.map(v => -v);
      const right = normalize(cross([0, 1, 0], view));
      const key = normalize(view.map((v, k) => v * 0.7 - right[k] * 0.55 + (k === 1 ? 0.85 : 0)));
      const fill = normalize(view.map((v, k) => v * 0.5 + right[k] * 0.8 + (k === 1 ? 0.1 : 0)));
      const light = 0.42 + normal[1] * 0.1 + Math.max(0, dot(normal, key)) * 0.50 + Math.max(0, dot(normal, fill)) * 0.18;
      let rgb;
      if (mode === 'clay') rgb = [0.55, 0.57, 0.54].map(v => srgb(v * light));
      else if (mode === 'wireframe') rgb = [0.71, 0.76, 0.72].map(v => srgb(v * light));
      else rgb = [0, 1, 2].map(k => srgb(primitive.material.base[k] * (colors[ia * 4 + k] + colors[ib * 4 + k] + colors[ic * 4 + k]) / 3 * (primitive.material.unlit ? 1 : light) + primitive.material.emissive[k]));
      const projected = clipped.map(v => [(0.5 + v[0] / v[3] * 0.5) * width, (0.5 - v[1] / v[3] * 0.5) * height, v[2] / v[3]]);
      for (let k = 1; k < projected.length - 1; k++) triangles.push({points: [projected[0], projected[k], projected[k + 1]], color: rgb});
    }
  }
  return triangles;
}

export function rasterizeSoftwareTriangles(triangles, width, height, {wireframe = false, lineWidth = 1, target = null} = {}) {
  const count = width * height;
  if (!target || target.width !== width || target.height !== height) target = {width, height, data: new Uint8ClampedArray(count * 4), depth: new Float32Array(count)};
  const pixels = target.data, depth = target.depth;
  pixels.fill(0); depth.fill(Infinity);
  let submitted = 0;
  const edge = (a, b, x, y) => (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]);
  for (const triangle of triangles) {
    let [a, b, c] = triangle.points;
    if ([...a, ...b, ...c].some(v => !Number.isFinite(v))) continue;
    let area = edge(a, b, c[0], c[1]);
    if (Math.abs(area) < 1e-8) continue;
    if (area < 0) { [b, c] = [c, b]; area = -area; }
    const minX = Math.max(0, Math.ceil(Math.min(a[0], b[0], c[0]) - 0.5)), maxX = Math.min(width - 1, Math.floor(Math.max(a[0], b[0], c[0]) - 0.5));
    const minY = Math.max(0, Math.ceil(Math.min(a[1], b[1], c[1]) - 0.5)), maxY = Math.min(height - 1, Math.floor(Math.max(a[1], b[1], c[1]) - 0.5));
    if (minX > maxX || minY > maxY) continue;
    submitted++;
    const dx0 = b[1] - c[1], dy0 = c[0] - b[0], dx1 = c[1] - a[1], dy1 = a[0] - c[0], dx2 = a[1] - b[1], dy2 = b[0] - a[0];
    let row0 = edge(b, c, minX + 0.5, minY + 0.5), row1 = edge(c, a, minX + 0.5, minY + 0.5), row2 = edge(a, b, minX + 0.5, minY + 0.5);
    const az = a[2] / area, bz = b[2] / area, cz = c[2] / area;
    const dzX = dx0 * az + dx1 * bz + dx2 * cz, dzY = dy0 * az + dy1 * bz + dy2 * cz;
    let rowZ = row0 * az + row1 * bz + row2 * cz;
    const halfLine = lineWidth * 0.5, edge0 = Math.hypot(dx0, dy0) * halfLine, edge1 = Math.hypot(dx1, dy1) * halfLine, edge2 = Math.hypot(dx2, dy2) * halfLine;
    const [red, green, blue] = triangle.color;
    const wireRed = Math.round(red * 0.22 + 56 * 0.78), wireGreen = Math.round(green * 0.22 + 90 * 0.78), wireBlue = Math.round(blue * 0.22 + 79 * 0.78);
    for (let y = minY; y <= maxY; y++) {
      let e0 = row0, e1 = row1, e2 = row2, z = rowZ, pixel = y * width + minX;
      for (let x = minX; x <= maxX; x++, pixel++, e0 += dx0, e1 += dx1, e2 += dx2, z += dzX) {
        if (e0 < -1e-7 || e1 < -1e-7 || e2 < -1e-7 || z < -1.000001 || z > 1.000001 || z >= depth[pixel]) continue;
        depth[pixel] = z;
        const wire = wireframe && (e0 <= edge0 || e1 <= edge1 || e2 <= edge2), offset = pixel * 4;
        pixels[offset] = wire ? wireRed : red; pixels[offset + 1] = wire ? wireGreen : green; pixels[offset + 2] = wire ? wireBlue : blue; pixels[offset + 3] = 255;
      }
      row0 += dy0; row1 += dy1; row2 += dy2; rowZ += dzY;
    }
  }
  target.submittedTriangles = submitted;
  return target;
}

/* Real software 3D for browsers without WebGL: the same GLB/scene/accessor code,
 * camera matrices and clip volume, with opaque per-pixel depth testing. Wire
 * color is applied only to the nearest triangle, so hidden edges stay hidden.
 * Flat lighting is approximate; this never certifies GPU/PBR/performance. */
export class SoftwareGLBViewer {
  constructor(canvas, {onChange = () => {}, onError = () => {}, presets = {front: 0, right: 90, back: 180, left: -90, three: -35}, fallbackReason = ''} = {}) {
    this.context = canvas.getContext('2d', {alpha: true});
    if (!this.context) {
      const fresh = canvas.cloneNode(false); canvas.replaceWith(fresh); canvas = fresh;
      this.context = canvas.getContext('2d', {alpha: true});
    }
    if (!this.context) throw new Error('ไม่พบทั้ง WebGL และ Canvas 2D กรุณาเปิดภาพเรนเดอร์นิ่งหรือดาวน์โหลด GLB');
    this.canvas = canvas; this.onChange = onChange; this.onError = onError; this.presets = presets;
    this.engine = 'Software 3D'; this.scene = null; this.mode = 'material'; this.drawPending = false;
    this.camera = {yaw: 0, pitch: 0, fitYaw: 0, fitPitch: 0, zoom: 1, projection: 'orthographic', view: 'front', target: [0, 0, 0]};
    this.qa = {loaded: false, frames: 0, draws: 0, errors: [], webglError: null, engine: this.engine, softwareFallback: true, gpuVerified: false, webglUnavailableReason: fallbackReason,
      depthBuffer: true, occlusion: 'per-pixel-depth-buffer', wireframeOcclusion: 'per-pixel-depth-buffer',
      renderLimitations: ['Flat per-triangle vertex-color lighting; no textures or GPU PBR', 'Software preview does not validate WebGL or target-device performance']};
    this.bindControls(); this.resizeObserver = new ResizeObserver(() => this.requestDraw()); this.resizeObserver.observe(canvas);
  }
  async loadBytes(bytes, {preserveView = false} = {}) {
    const scene = prepareScene(parseGLB(bytes));
    if (scene.primitives.some(p => p.material.textureIndex !== undefined)) throw new Error('Software 3D รองรับ vertex colors และสีวัสดุเท่านั้น โมเดลที่ใช้ texture ต้องเปิดด้วย WebGL');
    this.scene = scene; this.camera.target = [...scene.bounds.center];
    if (!preserveView) { this.camera.zoom = 1; this.setPreset('front'); }
    scene.warnings.push('Software 3D: per-pixel depth testing for opaque faces and wireframe, with approximate flat lighting. WebGL has not been tested in this browser; GPU/PBR/performance approval is not implied.');
    this.qa.loaded = true; this.qa.stats = scene.stats; this.qa.bounds = scene.bounds; this.qa.warnings = scene.warnings;
    this.requestDraw(); this.notify(); return scene;
  }
  draw() {
    const canvas = this.canvas, ctx = this.context, rect = canvas.getBoundingClientRect();
    const scale = Math.min(Math.max(devicePixelRatio || 1, 1.25), 2, 1000 / Math.max(rect.width, rect.height, 1), Math.sqrt(650000 / Math.max(rect.width * rect.height, 1)));
    const width = Math.max(1, Math.floor(rect.width * scale)), height = Math.max(1, Math.floor(rect.height * scale));
    if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; this.rasterTarget = null; }
    if (!this.scene) { ctx.clearRect(0, 0, width, height); return; }
    if (!this.rasterTarget) {
      this.frameImage = ctx.createImageData(width, height);
      this.rasterTarget = {width, height, data: this.frameImage.data, depth: new Float32Array(width * height)};
    }
    const triangles = projectSoftwareTriangles(this.scene, this.camera, width, height, this.mode);
    rasterizeSoftwareTriangles(triangles, width, height, {wireframe: this.mode === 'wireframe', lineWidth: Math.max(1, scale), target: this.rasterTarget});
    ctx.putImageData(this.frameImage, 0, 0);
    this.qa.frames++; this.qa.draws = this.scene.stats.primitives;
    this.qa.submittedTriangles = this.rasterTarget.submittedTriangles; this.qa.rasterResolution = [width, height];
  }
}
for (const method of ['setPreset', 'setMode', 'zoom', 'fit', 'notify', 'requestDraw', 'bindControls']) SoftwareGLBViewer.prototype[method] = StaticGLBViewer.prototype[method];

export function createStageViewer(canvas, options = {}) {
  try { return new StaticGLBViewer(canvas, options); }
  catch (error) { return new SoftwareGLBViewer(canvas, {...options, fallbackReason: error?.message || String(error)}); }
}
