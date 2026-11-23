---
name: photoreal-head-web
description: Build or repair anatomically credible photoreal human-head 3D models for websites using Blender, measured facial anthropometry, craniofacial landmarks, photographic camera matching, sculpting, retopology, UV0, PBR textures, GLB export, and Three.js. Trigger for realistic head-only character modeling, incorrect eye/ear/nose/jaw proportions, facial anatomy QA, authorized reference-to-3D portrait, eyebrow tattoo texture switching, and diagnosing doll-like or uncanny 3D faces. รองรับการสร้างหัวคนสมจริง ตรวจสัดส่วนใบหน้า และแก้โมเดลศีรษะ 3D สำหรับเว็บ. Requires clay-model anatomy validation BEFORE UV/texturing; includes executable landmark, photo-fit, web-asset and release QA scripts.
category: UIUX
tags: [3d, photoreal, anatomy, blender, glb, three-js, multi-agent]
version: 2.0.0
agents:
  - antigravity
  - claude-code
  - codex
compatibility:
  antigravity: ">=1.0.0"
  claude-code: ">=1.0.0"
  codex: ">=1.0.0"
---

# Photoreal Head for Web - Anatomy First Edition

Act as **craniofacial anatomy-informed sculptor, facial anthropometry analyst, Blender character artist, texture artist, technical QA reviewer, and WebGL/Three.js technical artist**. Create a real editable 3D head when Blender or 3D tools are available; never substitute a nice-looking 2D render for the required mesh, UVs, textured GLB, or browser demo. Focus on **human morphological credibility** before high-frequency realism. A face with lovely skin but poorly placed ears, nose, eyes, jaw, or cranial volume is not photoreal.

## Non-negotiable principles

1. **Anatomy > landmarks > silhouette > secondary forms > UV > texture > lighting.** Never attempt to fix bad facial structure with PBR, filters, noise or high polygon count.
2. **Use a credible base mesh** with correct cranial vault, orbit, nasal support, jaw, ears and face loops when possible. Do not assume a stretched sphere, primitive nose and two spherical eyes can become hyperreal just by adding pores. Blender Studio specifically advises base meshes for hyperrealistic sculpting; check rights/attribution before using the CC-BY example. See [references/anatomy-sources.md](references/anatomy-sources.md).
3. **Measure, do not eyeball alone.** Use standardized soft-tissue facial landmarks, multi-view matching, and reports. But never force all heads to "five eyes across", equal thirds, golden ratios or a single purported ethnicity/sex average. Variation is real; use authorized subject-specific reference when fidelity matters.
4. **Prohibit fake QA.** Only claim a clay check, anatomical inspection, Blender render, UV baking, GLB export or browser QA if tools produced and inspected the actual evidence. Numeric landmarks do not prove realistic mesh topology, believable expression, or anatomical surface quality.
5. **Keep personally identifying photos local/private and authorized.** Avoid sending them to third-party services unless permission is clear. An uncalibrated single photo cannot determine a person's unseen 3D shape or guarantee identity-level likeness. Do not classify a person by protected attributes from the photo.
6. **Deliver head only**, including ears and optional upper neck, not a full body. Keep reusable, independently switchable eyebrow texture/decal layers for brow design websites.

## Choose a modeling route

| Available input | Preferred route | Limit to report |
|---|---|---|
| Text brief | Anatomically verified licensed base mesh + feature design + sculpt and clay review | Original generic character; not a particular real person |
| One photo | Fit landmarks and silhouette in visible view; use base mesh for missing volume | Nose depth, ears and back head remain inferred |
| Front + profiles + 3/4 | Camera align, multiview sculpt, independent view checking | Need matched expression, lighting and camera conditions |
| Calibrated 3D scan / licensed mesh | Clean scan, inspect landmarks, sculpt refinement, retopo, UV/bake | Depends on scan completeness and licensing |
| Existing incorrect GLB/BLEND | Inspect geometry first; re-sculpt from base forms, preserve what is sound | Texture improvements alone may not fix structural problems |

Default when unspecified: realistic **neutral-expression adult generic human**, eyes/ears/scalp/short upper neck, eyebrow-friendly uncluttered forehead, Blender authoring, Three.js output, 4K master texture and 2K runtime maps, 40k-90k total runtime triangles as a planning range (not a scientific rule). Select lower budget for mobile, multi-head catalogs or weaker devices. Avoid asking for extra inputs when a generic realistic head is feasible; report assumptions.

## Production workflow with mandatory gates

### G0 - Intake, reference reliability, tools, licensing

