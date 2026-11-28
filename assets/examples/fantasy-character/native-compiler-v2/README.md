# v2.0.0 Native compiler fixture — COMPILED_ONLY

Actual fixture execution in ChatGPT-hosted development container, 2026-11-28. Synthetic `assets/mesh-fixture.json` is input; no proprietary asset, external 3D service or local user machine execution. Python standard library. Not a character model, not a G1 humanoid and not an AAA benchmark.

- 18 triangles, 19 vertices, 2 skinned parts, 2 joints, 1 explicit clip, 0 embedded images; 4,708 bytes.
- Repeated generation matches SHA-256 `431c64a27d2c9c16b1710522757762b92cb0be60307c232e36e386ff3c52294b`.
- 26/26 tests PASS. See [compiler report](compiler.json), [test log](test-log.txt), [camera report](renders/views.json), [GLB](fixture.glb), and [actual renders](index.html).
- AI Chat execution: tested in hosted container (exact provider model ID not exposed in the benchmark record). Independent AI Agent platform execution: NOT TESTED. v1 and v2 use different scenarios; matched version comparison: NOT TESTED. Previous [v1 G1 blockout](../index.html) remains a historical baseline only.
- Full visual fidelity, UV overlap, self-intersection, normal/AO bake, deformation, full glTF validator, independent review and target performance: NOT VERIFIED. Viewer/game runtime not tested. The PNGs are CPU bind-clay renders, not PBR renders or image-generated substitutes.

## Reproduce
From `skills/aaa-fantasy-character-studio/` in verified hosted execution:

```sh
python -m unittest discover -s scripts -p 'test_*.py' -v
python scripts/native_mesh.py assets/mesh-fixture.json fixture.glb --report compiler.json
python scripts/render_clay.py fixture.glb renders --size 384
```
