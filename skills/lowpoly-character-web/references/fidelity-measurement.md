# Measure part shape without inventing a likeness percentage

`part_fidelity.py` measures calibrated binary silhouette agreement and explicitly annotated 2D landmarks. It does not recognize facial identity, judge characteristic hair planes, verify the rendering process, or certify production quality. Read this contract before supplying an assessment.

## Choose an honest reference basis

**Observed reference:** use `camera_calibration.reference_basis: "OBSERVED_REFERENCE"` only for comparison to the original source. Set `verified: true` only when projection, framing and shared scale are actually supported. A neat four-panel illustration is not proof of orthographic calibration.

**Uncertain concept sheet:** retain the original, label each view's projection/confidence, and list conflicting widths, hair shapes, poses or hidden features. Set `diagnostic_only: true` for approximate camera fits. Render and critique the actual HEAD geometry; record a prioritized correction list and useful preview even while the gate is `REVIEW_REQUIRED`. Do not optimize a poorly justified IoU or lower its threshold until the number passes. The Blender stage renderer's `alignment: "APPROXIMATE_CONCEPT"` is a disclosure, not calibration approval.

**Approved design interpretation:** when the original cannot define one consistent 3D shape, propose a coherent target sheet/landmark set preserving the observed high-priority features. Keep source and proposed target separate; label inferred back/hidden surfaces. Obtain explicit acceptance of material design choices from the user or a reviewer already authorized to make them. An agent must not invent user approval. Record who accepted what, the original source hashes, the conflicts resolved and the remaining limitations in a text evidence file. Use `reference_basis: "APPROVED_DESIGN_INTERPRETATION"`, `interpretation_evidence` and `limitations`; calibrate the model against these accepted targets. A passing result then applies to that interpretation, never to exact recovery of unknown source geometry. This branch permits useful progress without pretending all concept views can be physically reconciled.

When no such interpretation has been accepted, keep the stage in review. Ask about the unresolved design choice only when it blocks useful work; routine part review may be performed by an independent AI reviewer within the accepted brief.

## Inputs and registration contract

- Provide `part` from the six stage names, an actual stage `model.glb`, `model_author`, four unique `required_views` (`front`, `back`, `left`, `right`), and a view evidence object for each. Missing observed views require the documented interpretation branch; silently deleting them cannot produce PASS.
- Export self-contained `TRIANGLES` geometry with decoded float POSITION data for this numerical gate. Convert strips/fans to mode 4 and decode sparse/compressed geometry before assessment. The checker reads real vertex/index payloads, rejects truncated/nonfinite/degenerate data and requires geometry reachable from the active scene; it is not a complete Khronos validator.
- Preserve independent source and render PNGs with meaningful visible content. Copied pixels, transparent/blank images and the same file reused as image/mask are rejected. Reference and render must share canvas dimensions and camera framing. Use `part_region_crop.py` for the same ROI after global registration; do not independently center, scale, stretch or flip the model to hide disagreement.
- Prepare independently checked binary PNG part masks: white foreground, black background, no cast shadow or mannequin guides. Render masks must isolate the actual part using an object-ID/alpha pass. The masks need at least a 32-pixel canvas, a 16-pixel part extent in both axes, 20 foreground pixels and meaningful background (under 98% occupancy). These checks reject obvious degeneracy; they do not validate segmentation semantically. Improve evidence resolution for face/ear details.
- Annotate named physical landmarks on both images using finite normalized x/y pairs in [0,1]. Do not invent an occluded feature. Duplicate coordinates within one view cannot inflate the count; different views may share the same anatomical feature. At least 5 HEAD, 3 TORSO, 4 ARMS_HANDS, 4 LEGS_FEET, 2 OUTFIT_GEAR and 5 INTEGRATION observations are required. The reviewer must still verify that labels correspond to real features.
- Capture actual geometry renders after each edit. `render_stage_blender.py` imports the exported GLB and records its SHA-256, Blender version, camera parameters and image hashes. It does not create reference masks or certify reference alignment; its rest/static render is not animation QA.

## Independent review and schema

Use `review` in new assessments. Legacy `human_review` is accepted as an input alias only; it no longer implies a human reviewer. Do not provide both keys. For example:

```json
{
  "model_author": "author-agent-or-artist-id",
  "review": {
    "reviewer": "separate-reviewer-agent-or-artist-id",
    "reviewer_type": "AI",
    "independent_from_author": true,
    "approved": false,
    "notes": "Name the compared views, concrete defects, and any limits.",
    "render_model_sha256": "SHA256_OF_THE_EXPORTED_GLB",
    "context_sha256": null,
    "weighted_min": 4.3,
    "checks": []
  }
}
```

