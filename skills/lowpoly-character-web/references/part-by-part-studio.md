# Part-by-part authoring: isolated milestones, global context, hard stop

## Why this exists

The Sentinel S3 four-view reference was detailed; the prior resulting model still differed strongly in front/side face mass, hair volume, hands, side profile and gear. A valid GLB, coherent skin and four named animations did not repair the mismatched *shape*. This policy forbids fully assembling an incorrect character and only then checking similarity.

**Build parts one by one to control quality, but do not insist on six detached render objects.** The modeling workspace may have modular Blender collections, interchangeable assets, masks and vertex groups. The final deformable body must have sensible neck/shoulder/groin topology, consistent skinning and no seams where it should be one surface. Retopo/weld mesh after parts are fitted; attached hair/clothes/bag can remain separate meshes sharing an armature. Simply `Join` or Boolean Union does not guarantee animation topology.

## G0: Global reference calibration first

- Extract source views without rescaling their anatomy independently. Assign FRONT, BACK, camera-left and camera-right carefully; discover whether the source is perspective or orthographic, and document discrepancies. A stylized four-view concept sheet may not have geometrically consistent orthographic views.
- Mark target overall silhouette, head/body ratio, shoulder position, hip width, ground contact and explicit world height assumption. This is a *global guide*, not complete body generation. Lock one shared scale and a registered camera for each view, with perspective assumptions recorded. For inconsistent concept sheets, follow the observed-reference or approved-design-interpretation branch in [fidelity-measurement.md](fidelity-measurement.md); approximate fits remain diagnostic until that interpretation is accepted. Never auto-fit a model crop to hide actual scale errors.
- Build *temporary* transparent silhouettes/body guides as guides, not as finished geometry. The first polished component is HEAD.

## Ordered production milestones

| Gate | Isolated modeling target | Must match on source views | What can wait? |
|---|---|---|---|
| 01 `HEAD` | skull, chin, nose bridge, ears, eyes, brows, hair volume/tufts | front/back/left/right; head-to-body proportion from global guide | torso clothing, accessories |
| 02 `TORSO` | neck attachment, shoulders, chest, waist, shirt silhouette and collar | all four; relative size to approved head | arm hands, leg detail |
| 03 `ARMS_HANDS` | arms, cuffs, elbows, wrists, palm, thumb/fingers | front/back/side and elbow pivots | pockets/belt |
| 04 `LEGS_FEET` | pelvis/hips, thighs, knees, calves, boots/ground contact | all four and shared global proportions | gear decals |
| 05 `OUTFIT_GEAR` | straps, belt, bag, badge, lettering, pocket shapes | all visible views; account for front/back mirroring | final animation |
| 06 `INTEGRATION` | assembled character fitted into ONE world coordinate/scale and coherent silhouette | all views **plus recheck every earlier part on assembled final mesh** | animation/LOD follows only if approved |

### Each stage follows **build → render → measure → critique → edit → repeat**

1. Read just this stage's source-view crops at native resolution and list critical observed details. Record at least a primary front plus side/back for head. Assign `model_asset` to a real `.glb` snapshot from Blender/authorized modeler.
2. Render the isolated part against the *same camera calibration*, with an optional faint global mannequin for scale. Export four stage RGB/RGBA views and objective silhouette masks (reference masks must be annotated/checked; rendered alpha masks may be thresholded). Keep source untouched.
3. Use `part_region_crop.py` to crop the same ROI from globally registered full-frame views (do not separately refit model crops). Run `part_fidelity.py` for each stage and inspect its 3-row board: source, model, silhouette overlap (green agreement, red missing source pixels, blue extra model pixels). Track mask IoU, bbox error, landmark error, plus 0..5 critical scores from an explicitly identified independent HUMAN or AI reviewer.
4. **PASS requires both:** quantitative mask/landmark tolerance from registered views **and** reviewer-backed ratings (`>=4/5` each critical; weighted `>=4.3/5`), nonblank independent evidence files, a supported camera-calibration method, a real model snapshot and a reviewer distinct from the geometry author. This is a release *policy*, not a machine-guaranteed objective likeness percentage. Change thresholds only by documenting the reason and preserving original score/reports. Don't tamper with reference masks to improve metric.
5. If any view fails, inspect a ranked defect list; modify *geometry*, never hide a mismatch by zoom, FOV, background, material, mirror-flip or editing the reference. Re-render and recalculate. Preserve prior snapshots as `attempt_01`, `attempt_02`, ... for before/after checks.
6. Publish the current and prior stage GLBs in `build_stage_preview.py` with source crops, rendered views and the actual gate status. Show bounds/triangles/materials measured from this snapshot; keep whole-character and crowd estimates labeled separately. Do not start the next stage until the current one is PASS. If no tool can sculpt accurately, mark `REVIEW_REQUIRED` and stop; do not assemble a misleading finished character.

## Cross-stage dimensions and seams

- Keep `model_origin`, local X/Y/Z convention and the assumed character height stable. Share skeleton/rest-pose anchors (`neck_base`, `shoulder_L/R`, `hip_L/R`, `wrist_L/R`, `ankle_L/R`) across stages. Store them in metres in a `part_contract.json` or Blender custom props. Do not shift cameras or inflate the head during independent renders.
- Design seam rings at the neck, shoulders and hip for continuous topology. If skinning, retopo edge loops with consistent vertex flow and sufficient joints. Clothes/hair/accessories may stay in separate skinned meshes but must appear attached in poses.
- Avoid spending most of the character triangle budget on hidden anatomical detail or tiny badges; prioritize accurate outer contour, high-salience face/hair features, motion deformation and material grouping. Never simplify the approved silhouette for the hero tier without rerunning the visual gate.

## Integration regression gate

The `INTEGRATION` stage refuses PASS without **new** `HEAD`, `TORSO`, `ARMS_HANDS`, `LEGS_FEET` and `OUTFIT_GEAR` PASS reports all tied to the *same final integration GLB SHA-256*. Re-render/annotate each region on the assembled model, compare it with the original source, and run `part_fidelity.py` again. Do not reuse the old isolated-stage report; stage readers recompute the underlying assessment, including mandatory checks and exact part identity. Copying old render files into a new directory is not fresh evidence even if their paths satisfy the checker. Modifying that GLB afterward invalidates the regression. After all stages PASS, continue skin deformation QA, clips, LODs, material/draw-call budget, in-browser full & crowd QA.

## Appropriate modeler routing

- Preferred for human reference fidelity: Blender + professionally developed or licensed topology/rigged base of compatible design, guided vertex editing / sculpt and manual retopo at neck, face, elbows, shoulders, hips, knees.
- Low-poly faceted shading means *designing simplified planes*, not replacing the face with cuboids or relying on voxel output.
- Code-only primitive/SDF generators can produce broad blockouts or robotics, but usually cannot model the source's specific face and hair convincingly. A modeler must be capable of geometric refinement or the gate should fail honestly.
- If Blender/visual tools are absent, generate reference crops, stage manifests, diagnostic previews, analysis and **BLOCKED/REVIEW_REQUIRED** quality status rather than claiming a faithful finished humanoid.