- Verify Blender and permission to run scripts or modify files; inspect any user-provided `.blend/.obj/.fbx/.glb` and reference photos. If no 3D authoring environment exists, deliver executable instructions/scripts and mark 3D operations **not performed**. Never fabricate a model file.
- For likeness work, acquire front, left/right profile and both 3/4 views when reasonably available. Inspect face expression, focal length distortion, head pitch/yaw, hair occlusion, image mirroring and privacy. A single front image is insufficient for precise 3D facial reconstruction.
- Read [references/photo-fit-and-camera.md](references/photo-fit-and-camera.md) for view registration and [references/anatomy-sources.md](references/anatomy-sources.md) for scientifically defined landmarks and source licenses.

### G1 - Primary anatomy and silhouette, texture OFF

- Start with legitimate base head topology or high-detail neutral scan. Block the entire **cranial vault** including posterior depth, frontal bone, temporal region, **zygomatic/malar complex, maxilla, mandible, chin**, then actual eye sockets and ear attachment. Preserve believable relationships in front, both side profiles and 3/4.
- With FLAT GRAY material, render fixed front, 45-degree 3/4, left/right profile, and subnasal angle. Compare head width/depth, jaw projection, top/side silhouette and ears; do not advance if they are structurally wrong.
- **Required deep reference:** [references/anatomy-atlas.md](references/anatomy-atlas.md). Treat it as the sculpting checklist, especially when initial output looks like a mannequin or generic AI face.

### G2 - Anatomy of the eye, nose, ear, cheek, lips (texture still OFF)

- **Eyes:** spherical globe seated behind orbital rim, lid margins wrapping the globe, tear caruncle, upper lid crease and variable epicanthal fold, credible infraorbital/upper cheek and brow ridge volumes. Reject pasted-on almond-shaped eyes.
- **Nose:** separate nasion versus sellion/radix, nasal bones/upper dorsal support, upper lateral cartilage, lower lateral/alar cartilage, columella, nostril wall/rim, projection and nasal alar-cheek junction. Validate front/profile/underside; reject prism-like central extrusion or painted nostril dots.
- **Ears:** accurate lateral/posterior attach point; build helix, antihelix, scapha, concha, tragus, antitragus, lobule with real thickness. Never place flat duplicate ear discs on the front plane.
- **Lips, cheeks and jaw:** zygomatic/malar masses, maxillary support, nasal-labial fold where anatomically appropriate, lip vermilion and philtrum, mouth corners, mentalis and mandibular silhouette. Ensure volume exists in three-quarter view.
- Keep brow-bone volume physically credible; tattoo/brow texture overlays must follow that surface independently from anatomy.
- At each substep, check deliberate natural variation. Do not over-symmetrize or add random asymmetry just for realism.

### G3 - Measured facial landmarks and optional photographic comparison

- Create an empty `HEAD_ROOT` oriented **local +Z up, -Y front, +X subject-left**, `1 Blender unit=1 meter`, then `HEAD_LANDMARKS` empty objects `LM_n`, `LM_prn`, `LM_sn`, `LM_sto`, `LM_gn`, `LM_se`, `LM_rh`, `LM_g`, `LM_pg`, bilateral `LM_en_*`, `LM_ex_*`, `LM_al_*`, `LM_ch_*`, `LM_t_*` and for high fidelity REQUIRE `LM_sa_l/r`, `LM_sba_l/r` (ear top/bottom) plus nasal bridge `LM_se`, `LM_rh` and face markers `LM_g`, `LM_pg`. The `HEAD_LANDMARKS` collection is EXCLUDED from GLB export. Do not invent/guess occluded landmarks.
- Read [references/landmark-and-measurement-system.md](references/landmark-and-measurement-system.md); export coordinates using `scripts/blender_export_landmarks.py`, then run `scripts/analyze_anatomy.py --high-fidelity` for nose-bridge and ear-extent checks. Fix anatomical-order or asymmetry warnings after checking subject and camera. If independent 3D subject coordinates exist, compare **normalized** ratios; without them, report `REVIEW_REQUIRED`, not "perfect anatomy".
- For photo-guided likeness, annotate corresponding visible landmarks in reference photos and flat-clay rendered screenshots. Run `scripts/compare_photo_landmarks.py` for matched front and profiles. Review local overlays and per-region errors before touching textures. A 4% default 2D RMS is an adjustable engineering project threshold, not a scientific or biometric proof.
- If 2D mismatch is caused by camera projection instead of anatomy, correct the camera before distorting correct geometry. Google MediaPipe's estimated 478 facial points may assist XY annotation but **their relative Z is not measured physical depth** and should not be used to define a nose or ear in meters.
- **Block advancement** on landmark QA `BLOCKED`, major clay defects, camera-unexplained feature mismatch, or missing anatomical support; for incomplete generic reference leave documented visual-review limitations rather than manufacturing missing 3D data.

### G4 - Sculpt refinement, retopology, UV and texture

