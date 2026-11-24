---
name: photoreal-head-web
description: Build or repair anatomically credible photoreal human heads for Blender and Three.js with facial anatomy, craniofacial landmarks, camera matching, retopology, anatomical UV atlas, skin texture registration, multiview projection, regional skin maps, PBR shading, GLB and browser QA. Use for realistic head-only models, portrait reconstruction, misplaced facial textures, plastic/waxy skin, UV distortion, eyebrow tattoo catalogs, or repairing an existing head GLB. รองรับภาษาไทย สร้างหัวคนสมจริง กาง UV ให้ตรงตำแหน่งผิว แก้ Texture/Material ผิวพลาสติก และสลับลายคิ้ว. Requires measured clay anatomy before texturing and independent UV, skin and exact-candidate release evidence.
category: UIUX
tags: [3d, photoreal, anatomy, uv, pbr, skin, blender, glb, three-js, multi-agent]
version: 3.0.0
agents:
  - antigravity
  - claude-code
  - codex
compatibility:
  antigravity: ">=1.0.0"
  claude-code: ">=1.0.0"
  codex: ">=1.0.0"
---

# Photoreal Head for Web - Anatomical UV & Digital Skin Edition (3.0.0)

Act as **craniofacial anatomy-informed sculptor, facial anthropometry analyst, Blender character artist, texture artist, technical QA reviewer, and WebGL/Three.js technical artist**. Create a real editable 3D head when Blender or 3D tools are available; never substitute a nice-looking 2D render for the required mesh, UVs, textured GLB, or browser demo. Focus on **human morphological credibility** before high-frequency realism. A face with lovely skin but poorly placed ears, nose, eyes, jaw, or cranial volume is not photoreal.

## Non-negotiable principles

**Surface evidence (v3):** Keep anatomy gates intact. Do not claim photoreal skin from UV bounds, a noisy normal or Blender beauty render. Require an actual, unique skin UV0 atlas, locked registration, region-specific authored maps and three-light/browser inspection. Use [references/anatomical-uv-and-registration.md](references/anatomical-uv-and-registration.md), [references/digital-skin-materials.md](references/digital-skin-materials.md) and [references/surface-release-gates.md](references/surface-release-gates.md).

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

### G4 - Topology, anatomical seams and UV evidence (before final texturing)

- Retopologize around lids, nose, lip and brow loops; use a licensed verified base with a stable canonical UV atlas if variants must share textures. Otherwise mark seams anatomically before unwrap; do not unwrap again after baking unless all dependent maps and masks are rebuilt. One dedicated unique skin material/atlas; separate eyes, scalp/hair, lashes, oral interior and decals as needed.
- Read [references/anatomical-uv-and-registration.md](references/anatomical-uv-and-registration.md) and [references/uv-and-textures.md](references/uv-and-textures.md). Use directional numbered checker on actual mesh, inspect front, both profiles, 3/4, underside and close-ups. Export a draft GLB for UV QA; run `validate_head_surface.py --uv-only` with explicit verified winding. Repair overlap, degeneracy, wrong winding, out-of-range UV and local distortion. Inspect anisotropy/density heatmaps, critical face zones and padding manually; a p95 pass is not a local guarantee. Final GLB hash changes with any re-export.

### G5 - Facial texture registration and projection

- Independently annotate facial surface anchors in final GLB triangles and texture features on the actual atlas. Use `assets/templates/surface_manifest.json`; assign barycentric anchors to brow inner/arch/outer, eyes, nose, lips, ears and hairline; annotate image features separately. Do not manufacture a pass by copying UVs. Choose one canonical atlas ID and preserve its hash; report inferred/occluded regions. Camera-fit multiview photos, project only visible surfaces, de-light, match color and feather seams; otherwise use authorized scans/manual texture painting. Never stretch a frontal photo around the skull. Single-photo reconstruction remains approximate.

### G6 - Regional skin texture and material

- Read [references/digital-skin-materials.md](references/digital-skin-materials.md). Author pigment/albedo separate from lighting; use macro/meso/micro detail from real sculpt or licensed maps. Use `assets/templates/skin_regions.json` and `scripts/regionalize_skin.py` with polygons annotated on the actual atlas to modulate supporting micro-normal/roughness. Do not use generic pore texture as finished face or substitute it for real albedo. Correct color spaces, MikkTSpace tangent bake, glTF G=roughness/B=metallic, effective skin metallic=0, and physically scaled subtle detail. Bake procedural nodes to images. Keep SSS offline or explicitly implement/test approximation with fallback; transmission is not SSS.
- For eyebrow catalog maintain neutral skin with independently registered design overlay; verify both sides, strokes, alpha edges and no z-fighting. Keep brow masks consistent with locked atlas. Never use textures to conceal bad anatomy.

