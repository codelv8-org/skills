# Crowd performance benchmark (Vite + Three.js)

This is a **target-device benchmark**, not a guaranteed FPS chart. Clone real SkinnedMeshes correctly with `SkeletonUtils.clone`, render a grid of 1/10/30/50/100 characters, and report draw calls, triangles and browser frame times. This deliberately uses distinct skeletons/mixers for independently posed characters; ordinary `THREE.InstancedMesh` does not automatically offer per-instance SkinnedMesh animation.

1. Copy the exported model into `public/model.glb`.
2. `npm install`
3. `npm run dev` (open local URL)
4. Select same camera, lighting and shadows as production scene as far as practical; select animation; press **Export 10s reading** at each population. Record renderer, browser/OS, device, resolution, pixel ratio, shadows, active clips, memory where observable and screenshots.
5. Repeat on mid-range mobile and target desktops. If WebGL unavailable, mark `BROWSER_NOT_TESTED`; the static `scene_budget.py` report does not replace this.

**Limits:** The example intentionally does not have frustum culling tuning, hardware animation instancing, LOD, effects or navmesh. Use it to establish a baseline. Compare quality/perf against an optimized candidate; DO NOT say it guarantees 30 or 60 FPS. Shader compile/first-load is separate from warmed-up frame time. The ``frame_ms`` fields measure JS render-call elapsed time, not GPU time or inter-frame FPS; use browser profiling tools for accurate end-to-end FPS and GPU timing.
