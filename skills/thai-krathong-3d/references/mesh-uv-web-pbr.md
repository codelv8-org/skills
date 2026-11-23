# Mesh, UV and baked web PBR — R3.2

Use this release route for a textured web/game GLB. The editable research model
and legacy low-poly workflow remain separate. Do not call a scalar-only GLB a
fully baked PBR asset. Scripts run from the skill root using isolated background
Blender; never run scene-resetting code in the user's live Blender document.

## 1. Mesh decisions and QA

Keep an editable, material-separated source. Model actual leaf folds, thickness,
petal cupping, bread crust/crumb and clay inner walls before surface detail.
Normals and silhouette take priority over texture resolution. Use enough loops
to hold curvature, reserve hard normals for intended folds, and triangulate the
web copy before baking so its tangent basis survives export. Do not decimate
the source to meet an unspecified budget. Measure triangles, material/primitive
count and bytes; agree the target-device budget before lossy LOD work.

`mesh_uv_qa.py` reports finite vertices, empty/degenerate faces, loose geometry,
duplicate faces, nonmanifold edges, inconsistent winding, inward closed
components, boundaries and negative/singular transforms. It rejects unevaluated
modifiers: evaluate/apply them on an explicitly saved working copy first.
Boundaries warn by default because open craft surfaces may be intentional;
`--require-closed` makes them fail. This is not self-intersection detection,
retopology, watertight assembly certification or buoyancy simulation. Inspect
intersections and thin silhouettes in front/top/three-quarter views. Repair
the specific defect, preserve authorized source files, rerun QA and record
before/after evidence. Do not auto-weld thin folds or fill intended openings.

## 2. Source UV and bake UV are different contracts

Authored `SourceUV` controls leaf grain and petal gradients. Reuse, mirrors and
overlap may be intentional in that map, but finite coordinates and nonzero UV
triangle area remain required. R3.2 fixes collapsed perimeter walls and the
closing longitude of revolved forms without remapping broad petal surfaces.

The web pipeline copies evaluated geometry, joins it into one mesh, triangulates
it and creates a separate `BakeUV` atlas with Smart UV Project (default angle
66 degrees; configurable via `--uv-angle-limit`). Smart Project discovers
islands without gutters; deterministic uniform-scale bounding-box shelf packing
always assigns final pixel padding, avoiding near-empty atlases from excessive
initial packing margins. If curved projections overlap,
one bounded repair splits only the identified offending triangles into metric
planar UVs before the same conservative bounding-box pack. The report records the
split count. Source geometry and SourceUV remain unchanged; all gates rerun. Source image and
procedural inputs explicitly sample `SourceUV` while baking; changing the active
UV must not change the original material's grain direction. The released mesh
carries only BakeUV. It uses one PBR material and one glTF primitive. The baker checks MikkTSpace
tangents before baking; if a smoothed corner produces a zero tangent it flat-
shades only that demonstrated invalid web face once and records it. Unresolved
invalid bases fail. No source normals are changed.

The bake policy fails on missing/nonfinite/collapsed UVs, coordinates outside
0–1, positive-area overlap, insufficient island spacing, excessive stretch or
extreme density variation. Triangle clipping checks overlap; shared triangle
edges do not count as overlap. Cross-island edge distance checks padding.
Report `tile_border_min_px`, island count, UV area, texels/cm p05/p95 and
3D-to-UV Jacobian singular-value ratios (1 means locally isotropic). Default
stretch limit is 20; density p95/p05 limit is 8. The baker additionally requires
p05 density >=2 texels/cm by default (`--min-texels-per-cm`). Increase this budget
for close-up work. An evenly scaled atlas can still be far too small; density
ratio alone is insufficient. Subpixel triangle counts are reported. These are configurable helper
policies, not an artistic quality score. Thin sides still need visual review.

