# Repair the part: geometry-first error triage

When a stage fails, do **not** change shader parameters, improve lighting, crop the reference differently or simply export another GLB. Rank a visible source-vs-render difference and apply edits to the actual mesh at the relevant anatomical region. Re-render from the LOCKED camera set after every meaningful geometry edit.

## HEAD: priority before any other finished character parts

1. **Cranial silhouette and ratio:** measure hair-top, forehead, cheek/jaw bottom, chin, ears, and head width at eye line. Compare front and side. Fit the skull cage and hair volume on an appropriately proportioned facial base mesh. Do not replace a face with a faceted capsule if reference shows distinctive forehead and jaw planes.
2. **Hair:** build a coherent hair-cap base with intentional front swept wave, temples and rear volume. Control the largest planes explicitly; use a few overlapping designed hair locks if needed, not random spikes or triangle shards. Check top silhouette on all four views. Fix stray hair strands, hair-ear collisions and gaps.
3. **Eyes, eyebrows, nose and mouth:** annotate left/right centers, brow slopes, eye spacing, nose bridge and tip projection, lip line and chin center. Fix underlying geometry and expressive polygons first. Eye/brow color alone cannot recover incorrect positions. Ensure eye masses are not flat floating squares and brows sit clearly above eyes.
4. **Ears/neck:** match ear-height-to-brow/chin alignment and profile projection; maintain ear depth. Avoid a scalloped dark beard-like neck seam caused by overlapping polygons and incorrect normals.
5. **Check 4 views:** a front match does not authorize a back/side miss. A high front IoU may hide an unfaithful hairstyle or forehead, so every critical checklist line needs human proof.

## TORSO

- Compare neck cylinder (actual neck shape), shoulder slope and breadth, chest/waist taper, shirt collar, rear silhouette and belt position relative to approved HEAD and global height.
- Avoid self-intersection or disconnected top silhouette when moving shoulders. Preserve reference's garment layers without using many tiny material primitives.

## ARMS_HANDS

- Fit shoulder/elbow/wrist anchors, forearm taper, sleeve cuffs, hand length, palm/knuckle/thumb silhouette. Avoid replacing articulated fingers with a mitt if fingers are visible at target screen scale.
- Test a 90° elbow pose before declaring arm topology done. If the hand intersects shoulder/face during salute, refine rotation curve and weights.

## LEGS_FEET

- Fit pelvis width, thigh/shin length, knees, shoe thickness/toe shape and foot alignment. Check side views and weight bearing. Avoid shoe sliding or toe clipping floor in Walk/Run.

## OUTFIT_GEAR

- Map each bag/badge/strap to correct anatomical side across front/back/profile. Preserve large dark bag silhouette in side views. Use textures/atlas for tiny emblems rather than separate draw-call-heavy geometry when visual scale justifies it.

## Integration regression / WebGL optimization

- Re-render all five regions from the joined/skinned model. Head-to-neck connections may have changed after retopo; side profile may change when bag is attached.
- Keep face/hair critical contours when LOD reducing; model distant NPC faces with fewer triangles but retain shape language and material identity. For crowd-scale faces, prefer stable texture/vertex-color cues over multiple detailed separate meshes; never invent dozens of independent draw calls.
- Keep stage budget, measured draw submissions, texture usage, clip count and skin joints in the performance report. Use `scene_budget.py` for estimates and `assets/crowd-benchmark/` for actual GPU measurements.

## Example: Sentinel S3 previous prototype

The earlier model has a visible round/flat hair mass with stray spikes compared with the swept-back facet hair of the supplied four-view sheet; the lower face and ears differ in front/profile, and there is noisy neck geometry. Treat `HEAD` as **REVIEW_REQUIRED** first; do not continue to TORSO just because the original GLB contains 22 joints or 4 clips. Source screenshots are not calibrated and no independently reviewed silhouette masks are available, so do not publish a numerical 'likeness percentage' for that example.
