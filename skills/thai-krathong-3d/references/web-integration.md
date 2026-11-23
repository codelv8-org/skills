# Three.js / WebGL Integration

The `.glb` exported by this Skill is **glTF Y-up**, units **meters**. Krathong is centered at approximately X=Z=0, base at Y=0. The decorative flame is mesh-only; use a point light in the runtime if desired.

## Basic Three.js loader

```js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const world = new THREE.Scene();
const clock = new THREE.Clock();
let krathong;

loader.load('/assets/krathong.glb', ({ scene }) => {
  krathong = scene;
  world.add(scene);
});

function animate() {
  requestAnimationFrame(animate);
  if (krathong) {
    const t = clock.getElapsedTime();
    krathong.position.y = 0.007 * Math.sin(t * 1.3); // stylized float bob
    krathong.rotation.z = 0.018 * Math.sin(t * 0.7);
  }
  // renderer.render(world, camera); // configure renderer / camera separately
}
animate();
```

## Web release checklist

- Validate GLB using `scripts/qa_model.py`.
- Confirm material colors under **physically appropriate** light. A glTF baseColorFactor is not a calibrated photo texture.
- Test in at least one desktop browser and one target mobile device. Keep GLB in static assets; avoid server-side runtime generation for every client.
- Configure shadows only where necessary. Materials are matte by default (high roughness).
- Count draw calls in the browser: material groups commonly mean separate meshes/draw calls. Merge materials/meshes for crowds or dozens of instances, preserving a source copy for editability.
- Add `LOD` copies or lower-quality presets if using many simultaneous krathongs.
- Use `InstancedMesh` only for compatible repeated geometries with shared materials; a krathong with many separate groups is better batched off-line before instancing.
- Do not mistake decorative bobbing for physically correct floating. Use mass, water surface, center of buoyancy and collisions if a simulation requires physical realism.
- The legacy/sample baseline GLB is not a complete PBR bake. For a web release use the [R3.2 mesh/UV and baking workflow](mesh-uv-web-pbr.md) and load `krathong-web.glb`. It embeds sRGB BaseColor, Non-Color tangent Normal and packed ORM (R=AO, G=roughness, B=metallic). Retain GLTFLoader's imported material/texture settings.