The final pack reserves `2 * margin + 4` pixels between island bounding boxes,
checks at least `2 * margin` between actual islands and reserves `margin` at the
tile border. Dense assemblies need larger atlases. On packing failure, inspect
`bake-qa.json`, increase resolution or reduce margin with a justified mip/LOD
plan. Never ignore overlap/padding errors. No finite padding guarantees no
bleed at every mip level; inspect distant views on the actual device.

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/mesh_uv_qa.py -- --input /absolute/source/krathong.blend --out /absolute/qa/source.json
blender -b --factory-startup --python-exit-code 1 --python scripts/bake_web_pbr.py -- --input /absolute/source/krathong.blend --out-dir /absolute/new-web-output --resolution 2048 --samples 32 --margin 8 --render
blender -b --factory-startup --python-exit-code 1 --python scripts/mesh_uv_qa.py -- --input /absolute/new-web-output/krathong-web.blend --collection Krathong_Web --uv-layer BakeUV --bake-uv --resolution 2048 --min-gap-px 16 --out /absolute/qa/web.json
blender -b --factory-startup --python-exit-code 1 --python scripts/check_reference_model.py -- --input /absolute/new-web-output/krathong-web.glb --web-pbr --out /absolute/qa/roundtrip.json
```

Arguments after `--` belong to the scripts. `--python-exit-code 1` is required
for reliable process failure status. `--out-dir` must be new or empty and must
not contain the input. The baker refuses live-scene execution and Blender
versions below 4.2. Tested runtime: Blender 5.2.2 LTS; older versions satisfying
the API minimum are not verified. Use `--help` for the actual CLI contract.

## 3. Actual Cycles bake and portable material

| File | Actual operation | Image interpretation / glTF connection |
| --- | --- | --- |
| BaseColor.png | DIFFUSE, COLOR only; no direct/indirect lighting | sRGB; Principled Base Color |
| Normal.png | NORMAL, tangent space, +X/+Y/+Z | Non-Color; Normal Map node, strength 1 |
| Roughness.png | ROUGHNESS bake | Non-Color scalar data |
| Metallic.png | Metallic input routed through EMIT temporarily | Non-Color scalar data; linked inputs supported |
| AO.png | AO bake of the isolated joined asset | Non-Color; not multiplied into Base Color |
| ORM.png | Pack AO.R / Roughness.R / Metallic.R into R/G/B | Non-Color; R → Occlusion, G → Roughness, B → Metallic |

Input material contract: opaque direct Principled BSDF, UV-based coordinates,
no nested node groups. Unsupported transparency/groups/coordinate domains fail
explicitly; flatten/re-author an authorized copy with a separately validated
workflow. Same-mesh baking captures procedural micro-bump into the normal map.
It is not high-to-low projection: retopology, cages, ray distances and skew
correction need their own reviewed source/target pairing. SSS, transmission,
clearcoat and emissive appearance are not reconstructed by the five core maps.
Source krathong materials use nonmetallic values; a black Metallic map is valid.

The source .blend is never saved over. Output includes packed-image
`krathong-web.blend`, embedded-texture `krathong-web.glb`, six PNGs, source and
bake QA reports, roundtrip report and `web-pbr-report.json` with hashes,
timings, settings, failures and input preservation. Optional renders are made
from the **reimported GLB**, not only the source scene. Stage lights/camera/floor
are created after asset export and do not enter the asset collection or GLB.
After changing shaders, UVs or topology, rebake and repeat the export checks.

## 4. Export and delivery acceptance

`check_reference_model.py --web-pbr` requires embedded PNG BaseColor/Normal/ORM,
AO and metallic-roughness sharing that ORM texture, triangles with normals,
tangents and the referenced UV coordinates, and valid imported mesh/UV data.
Actual exported float accessors are checked for finite values, unit normals/
tangents and valid tangent handedness; attribute names alone do not pass.
Missing UV is a failure in this mode. The old structural checker remains
available for legacy assets; its warnings must not be mistaken for web-release
approval. The baker separately verifies non-overlap and pixel padding at the
chosen atlas resolution. Inspect the raw GLB and rendered output; material
names alone prove neither map correctness nor appearance.

Reproducible tests require only Blender, not system NumPy/Pillow:

```bash
blender -b --factory-startup --python-exit-code 1 --python tests/test_mesh_uv_blender.py
blender -b --factory-startup --python-exit-code 1 --python tests/test_web_pbr_blender.py -- --out-dir /absolute/new-test-evidence
```

Tests include all eight source reference presets, deliberately invalid mesh/UV
fixtures, actual Cycles baking with varying procedural roughness/metallic,
pixel-level ORM channel checks, embedded-image parity, corrupt GLBs missing
normal/UV data and refusal to overwrite existing results. Tests are technical
evidence, not a similarity score or device acceptance. 256px test atlases do
not demonstrate production texture quality.

In Three.js, load the GLB with GLTFLoader and retain its imported materials.
The loader assigns texture interpretations and glTF's UV convention; do not
globally force every image to sRGB or flipY. Verify highlights, normals, colour,
mips and silhouettes under representative runtime lighting. Measure GPU memory,
draw calls, file bytes and load time before optional compression. Compression
requires another validation/render pass; never claim a measured FPS without
running the target device.

## Primary references

- [Blender glTF material/export contract](https://docs.blender.org/manual/en/5.2/addons/scene_gltf2.html)
- [Blender object baking API](https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.bake)
- [Blender UV operators](https://docs.blender.org/api/current/bpy.ops.uv.html#bpy.ops.uv.smart_project)
- [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)

Installed Blender 5.2.2 operator RNA and shipped glTF exporter code were also
inspected for bake arguments, UV packing and the `glTF Material Output` AO hook.

See [web-pbr-verification.json](web-pbr-verification.json) for the R3.2 tested
runtime, actual test counts, representative outputs and explicit limitations.