Populate every mandatory check generated by `stage_pipeline.py init`; the empty example cannot pass. Keep their IDs and `critical: true`, positive finite weights, 0–5 ratings, nonblank notes and existing nonblank PNG comparison evidence. Critical checks require >=4/5 and the weighted score requires >=4.3/5. These are heuristic review targets, not a validated perceptual scale. Changing a review threshold requires a reason and retained prior reports; never remove critical criteria or landmarks to make a result pass.

Ask the independent reviewer to inspect actual source/render boards and, where available, the live GLB from multiple angles. Give the brief and raw artifacts, not an intended verdict. Have them name specific geometry corrections and judge the current snapshot; author self-checks remain useful but do not fulfill independence. Identify another AI agent as `AI`, and reserve `HUMAN` for a real person's observed approval. The script validates declared fields and differing IDs; it cannot authenticate reviewer identity or prove independence. Never label synthetic test fixtures as acceptance of a real model.

Reports expose `reviewer_type`, `reviewer_approved` and `reviewer_weighted_rating_0to5`. Compatibility fields `human_approved` and `human_weighted_rating_0to5` are false/null for AI review. Old reports require a fresh evaluation under this evidence contract; they are not silently upgraded.

**Pin exactly what was reviewed.** First run an assessment with decisions unapproved to obtain `required_review_context_sha256`. Have the independent reviewer inspect those exact model/images/masks, camera parameters, landmarks, thresholds, rubric and interpretation evidence, then copy that digest into `review.context_sha256` while recording their actual decision. The digest excludes approval/rating/notes fields, so it can be obtained before a decision. It includes current evidence bytes and nondecision inputs. The checker never refreshes this review pin: a changed render, mask, model, camera, landmark, threshold or reviewed board makes the previous approval stale and returns `NOT_TESTED`. Do not automatically copy the new digest and carry the old approval forward. This binding records review freshness; it still cannot authenticate the reviewer.

## Measurements and interpretation

- `silhouette_iou = |mask_ref ∩ mask_render| / |mask_ref ∪ mask_render|`. An IoU of 0.85 means 85% binary-mask intersection/union, never “85% character likeness.” High overlap can coexist with a visibly wrong face or hair.
- `bbox_size_error_ratio` measures the largest relative width/height mismatch. `bbox_center_error_ref_height` measures center displacement divided by reference-part height. Do not normalize these errors away afterward.
- `mean_landmark_error_ref_height` averages 2D paired-point distances divided by reference-mask height. It is not a 3D reconstruction error or recognition score.
- Initial HEAD defaults: each view IoU >=0.84, bbox error <=0.09, center error <=0.07 head heights, mean landmark error <=0.06, and the review criteria above. Benchmark any project-specific changes against accepted examples and retain the rationale.

A facial expression, jaw plane, ear depth or rear hair contour may fail review despite passing all numeric thresholds. Fix the actual geometry, recapture the same cameras, and compare the new and previous attempts.

## Gate integrity and limits

Missing evidence produces `NOT_TESTED`; malformed, blank, duplicated or structurally invalid evidence produces `BLOCKED`; a valid but failed comparison or diagnostic-only fit produces `REVIEW_REQUIRED`. Only a complete passing assessment produces `PASS`. Scripts do not prevent deliberate false statements or prove that submitted masks/render files derive from the model; inspect the real GLB and renderer provenance.

`stage_pipeline.py` reproduces saved PASS results from current inputs and checks the full evidence hash set, part identity, exact model and review fields. Editing a report to say PASS, deleting its hashes or recycling a different part report cannot advance the pipeline. Original reference hashes captured during initialization are checked. Keep originals and attempt history even when the project was initialized before references were available.

After assembly, re-render all earlier regions from the final integrated GLB, create fresh assessments and review evidence under `stages/06_integration/regression/`, and re-evaluate each region. Reports must correspond to the expected region and same final model hash. Hashes detect file changes; copying an old image into a new folder does not make it fresh render evidence.

## Commands

```bash
python scripts/stage_pipeline.py init --out my-character --reference-dir reference_pack
python scripts/stage_pipeline.py next --project my-character
# Author HEAD and populate its assessment with actual evidence and independent review.
python scripts/stage_pipeline.py evaluate --project my-character --stage HEAD
# TORSO remains blocked until HEAD can reproduce PASS.
python scripts/stage_pipeline.py evaluate --project my-character --stage TORSO

# Regression model_asset must point to ../model.glb from the regression directory.
python scripts/part_fidelity.py my-character/stages/06_integration/regression/head_assessment.json \
  --out my-character/stages/06_integration/regression/head_gate.json \
  --board my-character/stages/06_integration/regression/head_comparison.png
```

Keep report/board output separate from input evidence: `--out` and `--board` must not overwrite the assessment, GLB or any declared evidence path. The standard stage output `review/comparison_board.png` is distinct from input review evidence. After shape stages pass, rig, animation, LOD and measured WebGL requirements still apply.
