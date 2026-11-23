---
name: thai-krathong-3d
description: Create, sculpt, customize, review and optimize Thai krathong 3D models from Thai/English text, reference photos and screenshots. Use for ปั้นกระทง 3D, กระทงใบตอง, กระทงดอกบัว, Loy Krathong assets, matching Posy For You or SeasonSnap references, improving an existing krathong, or exporting GLB/Blender assets for Three.js and games. Includes research-grounded structural families, actual Blender geometry and materials, Mesh/UV QA, real Cycles PBR baking, packed ORM, strict web GLB validation and per-image reference review.
category: UIUX
version: 3.2.0
agents: [antigravity, claude-code, codex]
compatibility:
  antigravity: ">=1.0.0"
  claude-code: ">=1.0.0"
  codex: ">=1.0.0"
---

# Thai Krathong 3D Builder

## R3.2 — mesh/UV QA and baked web PBR

For a textured web/game release, read [mesh-uv-web-pbr.md](references/mesh-uv-web-pbr.md).
Run source mesh/UV QA, preserve the editable source, then use
`scripts/bake_web_pbr.py` in isolated background Blender to produce a separate
triangulated BakeUV atlas, actual BaseColor/Normal/Roughness/Metallic/AO bakes,
packed ORM, web BLEND and embedded-texture GLB. Use
`scripts/check_reference_model.py --web-pbr` for strict reimport validation.
The baseline export below remains a source/preview route, not proof of baked
PBR completeness. Do not claim a bake merely because a shader has a Bump node.

Mesh QA rejects degenerate/duplicate/nonmanifold/inconsistently wound geometry,
inward closed components, loose vertices and invalid transforms. Open craft
surfaces need an explicit policy. Bake UV QA rejects collapsed/overlapping UVs,
insufficient island padding, out-of-tile coordinates and excessive stretch or
density variation. Repair demonstrated defects on an authorized working copy;
never silently weld thin folds, overwrite source assets or waive failed gates.

Inspect front/top/three-quarter renders of the reopened GLB. Record technical
pass/fail separately from visual/reference acceptance and target-device tests.
The pipeline does not automatically retopologize, project high-to-low detail,
remove self-intersections or bake SSS/transmission/emission into core PBR maps.
Tested runtime is Blender 5.2.2 LTS; reproducible tests live in `tests/`.

## Verified overview and examples

Open [the overview](examples/web-pbr-showcase/overview.html) or
[the example gallery](examples/web-pbr-showcase/index.html) for three actual
Blender-generated krathong families, rendered GLB views, Thai example prompts,
embedded-PBR GLB downloads and per-example hashes. Read the
[example README](examples/web-pbr-showcase/README.md) for exact reproduction
commands and limits. The gallery is rendered-image evidence, not a realtime
3D viewer; its prompt copy is guidance, not a claim of a new chat execution.

## Research integration R3.1 — primary reference workflow

**Use this route first for image/site-led, realistic, lotus, folded-leaf, tiered, diamond, bread and clay requests.** The legacy workflow below is retained for simple low-poly baselines and backwards compatibility only. Do not automatically reuse its two-ring generator for structurally different references.

Read [research-evidence.md](references/research-evidence.md), the relevant entries in [screenshot-study.md](references/screenshot-study.md) and `assets/reference-catalog.json`. Inspect the actual reference images, not only text describing them. The catalog covers the user's 14 supplied screenshots; it does not establish that every model/page on either website was inspected.

### Choose structure before colour

| Visible structure | Starting preset | Critical comparison |
|---|---|---|
| Open white lotus with different whorls | `assets/ref-white-lotus.json` | Spoon petals, open silhouette, whorl pitch, central volume |
| Pink lotus bowl | `assets/ref-pink-lotus.json` | Broad upright petals, rounded lip, pale-to-pink gradient |
| Thick orange petal bowl | `assets/ref-orange-bowl.json` | Curved thick lips and low broad interior |
| Circular folded banana leaves | `assets/ref-banana-classic.json` | Planar folds, staggered rings, exposed stem base |
| Several leaf terraces | `assets/ref-tiered-leaf.json` | Distinct platform heights and decreasing radii |
| Diamond/heart-like whole footprint | `assets/ref-diamond-leaf.json` | Whole outline, four corners and central negative space |
| Bread slices arranged as a flower | `assets/ref-bread-flower.json` | Flattened slices, crust/crumb, central bread volume |
| Terracotta vessel | `assets/ref-clay-bowl.json` | Open cavity, substantial rim and curved wall thickness |

