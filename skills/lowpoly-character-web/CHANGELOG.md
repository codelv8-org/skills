# Changelog

## v4.1 — 2026-11-20

- Strengthened stage gates: decode real geometry payloads, reject invalid/blank/copied evidence, preserve mandatory criteria, validate finite review weights and distinct landmarks, and check scene reachability and non-degenerate triangles.
- Require explicit independent author/reviewer identities, with HUMAN and AI review distinguished. Bind approval to the current model, camera, thresholds, annotations and evidence bytes; re-evaluate saved PASS reports and block stale approvals.
- Keep approximate reference interpretations diagnostic; separate measured mask/landmark agreement from art review and never label either as a likeness percentage. Integration checks the actual final model and each accepted part's regression evidence.
- Added actual-GLB Blender stage rendering with provenance manifests and a static part-review web preview: reference/current/previous comparison, orbit/zoom, linked views, material/clay/wireframe, actual asset counts, and a labeled software fallback when WebGL is unavailable.
- Prevent output-path collisions with source models, assessments and evidence. State workflow and renderer verification limits explicitly.
- Focused verification: 27 affected gate tests passed and skill structure validation passed. Full legacy-suite coverage remains separate and environment-dependent.

## v4.0 — 2026-11-20

- **Head-first locked stage pipeline:** HEAD → TORSO → ARMS_HANDS → LEGS_FEET → OUTFIT_GEAR → INTEGRATION. Later stages are blocked until earlier hash-bound, visibly reviewed PASS.
- Added `scripts/stage_pipeline.py` with `init`, `evaluate`, `next`, `status` and integrated-part regression checks.
- Added `scripts/part_region_crop.py` to crop source/render using exactly the same region after global registration (no image-fit cheating).
- Added `scripts/part_fidelity.py`: per-view calibrated mask IoU, bbox/center/landmark checks, evidence-cited human feature ratings, and difference contact board.
- Added `references/part-by-part-studio.md`, `references/fidelity-measurement.md` and `references/quality-failure-playbook.md`; no fake likeness percentage and no source-mask/camera manipulation to improve scores.
- Retained v3 automatic WebGL preview, skin QA, LOD budgets and browser/crowd requirements. Prior Sentinel model is NOT silently deemed fixed.

## v3.0 — 2026-11-20

- **BREAKING QUALITY STANDARD:** Reference-matching four-view clay lock and human evidence-backed likeness review precede materials/rig. Marked failures must cause modeling revisions, not self-congratulatory GLB PASS.
- Added `scripts/reference_intake.py` for 4-column or independent image views; preserving originals and recording uncertain camera/scale, per-feature metadata and normalized landmark slots.
- Added `scripts/reference_review.py` for actual two-row four-view reference/model board plus scored review contract. Ratings/evidence are not generated automatically.
- Added `scripts/projected_lod.py` for perspective projected CSS-pixel height/LOD guidance with explicit metre/FOV assumptions.
- Added `scripts/scene_budget.py`, distinguishing real GLB primitive submissions from polygons and conservative Hero/NPC/Crowd planning caps, with multi-actor scenarios (not an FPS meter).
- Added `assets/crowd-benchmark/` Vite + Three.js example for measured 1/10/30/50/100 actors, clips, shadows, render draws, triangles and frame intervals; target browser test pending at point of packaging unless run on real GPU.
- Added `references/image-reference-pipeline.md`, `references/webgl-scene-budgets.md` and `references/acceptance-iteration.md` covering camera/landmark uncertainty, ratios/LOD, retopology art quality and explicit release terms.
- Preserved v2 skinned demo, GLB inspectors, preview generator, and continuous-mesh guidance; procedural demos explicitly remain prototypes.

## v2.0

- Skin-first humanoids; strict structural skin and animation checks; automatic generated WebGL preview site.
