# Image reference: evidence -> view calibration -> modeling constraints

**Use for source image(s).** Read the picture before writing geometry code. Realizing depth from a few 2D images is ill-posed; even a neat 4-view sheet may use perspective, different poses, lighting, shadows, hairstyle asymmetry or inconsistent accessories. Labels `LEFT SIDE`/`RIGHT SIDE` are camera views, not necessarily the character's anatomical left/right. Do not equate a 4-view sheet with photogrammetric or measured orthographic scans.

## Intake (mandatory)

- Inspect original at native resolution; record pixel dimensions, all separate panels, source provenance and intended rights. Crop source safely, excluding captions/background but **not** feet, hair tips or attached equipment. Preserve original unaltered; never crop off subject features.
- Use `scripts/reference_intake.py` on 4-column sheet or individual files. **Review each crop visually**; bad automatic cropping is an explicit failure.
- Record whether camera is perspective/orthographic/unknown for **each** view. Record camera height, lens/FOV and subject direction only if supportable. Exact common 3D measurements are *not* recoverable without calibration or a known dimension. Set target height in metres as a documented project assumption (e.g. user says 1.7m; don't assert that the image proves it).
- Annotate landmarks and colors manually: top of hair, skull and chin, eye/eyebrow/ear/nose, neckline, shoulder joints, sleeve cuffs, hands, pelvis, knees, ankles and foot soles; separately itemize belt, badge, purse, radio, straps and insignia. Record normalized x/y by cropped image width/height with confidence and `unknown` where occluded.
- Compile **feature constraints per view**, including side/rear views: hairstyle volume/tufts, front face silhouette and cheek/jaw, ear projection, body ratio, clothing seams and folds, bag side, boot silhouette, hand finger count, exposed forearm length. Mark `must-match`, `stylization-tolerant`, and `inferred` explicitly.
- Cross-check left/right mirrored design, e.g. strap that is camera-left on the front should plausibly appear camera-right in back. Do not copy asymmetry blindly into both sides. Resolve conflicts with user-supplied images before pretending the 3D reconstruction is exact; otherwise mark inferred details and the fidelity gate REVIEW_REQUIRED. For a useful way forward, propose an explicit coherent interpretation and follow the acceptance branch in [fidelity-measurement.md](fidelity-measurement.md); retain the source and do not invent user acceptance.

## Normalized proportions (ratio must be explicit)

Use **silhouette body height excluding cast shadow** as the normalization denominator for images with unknown physical scale. Measure head-to-body ratio, shoulder-to-body width, arm length to mid-thigh, torso/leg split, shoe-to-body height. Re-check near-identical head landmarks in front and side; a 3/4 angle may not be orthographic. For example `head_height / character_height`, `shoulder_width / character_height`, and `knee_y / character_height` are meaningful normalized constraints; values are **derived from the actual reference**, not universal anatomy constants.

Use glTF `+Y` up and authoring convention specified by project. Adopt 1 unit = 1 metre and root at ground; avoid silently scaling character to match camera instead of correcting proportions. Record target height, root orientation, foot contact and collision capsule for simulation.

## View match gate: no material before silhouette lock

1. Establish global proportion guides, then author HEAD geometry first (licensed head/base fitted or sculpted to reference). Continue with each remaining part only after its predecessor passes.
2. Render front/back/left/right **from camera projection matched to the reference where possible** with the same fixed canvas/ROI after global registration; do not independently crop each silhouette to its own bounds. Show 50% alpha overlays and side-by-side comparison.
3. Compare silhouettes at same normalized height, including head volume/forehead hairline/ear positions, shoulder and waist width, bag protrusion and shoes. If the supplied reference is perspective or internally inconsistent, annotate limitations rather than force a fake single-camera fit.
4. Fix mismatched facial landmarks, silhouette and ratios **in geometry** and repeat this step until accepted. Color and PBR shaders do not rescue anatomy errors.
5. Only then authorize retopology and later rigging. Loop back to modeling when result differs visibly; structural `PASS` cannot replace this gate.

## Quality evidence: explicit independent review

Use `part_fidelity.py` with the current `review` schema for advancement. `reference_review.py --board ...` is a legacy contact-board/global rubric helper, **not a similarity measurement or a substitute for part gates**. It does not authenticate human review. The reviewer fills `reference_scorecard.json` with 0-5 ratings, explanations and evidence per mandatory feature and sets `reference_camera_alignment_verified=true` *only when true*. The checker refuses PASS unless all checks have supported ratings, critical checks >=4, and weighted score >=4.3/5. This is a review policy with subjective inputs, not a machine-recognized truth. Any rating whose evidence is unavailable is NOT_TESTED/REVIEW_REQUIRED.

If you have actual matched binary silhouette masks (reference and render, calibrated to same view), you may compute area IoU as an **auxiliary** signal; do not auto-segment arbitrary colored images and invent an accurate IoU. Landmark normalized-coordinate errors can be quantified after labels exist. Do not present these surrogate numbers as facial likeness or artistic acceptability.

## Good vs bad image-to-character path

- **GOOD:** four-view source -> crop/landmark constraints -> sculpt reusable licensed base -> four-view silhouette test -> retopo/joint loops -> outfit -> weight paint and animated poses -> review -> LOD / WebGL budget.
- **BAD:** four-view source -> generic SDF ellipsoids or assembled cylinders -> marching cubes -> random color facets -> attach accessories -> call it finished because GLB validates.

The source used for the Sentinel S3 prototype was detailed enough to constrain many visual features. The previous builder used SDF/marching cubes and lacked manual retopo, so reference comprehension alone would not have created a faithful high-quality result.