These are starting constructions. The 14 images include subtypes which may need component edits; document the remaining gap. Do not claim a traditional named fold solely from a similar silhouette.

Interpret Thai material terms in context: “กระทงกลีบดอกบัว” can mean banana leaves folded into a lotus motif or a lotus/petal-shaped body. Use the supplied image and stated material to choose; do not silently turn a green folded-leaf reference into a white flower.

### Record and build

Create `reference_analysis.json` in the output directory: primary image identifier, family, visible layers, silhouette ratios, centre construction, material cues, accessory counts, camera estimate, occlusions, inferred parts and largest current mismatch. Retrieve catalogued screenshots using their known file identifiers when necessary. Treat 0.26 m default diameter as a working assumption, not a measured reference size. Preserve the absence of accessories in a bare reference. Keep seed fixed during revisions.

Use Blender's bundled Python for the new route; it requires no pip packages. Developed against Blender 4.3; inspect actual version compatibility before changing API calls. Run from the skill root:

```bash
blender -b --python-exit-code 1 --python scripts/build_reference.py -- --preset assets/ref-white-lotus.json --out-dir /absolute/output/white-lotus --render --resolution 640 --samples 24
blender -b --factory-startup --python-exit-code 1 --python scripts/check_reference_model.py -- --input /absolute/output/white-lotus/krathong.glb --out /absolute/output/white-lotus/roundtrip.json
```

`scripts/build_reference.py` creates source geometry and calls `scripts/reference_finish.py` for original image textures, materials and presentation. With `--render`, inspect actual Blender front/top/three-quarter renders. Read command help for additional supported arguments. Use `scripts/check_reference_model.py` to reopen the saved GLB in a clean scene and inspect the exported asset, not just the source scene. Read [material-and-export.md](references/material-and-export.md) before claiming portable material fidelity.

Keep render-stage floor/water, lights and cameras outside the asset collection and GLB. Require metres, glTF native +Y up, embedded textures and recognisable component names. Return a `.blend` or rendered preview only when actually created and verified.

### Shape-first gates

1. **Whole form:** match footprint, width/height, opening and exposed base. Disk, flower, terraces, diamond and hollow vessel need different geometry.
2. **Petals/folds:** match broad petal cupping and thickness, or planar leaf ridges/valleys/flaps. Fix spikes, intersections and mechanically identical layers before surface detail.
3. **Assembly:** match layer count, phase offsets, overlap and central volume. Distinguish visible counts from inferred rear counts. Fix the worst mismatch without rebuilding unrelated parts.
4. **Material:** distinguish waxy leaf, soft petal, porous bread, fibrous stem and rough clay. Check grain direction and gradients on the exported GLB. Organic materials are nonmetallic.
5. **Presentation:** align reference camera elevation, perspective, crop and lighting before judging likeness. Keep a neutral shape inspection as well as the reference-style presentation.
6. **Export and visual decision:** reopen GLB; check finite geometry, dimensions, image embedding and export appearance. Record `visual-review.json` with evidence and remaining discrepancies. Technical success must leave visual status `unreviewed` or `needs_revision` until actual image comparison is performed. Never invent percentage similarity.

Read [craft-and-materials.md](references/craft-and-materials.md) for physical construction and evidence limits. Numerical material parameters, hidden geometry, scale and camera settings are design choices, not laboratory measurements. Keep a high-quality editable source and derive a separately reviewed web LOD when required.

