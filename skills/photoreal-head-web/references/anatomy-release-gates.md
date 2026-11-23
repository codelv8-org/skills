# Photoreal anatomy release gates (mandatory operating procedure)

Do not allow a rendering's attractive skin texture to hide a poorly sculpted head. A realistic head must pass each preceding quality gate before the following stage begins.

| Gate | Stage and evidence | Automatic checks | Manual acceptance / block condition |
|---|---|---|---|
| G0 | Permissions, source and reference assessment | File inventory; license/camera notes | Unlicensed reference/mesh or missing tools: STOP/limited mode |
| G1 | Skull + jaw + midface volume; gray-clay contact sheet | Source mesh/camera structure | Reject flattened back skull, floating eyes/ears, synthetic head contour |
| G2 | Eyes/nose/ears/lips sculpt; close-ups | 3D landmark report and optional subject-reference ratio drift | Reject detached nasal prism, wrong ear placement, flat eyelids/nostrils |
| G3 | Photographic matching for a specific likeness | Per-view 2D RMS and landmark overlay | Reject mismatched camera or large feature errors; do not claim likeness from one image |
| G4 | Clean base/retopo + UV + bake | Geometry and GLB UV validation | Reject stretched eyebrow islands, broken loops, baked shadows in albedo |
| G5 | Browser, performance and eyebrow design switching | GLB structural QA, load/interaction checks | Reject web mismatch, brow z-fighting, transparent edges, broken map channels |

## Deliverable pack

```text
project/
  inputs/              # Private references; do not ship to website by default
  source/head.blend
  reports/landmarks_3d.json
  reports/anatomy_qa.json
  reports/front_photo_fit.json       # if reference photo exists
  reports/profile_photo_fit.json     # if reference profile exists
  reports/front_landmark_overlay.png # if annotated
  reports/anatomy_checklist.md       # screenshots, manual findings, fixes
  previews/clay_front.png
  previews/clay_threequarter.png
  previews/clay_left_profile.png
  previews/clay_right_profile.png
  previews/clay_under_nose.png
  previews/pbr_front.png
  uv/head_uv0_layout.png
  textures/...
  export/head.glb
  reports/glb_qa.json
  README.md
```

## Required report contents

1. Evidence quality: generic vs reference-inspired vs specific likeness; views available and limitations (occluded ears, unknown focal length, absent posterior view).
2. Landmarks placed and gate: indicate exact `anatomy_qa.json` status. Never promote `REVIEW_REQUIRED` to scientific pass without evidence.
3. Image overlay: list per-view photo-fit RMS, worst region and remediation; annotate that this is not a biometric measure.
4. Clay screenshot review: describe actual human-reviewed findings for cranial vault, sockets, nose, ears, mandible, eyebrows and jaw (not generic "looks good").
5. Geometry/UV/PBR and glTF QA: actual asset sizes, triangle totals, UV map/channel behavior and web tests.
6. Limitations: distinguish **tool unavailable**, **quality gate not run**, **view lacking**, and **inference required**. Never invent render, screenshot, file, review or scientific accuracy.

## Strict final export

Use `analyze_anatomy.py --high-fidelity` to generate `reports/anatomy_qa.json` after manually placing all required head/nose/ear points. Use `--release --anatomy-report reports/anatomy_qa.json --manual-anatomy-reviewed` with `scripts/blender_export_head.py` only after you actually review gray-clay screenshots. This flag is an operator attestation, not a substitute for looking at the model. For an authorized specific likeness, additionally use `--likeness-requested --photo-fit-report reports/front_photo_fit.json` (and separate profile fit report when a matching profile exists). A blocked anatomy report or non-passing photo fit **prevents release export**. Draft exports without `--release` remain available for iterative visual review; do not label these final or anatomically verified.
