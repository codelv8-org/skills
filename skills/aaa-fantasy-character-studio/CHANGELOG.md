# Changelog

## 2.0.0 — 2026-11-28 — Beta

### Added
- STRICT_AGENT_CLOUD, CLOUD_DCC (opt-in), and PLAN_ONLY capability routing.
- Editable MeshIR, standard-library GLB compiler, runtime preflight and deterministic CPU bind-clay renderer with camera lock.
- Semantic parts, stable IDs, local repair checkpoints, authored skeleton/weights and explicit animation tracks.
- Meshy/Tripo public workflow research and constraints; no proprietary model weights or service calls.
- Eleven native tests (26 total including 15 prior tests), fixture and rendered evidence.

### Changed
- Default from DCC-first to verified cloud execution. Use Y-up/+Z in native MeshIR/glTF; explicitly map Blender axes. GLB and editable IR/code are primary outputs; FBX/BLEND require a verified cloud backend.
- Retain all 12 G0–G11 quality gates and independent-review requirements.

### Fixed
- Make absent tools and incomplete QA explicit rather than silently assuming Blender, model access, or a valid runtime. Add deterministic camera and compiler checks.

### Removed
- Mandatory Blender dependency for native GLB compilation. No existing production gate is removed.

### Breaking changes
- Default backend and source coordinate convention change; migrate axes explicitly and keep old accepted source/exports. DCC-only deliverables require opt-in.

### Tests and known limitations
- 26/26 Python unit tests PASS on the ChatGPT-hosted development container; deterministic 4,708-byte fixture GLB SHA-256 `431c64a27d2c9c16b1710522757762b92cb0be60307c232e36e386ff3c52294b`; five bind-clay views produced. External learned reconstruction, automatic retopology, full UV overlap, high-to-low bakes, deformation, full glTF validator, target-engine performance and independent review are not certified. Matched v1/v2 visual and AI Chat/AI Agent benchmarks NOT TESTED. Separate provider/model execution NOT TESTED. Existing v1 concept overview retained pending refresh.

## 1.0.0 — prior baseline
DCC-first production contract, G0–G11 quality gates, GLB inspection and evidence sealing. 15 synthetic tool tests. Prior G1 reference-traced prototype is preserved and explicitly failed visual fidelity; see the historical showcase.