Deliver verified GLB, editable Blender scene, actual renders and build/round-trip reports when available. State the primary reference, family, dimensions, technical checks and unresolved visual mismatches. Keep temporary validation outputs outside the installed skill.

**Research status rule:** a completed report or a ZIP in another session does not prove the named skill was updated. Inspect its active instructions and scripts. R3.1 is a new implementation of the completed research findings, not a recovered copy of the unavailable archive described in that report; see the provenance and test record in [research-evidence.md](references/research-evidence.md).

## Legacy compatibility workflow

Use the following baseline only when the user deliberately needs its simpler procedural style. Its anatomy, staged review and honest-delivery principles also inform the primary route, but its default geometry and CPU preview must not override the selected reference family above.

For this legacy route, build culturally recognizable, attractive, **original** 3D Thai krathongs from the simpler procedural GLB baseline. Prefer useful geometry and honest visual review over an unverified claim of photorealism. Follow the user's language (Thai by default).

## 1. Determine the brief without needless questions

Accept any combination of:
- Text, e.g. “สร้างกระทงใบตอง ดอกดาวเรือง เทียน 1 ธูป 3 แบบ Low Poly”.
- One or more reference images with optional front/top/side photos; use native visual interpretation, not OCR.
- Existing `.blend`, `.glb`, `.gltf`, `.obj`, `.fbx` when accessible.

Default when unspecified: **traditional green banana-leaf krathong**, circular banana-stem base, two folded-leaf rings, marigold and globe-amaranth flowers, one unlit wax candle and three incense sticks, diameter about **0.26 meters**, medium-density game-friendly mesh, `.glb` for web. Do not invent a hidden backside from one photo; mark it inferred.

For reference images, extract an explicit `reference_analysis.json` before modeling. Follow [reference-qa.md](references/reference-qa.md) and [anatomy.md](references/anatomy.md). If references disagree, prioritize the user's designated primary reference; identify material uncertainty.

## 2. Select output/quality strategy

- **Web/game/Three.js**: generate optimized GLB (+Y up, meters), transparent multi-view diagnostic preview PNG, QA JSON. Preserve separate material/part groups.
- **Blender editing/sculpting**: produce a `.blend` using Blender when installed; retain geometries named by assembly, then manually refine leaf-fold creases, flower shapes, UVs and material roughness as needed.
- **Realistic / close match to photo**: treat generated mesh as **blockout only**. Use side-by-side orthographic comparisons, hand-sculpt/retopo in Blender, and appropriate original/authorized PBR textures. Never claim exact likeness without visual review.
- **Low Poly**: choose `quality=low`, keep deliberate silhouettes and moderate material count. **Medium** is the default; **High** still requires review and optimization.

Read [anatomy.md](references/anatomy.md) for morphology and proportions. Read [web-integration.md](references/web-integration.md) when integrating in a website or game.

## 3. Generate and inspect stages in order

Run commands from the root of this Skill directory. Dependencies: `python -m pip install numpy trimesh Pillow`.

```bash
python scripts/generate_krathong.py --preset assets/traditional.json --stage base --out output/01-base.glb
python scripts/generate_krathong.py --preset assets/traditional.json --stage leaves --out output/02-leaves.glb
python scripts/generate_krathong.py --preset assets/traditional.json --stage flowers --out output/03-flowers.glb
python scripts/generate_krathong.py --preset assets/traditional.json --stage complete --out output/krathong.glb
python scripts/qa_model.py output/krathong.glb --quality medium
python scripts/render_preview.py output/krathong.glb --out output/krathong-preview.png
```

Alternate presets: `assets/lotus.json`, `assets/stylized.json`. Use a fresh JSON config override with `--config output/custom.json`, not ad-hoc rewrites of the code, when only counts/colors/features defined in the JSON schema need changing.

**Stage gates. Do not proceed to the next stage if the current one fails:**

