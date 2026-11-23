# Low-poly Character Web Studio v4.1

A reusable ChatGPT skill for reference-driven, quality-gated low-poly character modeling and WebGL simulation. Primary focus is **actual visual fidelity**, reliable skinned deformation and measured multi-character performance — not only a file with a passing GLB parser.

## Improvements over v2

1. Reference sheet intake: four panel cropping or independent front/back/left/right, source checksum, camera/scale uncertainties, per-feature prioritized checklist and normalized landmark slots.
2. Mandatory reference-vs-model four-view board + **evidence-backed independent review**. Identify the reviewer as HUMAN or AI; AI review is never human approval. A generated scorecard starts NOT_TESTED; no similarity score is fabricated.
3. Geometry method selection: favor fitted topology/sculpt/retopo for fidelity; forbid declaring general SDF/marching-cubes or detached primitives final-quality human geometry without artistic corrections.
4. Web use profile: world metre scale, screen pixel size, hero/NPC/crowd LOD tiers, per-asset primitive/material caps, physically consistent character/collider proportions.
5. Scale and LOD planning from physical character height, camera FOV and approximate CSS screen pixels (`projected_lod.py`); scene-aware GLB budget analysis with 1/10/30/50/100 characters — **analytical estimates only**. Separate actual Three.js benchmark harness to record browser metrics.
6. Continue v2 real GLB, skinning inspector, clips and runnable offline-capable preview; preserve original scripts/reference materials.

### Quickstart

```bash
pip install Pillow numpy trimesh
python scripts/reference_intake.py reference.png --layout four-columns --out project/references
# Model in Blender (or other real tool); export glTF GLB; create four matched camera renders.
python scripts/reference_review.py --ref project/references --renders project/renders --board project/reference_check.png --new-scorecard project/reference_scorecard.json
python scripts/inspect_character_glb.py project/export/character.glb --profile hero --json project/reports/structure.json
python scripts/scene_budget.py project/export/character.glb --profile npc --json project/reports/scene_budget.json
python scripts/build_preview_site.py project/export/character.glb --out project/preview
```

`assets/crowd-benchmark/` needs `npm install` then `npm run dev`; copy the actual model into its `public/model.glb`. The benchmark needs a real WebGL browser and target device. Note that a missing Blender executable means no `.blend` or manual retopology can be claimed from this skill bundle alone.

### Critical warnings

- Validation only proves specific technical properties, not appearance or faithful 3D reconstruction.
- A four-view illustration may not be a calibrated orthographic scan.
- Per-NPC triangle count is not sufficient to guarantee scene performance. Draw calls, materials, skeleton updates, shadows, VRAM and animation count matter.
- Performance profile caps are initial **design heuristics**, not measured FPS guarantees.

See `SKILL.md` for mandatory gates; `references/` for image intake, ratios, QA and LOD, and `scripts/` for tested utilities.

## v4.1 staged visual acceptance

Run `python scripts/stage_pipeline.py init --out character_project --reference-dir reference_pack` before modeling. Start at HEAD, deliver actual exported model and registered masks, then call `evaluate --stage HEAD`. TORSO cannot start until HEAD PASS. See `references/part-by-part-studio.md` and `references/fidelity-measurement.md`. This is a process+QA upgrade, not an automatic 2D-to-3D sculptor.

Review approval binds the actual model, camera configuration, thresholds, landmarks and evidence bytes. Re-evaluation checks those inputs again; an edited PASS file or old approval cannot unlock later stages. Approximate concept-sheet cameras remain diagnostic until the correspondence or a documented accepted design interpretation is resolved. Source-only annotations are not paired reference/render landmarks.

`scripts/render_stage_blender.py` imports the actual GLB into Blender, renders fixed views and records provenance hashes. `scripts/build_stage_preview.py` creates a side-by-side reference/current/previous static-head viewer with orbit, zoom, view presets, material/clay/wireframe and asset statistics. It supports opaque, untextured static geometry only; use the standard animated preview for skinned final characters. If WebGL is unavailable, the viewer clearly labels its software 3D fallback. Software preview does not validate GPU rendering, PBR or runtime performance.

The stage validator is a workflow guard, not an authenticated reviewer identity or a substitute for visual review. Passing structural limits does not approve likeness, deformation or target-device performance.
