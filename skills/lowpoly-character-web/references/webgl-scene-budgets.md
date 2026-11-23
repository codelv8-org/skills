# Character assets for 3D WebApp / WebGL simulation

## Size, ratio, camera and intended use

All measurements are **planning targets**, not universal performance laws. Determine target device/GPU class, canvas dimensions, DPR, desired 30/60 FPS, target camera distance/FOV, other objects and effects, concurrent visible characters, desired independent animations, and scene density BEFORE choosing the mesh resolution. Character scale must be consistent with environment: choose a documented adult/creature height (e.g. ~1.7m if appropriate to the brief), glTF +Y up, feet at ground, root at 0, collider dimensions. Ratio is both anatomy and *apparent screen size*, not only triangle count.

## Report measured, estimated and untested quantities separately

At every approved or review-required stage, inspect the exported GLB and report its SHA-256, actual world bounds, triangle count, visible primitives, used materials, texture sizes and file bytes. A HEAD snapshot's numbers cover HEAD only; retain a separate provisional allocation for the remaining character. Verify glTF units against the declared character-height assumption and approved head/body ratio before considering a scaled export valid.

| Quantity | Evidence | Appropriate label |
|---|---|---|
| GLB bytes, decoded triangles/materials, world-space bounds | Exact current snapshot and inspector output | Measured asset statistics; state whether bounds use rest pose |
| Visible primitive submissions × actors, planned LOD allocation | `scene_budget.py`, scenario and visibility assumptions | Analytical estimate |
| Calls/triangles reported by a running renderer | Captured runtime counters with workload | Observed renderer statistics |
| FPS, frame percentiles, loading and animation update time | Timed run on named browser/hardware and exact GLB hash | Measured runtime; otherwise `NOT_TESTED` |

Compare revisions using the same cameras, actor count, resolution/DPR, animation and lighting. A lower triangle count alone does not prove faster rendering. Export the budget report beside the stage preview so the user can inspect both the shape change and its measured/estimated cost.

## Art-directed LOD budget defaults (per visible character)

| Rendering tier | When useful | Initial triangles | Primitive/draw starting cap | Distinct used materials | Animation path |
|---|---|---:|---:|---:|---|
| HERO / LOD0 | 1-3 prominent, >160px tall onscreen | <= 12,000 | <= 8 | <= 8 | Full rig, face/hands/equipment |
| NPC / LOD1 | ~10-30 visible, 60-160px | <= 5,000 | <= 4 | <= 4 | Simplified hands/details; full or reduced rig |
| CROWD / LOD2 | ~30-100 visible, 15-60px | <= 1,500 | <= 2 | <= 2 | Reduced bones/animation samples; consider batching |
| DISTANT / impostor | <15px, 100+ potential subjects | Justified only by scene | Ideally 1 shared draw path | shared | 2D impostor/billboard/batched animation or cull |

Values are **heuristics**. Screen-size thresholds use character projected pixel height and require hysteresis, switching based on camera and viewport (including DPR). If character expression is the focus on an HD monitor, use a higher tier. Do not degrade visual fidelity just to hit arbitrary caps: instead trade use-case requirements, choose fewer simultaneous detailed actors, or target stronger hardware.

**One hero-model per character is not a crowd asset.** Export separate LODs with matching root, bounds, pivot and animation meaning. Prefer hand-authored silhouette-friendly reductions: preserve large hairstyle planes, facial reading distance, bags and boots at their screen sizes; remove hands/fingers/badges from small far LOD. Verify mesh selection against zoomed-out preview.

## What actually costs frame time

- Base pass draw calls scale with the number of **visible primitives per character**, not just triangles. Each additional material/primitive can imply another draw. 17 primitives x 50 characters is about 850 primitive submissions *in a naive one-pass visibility scenario*; renderer calls can differ due to culling, shadows, batching and scene state.
- CPU time includes scene graph updates and per-character `AnimationMixer`, bone matrices and world transforms. GPU time includes vertex skinning, fragment shading, lights/shadows, overdraw, resolution and dynamic scene complexity. Network bytes and decode time are separate loading bottlenecks.
- A tiny `.glb` doesn't mean good runtime performance, nor does 1 Mesh automatically imply 1 draw call if it contains many material primitives.
- `THREE.InstancedMesh` is excellent for matching static geometry/material, **but does not automatically instance independently animated skeletal characters**. Correct clones use `SkeletonUtils.clone`, with per-character mixers and costs; scale to animation textures/GPU skinning/atlas/vertex animation only when implemented and tested. Do not claim plain InstancedMesh handles 100 different humanoid gaits.
- Merge primitive batches and use vertex colors/color atlas for repeatable palette when appropriate. Do **not** flatten or merge animated bones/skin away. Shared geometries/materials and texture atlases lower memory and state changes. Disable invisible accessories and costly shadows per distance/importance.
- Geometry compression (Meshopt/Draco) reduces transfers, not proportional frame compute. KTX2/Basis reduces GPU texture memory when supported. Preserve skeleton clips, node references, face winding and material appearance through optimization; ensure decoder support.

## Runtime QA: representative multi-character scene

1. Estimate distance-dependent apparent size with `scripts/projected_lod.py --height-m 1.7 --distances-m 2 5 10 20 40 --fov-vertical-deg 50 --viewport-css-height 900` (1.7m is only an example assumption, not an inference from art). Distances and threshold tiers are rough; apply bounds projection and hysteresis in actual viewer. Run `scripts/scene_budget.py character.glb --profile npc --instances 1 10 30 50 100 --json reports/scene_budget.json`. Report its figures as **estimated** primitive submissions, not actual draw calls or FPS.
2. Use `assets/crowd-benchmark/` or integrate the actual exported model into production Three.js scene. Record GPU model, browser, hardware, WebGL version, viewport size/DPR, lights/shadows, animation path, render loops and LOD scheme.
3. Test visible concurrent actor counts 1, 10, 30, 50, 100 (adjust to brief). Capture measured renderer.info.render.calls and triangles, FPS (mean and p95 frame duration), CPU/GPU profile when available, GLB load and GPU memory approximations.
4. Confirm all tested clips deform correctly in LOD0 and that LOD changes don't pop, lose bones, change height/root orientation, or alter front/back assets. Use camera walk-through and target mobile if included.
5. Optimize once, test again with **the same workload**; no optimization claim without before/after on a target device. Never mark `PERFORMANCE_PASS` without an actual benchmark; label it `NOT_TESTED` if browser unavailable.

For the prior Sentinel S3 exported GLB, structural data showed 9,134 tris, 17 primitives and 23 defined materials, including one skinned body and four clips. This was within the old 12k-triangle hero target but unsuitable to declare efficient for many NPCs without reducing render primitives and benchmarking.

## Technical references (verify version-specific details)

- Three.js InstancedMesh (static batching): https://threejs.org/docs/pages/InstancedMesh.html
- Three.js SkeletonUtils.clone: https://threejs.org/docs/pages/module-SkeletonUtils
- Three.js optimizing draw calls: https://threejs.org/manual/pages/optimize-lots-of-objects.html
- glTF-Transform: https://gltf-transform.dev/cli
- Blender Studio character retopology: https://studio.blender.org/training/realistic-human-research/retopology/