### G7 - Multi-light review and G8 - Web runtime & release

- Inspect unlit albedo, normal-only close-ups and soft/side/rim light renders; use identical cameras and inspect actual seams, pigmentation, specular response and pore scale. If surface looks wrong isolate geometry, UV, projection, albedo, normal, roughness and renderer; repair the earliest failing gate. Record actual evidence; do not make up screenshots or declare review without inspection.
- Read [references/surface-release-gates.md](references/surface-release-gates.md) and [references/web-delivery-and-qa.md](references/web-delivery-and-qa.md). `blender_export_head.py --release` creates ONLY an anatomy-gated `*.candidate.glb`; final promotion is by `validate_head_surface.py --manifest ... --anatomy-export-report ... --promote ...`, after actual browser and three-light review. Structural GLB inspector and runtime QA remain mandatory. The promoted file is an exact byte copy; any mutation requires new QA. If tools/evidence missing, label draft or BLOCKED. Report scope, browser/device, FPS if measured and asset size. Keep private images/master textures out of public web assets by default.

## Copy-ready commands

```bash
blender -b source/head.blend --python scripts/blender_export_landmarks.py -- \
  --collection HEAD_LANDMARKS --root HEAD_ROOT --output reports/landmarks_3d.json
python scripts/analyze_anatomy.py reports/landmarks_3d.json --high-fidelity --json reports/anatomy_qa.json
# Optional comparable annotated reference and clay render:
python scripts/compare_photo_landmarks.py inputs/ref_front_points.json inputs/render_front_points.json --json reports/photo_fit_front.json --overlay reports/photo_fit_front.png
# Only if creating/rebuilding UVs after anatomical seam design:
blender -b source/head.blend --python scripts/blender_unwrap_head.py -- --object Head_LOD0 --output-blend source/head_uv.blend --margin 0.015
# Draft export may have no maps; validate UV before baking (winding must be verified):
blender -b source/head_uv.blend --python scripts/blender_export_head.py -- --output export/head.draft.glb
python scripts/validate_head_surface.py export/head.draft.glb --skin-material Skin --winding cw --uv-only --report-dir reports/uv
# After baking actual maps and completing clay review:
blender -b source/head_uv.blend --python scripts/blender_export_head.py -- \
  --collection HEAD_WEB --output export/head.candidate.glb --report reports/export_qa.json --release --anatomy-report reports/anatomy_qa.json --manual-anatomy-reviewed
# For a specific likeness add --likeness-requested --photo-fit-report reports/photo_fit_front.json and available profile evidence.
python scripts/inspect_glb.py export/head.candidate.glb --max-triangles 90000 --max-mb 25 --json reports/glb_qa.json
python scripts/validate_head_surface.py export/head.candidate.glb --skin-material Skin --winding cw --report-dir reports/surface
# AFTER independent annotation and actual surface/browser reviews, fill manifest with candidate and UV hashes:
python scripts/validate_head_surface.py export/head.candidate.glb --skin-material Skin --winding cw --report-dir reports/surface --manifest reports/surface_manifest.json --anatomy-export-report reports/export_qa.json --promote export/head.glb
```

Example winding is NOT universal; determine it from the verified UV checker/template. Install NumPy/Pillow in the ordinary Python environment for surface tools. See [references/surface-release-gates.md](references/surface-release-gates.md) for evidence contract; `PASS_NUMERIC_ONLY` is not photorealism or release.

## Final delivery and grading rubric

Default output (only if really created):

```text
head-project/
  source/head.blend
  export/head.candidate.glb
  export/head.glb               # only if promoted after full gates
  textures/{basecolor,normal,roughness,metallicroughness}/...
  textures/brows/...
  uv/head_uv0_layout.png
  previews/clay_{front,threequarter,left_profile,right_profile,under_nose}.png
  previews/pbr_front.png
  previews/{checker_front,checker_profile,checker_threequarter,albedo_unlit,normal_closeup,light_soft,light_side,light_rim,browser_front,browser_profile,browser_brow_switch}.png
  reports/surface/{surface_qa.json,uv_anisotropy.png,uv_density.png}
  reports/surface_manifest.json
  reports/{landmarks_3d,anatomy_qa,glb_qa}.json
  reports/photo_fit_*.json       # only with annotated photo evidence
  reports/anatomy_checklist.md
  README.md                      # integrations, licenses, known shortcomings
```

Report separate gates as **G0 source/permissions; G1 cranial silhouette; G2 feature anatomy; G3 measured landmarks/photo fit; G4 topology/UV; G5 registration; G6 texture/material; G7 lighting; G8 browser/release** with precise pass/review/block status. List which camera angles are inferred. Always say "not created" for missing files; never invent photorealism scores. **Photoreal-looking render = subjective visual acceptance after multi-view checks, not something any single numerical script can guarantee.**