- Retopologize with usable quad loops around eyelids/mouth/brows and correct silhouette. Keep high/low detail variants and bake high-poly normal detail to the real-time mesh. Head, eyes, brows, lashes, scalp/hair cards and decals may be separated by appropriate material/deformation needs.
- Lay seams behind ears/scalp and under chin, preserving continuous face/brow UV0 with enough texel density. Minimize stretching on eyes, nasal bridge, alar curvature, philtrum and eyebrow zone. GLB must use normalized 0-1 UV0 rather than UDIM-only material. Use `scripts/blender_unwrap_head.py` only when seams have been thoughtfully placed.
- Paint real face albedo from authorized reference/manual work, remove shadows, bake OpenGL (+Y) tangent-space normals and region-dependent roughness. Skin metallic = 0. Subsurface response in Blender does not automatically export identically to glTF. The optional `scripts/make_skin_microdetail.py` makes **supporting pore texture**, never an actual face/identity map.
- Keep eye cornea/iris/sclera physically plausible with restrained reflections; skin color variations and lashes should not conceal a structurally wrong eye.
- Eyebrow catalog: separate face-neutral material and individually switchable brow design texture/decal. Use mask/overlay conforming to brow arch, alpha feathering, accurate UV registration, orientation-varying tapered strokes and no z-fighting. Preserve original brow geometry for all variants.
- Read [references/uv-and-textures.md](references/uv-and-textures.md).

### G5 - Evidence-gated GLB export, browser verification and release

- Save `.blend` source and visual evidence. Read [references/anatomy-release-gates.md](references/anatomy-release-gates.md) for the complete release checklist, and [references/web-delivery-and-qa.md](references/web-delivery-and-qa.md) for WebGL budgets.
- For draft iteration, `blender_export_head.py` may export to preview. **For final release**, pass `--release --anatomy-report ... --manual-anatomy-reviewed` only when actual clay renders were reviewed. If specific likeness requested, also pass `--likeness-requested` and applicable `--photo-fit-report ...`. Invalid evidence or `BLOCKED` status prevents release.
- Run `scripts/inspect_glb.py` and `scripts/render_uv_layout_glb.py`. Inspect UVs, embedded image maps and shader behavior. Open actual GLB with Three.js/React Three Fiber (starter: `assets/web/HeadViewer.tsx`). Check mobile and desktop silhouette, face normals, color, eye appearance, mouth, ear depth, forehead/brow swapping, alpha and zoom.
- Never claim browser-validated when only GLB JSON was parsed. Measure file size/triangles/FPS if device/browser tools allow. Keep source/private photos out of public web assets by default.

## Copy-ready command sequence

```bash
# Blender landmark evidence AFTER sculpting; requires an actual head.blend
blender -b source/head.blend --python scripts/blender_export_landmarks.py -- \
  --collection HEAD_LANDMARKS --root HEAD_ROOT --output reports/landmarks_3d.json

python scripts/analyze_anatomy.py reports/landmarks_3d.json \
  --high-fidelity --json reports/anatomy_qa.json

# Only when comparable annotated reference and model-render images exist:
python scripts/compare_photo_landmarks.py \
  inputs/ref_front_points.json inputs/render_front_points.json \
  --json reports/photo_fit_front.json --overlay reports/photo_fit_front.png

# After anatomy + actual gray-clay inspection: UV and export with QA release gate
blender -b source/head.blend --python scripts/blender_unwrap_head.py -- \
  --object Head_LOD0 --output-blend source/head_uv.blend --margin 0.015

blender -b source/head_uv.blend --python scripts/blender_export_head.py -- \
  --collection HEAD_WEB --output export/head.glb --report reports/export_qa.json \
  --release --anatomy-report reports/anatomy_qa.json --manual-anatomy-reviewed

# For authorized exact likeness, add --likeness-requested \
#     --photo-fit-report reports/photo_fit_front.json
python scripts/inspect_glb.py export/head.glb --max-triangles 90000 \
  --max-mb 25 --json reports/glb_qa.json
python scripts/render_uv_layout_glb.py export/head.glb --size 2048 \
  --out uv/head_uv0_layout.png
```

## Final delivery and grading rubric

Default output (only if really created):

```text
head-project/
  source/head.blend
  export/head.glb
  textures/{basecolor,normal,roughness,metallicroughness}/...
  textures/brows/...
  uv/head_uv0_layout.png
  previews/clay_{front,threequarter,left_profile,right_profile,under_nose}.png
  previews/pbr_front.png
  reports/{landmarks_3d,anatomy_qa,glb_qa}.json
  reports/photo_fit_*.json       # only with annotated photo evidence
  reports/anatomy_checklist.md
  README.md                      # integrations, licenses, known shortcomings
```

Report separate gates as **G0 source/permissions; G1 cranial silhouette; G2 feature anatomy; G3 measured landmarks/photo fit; G4 topology/UV/texture; G5 browser** with precise pass/review/block status. List which camera angles are inferred. Always say "not created" for missing files; never invent photorealism scores. **Photoreal-looking render = subjective visual acceptance after multi-view checks, not something any single numerical script can guarantee.**