1. **Base**: Circular, shallow and proportionate; plausible stem and banana-leaf wrapping; scale confirmed. Fix base proportions before leaves.
2. **Banana-leaf folding**: Correct ring count/offset, visible individual folded triangular or lotus-like leaf motifs; check silhouette in *front and top* views. No generic vertical spikes masquerading as leaves.
3. **Flowers**: Match reference flower type, density, color, relative size and placement; no bare space unless in reference. Distinguish a marigold head from a smooth yellow ball.
4. **Ceremonial features**: Correct quantity and placement of candle/incense; inspect overlaps, stick lengths, and decorative balance. Treat flame as optional **visual** element only.
5. **Complete**: Run geometry QA, render isometric/front/top previews, compare against reference, revise, and repeat until accepted. Distinguish automated structural checks from subjective visual similarity.

Render each stage where reference matching is important. For stage-specific QA, use `--stage base|leaves|flowers|ceremonial|complete`. A prompt such as “แก้ให้เหมือนภาพมากขึ้น” should identify and repair **the worst mismatch first**, not regenerate unrelated parts.

## 4. Reference fidelity QA (mandatory for photo-led work)

Use [reference-qa.md](references/reference-qa.md). Compare same crop, orthographic angle, scale and object center where possible. Evaluate morphology, silhouette, layer structure, palette, floral arrangement, and accessories separately. Record evidence, confidence and remaining discrepancies. Human/vision-assessed scores are **heuristic**, not an automated computer-vision similarity percentage. Gate on shape-critical mismatches before detailing secondary textures.

When a stage fails, log `(part, observed mismatch, affected view, correction, re-test result)` and update only that part. Re-run the stage and its successor stages after edits; keep seed fixed for reproducibility.

## 5. Finish and export

`generate_krathong.py` writes a `.glb` and neighboring `.report.json`; `.glb` is suitable for Three.js. `render_preview.py` writes one three-view PNG. `qa_model.py` validates geometry, expected content names, dimensions, and triangle budget; it does **not** certify watertightness, real flotation physics, or artistic matching.

If Blender 3.6+ is available:

```bash
blender -b --python scripts/blender_finish.py -- --input output/krathong.glb --blend output/krathong.blend --render output/blender-preview.png
```

This creates an editable Blender scene with studio camera and lights. On a machine without Blender, return only verified `.glb`, PNG and JSON; **do not pretend a `.blend` exists**. Blender finish helper is optional and may require Blender-specific adjustment for a particular version or render environment.

## 6. Deliverable contract

Provide these when completed and available:
- 3D: `krathong.glb` (meters, glTF native +Y up).
- Diagnostic: `krathong-preview.png` (iso/front/top).
- QA: `krathong.report.json` (component counts, bounding box, triangles, file size, caveats).
- Editable: `krathong.blend` **only** if created and opened/verified in Blender.

State style, counts, dimensions, performance level, passed/failed checks and unverified items. For asset integration, include the file or verified link and the short Three.js import instructions from [web-integration.md](references/web-integration.md). When the user asks only to design the Skill, package the Skill itself; do not confuse the sample 3D model with the Skill package.

## 7. Safety, cultural and licensing considerations

- Respect Thai krathong form and material vocabulary; do not conflate krathongs with sky lanterns.
- Prefer banana stem/banana leaf, real flowers and other biodegradable materials in physical-craft discussions; a **digital** mesh need not physically float.
- User-supplied images and authorized references may be used for comparison; do not embed third-party reference photos or trademarks in distributed assets without permission.
- Never invent empirical scores, UV baking, a rig, native Blender outputs or performance benchmarks without running and verifying them.

## Helpful files

- [anatomy.md](references/anatomy.md): component morphology and visual references.
- [reference-qa.md](references/reference-qa.md): image audit and mismatch gates.
- [web-integration.md](references/web-integration.md): glTF/Three.js loading, web optimization.
- [examples.md](references/examples.md): Thai prompts and practical presets.
- `scripts/generate_krathong.py`: deterministic procedural generator.
- `scripts/qa_model.py`: numerical model QA.
- `scripts/render_preview.py`: diagnostic three-view PNG generator.
- `scripts/blender_finish.py`: optional Blender import/lighting/render/`.blend` helper.
