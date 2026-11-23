# Evidence-driven release gates

Statuses: `PASS`, `REVIEW_REQUIRED`, `BLOCKED`, `NOT_TESTED`. Never silently treat `NOT_TESTED` as PASS. Keep separately produced evidence paths, tool versions and actual readouts.

| Gate | Test | Minimum evidence | Block/review signal |
|---|---|---|---|
| C0 | Rights and target | Source manifest, reference permissions, target usage | Source unknown/license conflict |
| C1 | Shape, silhouette, mass | Front, profile, rear, 3/4 clay + thumbnail | Wrong body/face depth, asymmetric joints or unreadable silhouette |
| C2 | Topology/facial placement | Wireframes, head close-up, normal check | Inverted faces, joint collapse, overly low/long eyebrows, holes that aren't intentional |
| C3 | UV/material | Material breakdown, checker if textures exist, front/back final | Atlas UV distortion, invalid texture material routing, z-fighting |
| C4 | Rig/animation (optional) | Rest pose, 4+ bend previews, clip recordings | Missing skin/weights/clip, bad pivots or joint penetration |
| C5a | GLB structural | Real .glb and output of `inspect_character_glb.py` and ideally Khronos Validator | Broken GLB, invalid refs, budget overrun, required rig/animations absent |
| C5b | Browser | Actual GLB in viewer, relevant view captures, timing | GLB not loaded, broken materials/animations, target performance unmet |

## Standalone QA steps

- [ ] Record triangle count **after export**, material and draw-call estimate, GLB size and texture map dimensions.
- [ ] Confirm no unrelated objects, lights or cameras are accidentally exported.
- [ ] Confirm local scale and forward direction by import and view.
- [ ] Confirm that requested static vs skinning vs clips mode is truthful.
- [ ] Inspect front, back, side, three-quarter views and face close-up.
- [ ] For skinned character: inspect multiple pose bends, ground contact and loop transitions.
- [ ] For image-textured materials: test UV and atlas; for solid palette without image: do **not** demand UV0.
- [ ] Use Khronos Validator or comparable spec-aware validation when available; the bundled script does not scan all binary data and cannot prove full glTF conformance.
- [ ] Check browser playback and real mobile/desktop viewport where deployment is requested.
- [ ] Include known design or technology limitations in the final deliverable.

## Failure handling

If a numerical checker passes but the rendered silhouette is poor, status remains REVIEW_REQUIRED or BLOCKED until manually fixed. If a static GLB was generated, rigging gate C4 is NOT_APPLICABLE (do not mark animation PASS). If no 3D environment exists, give reproducible scripts and state which outputs do not yet exist. If browser absent, report C5b NOT_TESTED even if GLB parsed in Python.

## v2.0 stronger animated-human gate

- For animated human characters, **both** structural `--require-skin --require-animations` and deep `inspect_skinning.py` are mandatory. A GLB can have four named clips yet still be all detached rigid parts; in that case **C4 fails** unless user explicitly requests segmented mechanical style.
- Verify body joint loops in Blender. Per-primitive connected component counts are diagnostic only; two clothing material primitives need not be one indexed primitive, and some UV seams duplicate vertices.
- **Preview website is mandatory after every generated GLB**, including static builds. `export/preview` must contain actual model bytes + HTML/CSS/JS and be packaged in a ZIP. Browser test must load the exact GLB and scrub requested clips. If local server navigation is unavailable, report it separately instead of marking full serving PASS.
- Numeric QA and WebGL playback do not establish anatomically correct salute, gait, or joint shape. Capture elbow/knee/shoulder extreme-bend and hand-to-temple screenshots.

## v3.0 reference fidelity + WebGL multi-character gate

| Gate | Required evidence | Fail or review condition |
|---|---|---|
| G0 reference | Source SHA, full-res crops, projection assumptions, per-view feature/landmark list | Cropping loses features; source confidence invented; labels confused |
| G1 fidelity | Same-scale four-view matched camera board + evidence-backed scorecard | Material facial/hair/body proportion mismatch or unreviewed critical item |
| G2 geometry | Clay/wireframe + joint loop assessment + artist retopo evidence | SDF/marching-cubes body merely 'connected' but not proper retopo |
| G3 material | Referenced appearance, palettes, glTF material/primitive counts | Excessive draw surfaces, wrong outfit, over-detail without value |
| G4 deformation | Actual 45/90 shoulder/elbow/knee poses and clip sequences | Shoulder collapse, salute crossing face, foot penetration, floating accessories |
| G5 runtime budget | `scene_budget.py` + LOD plan/scene size/character metres | Hero-only character reused for 100 crowd actors without plan |
| G5 browser performance | Real WebGL benchmark with 1/10/30/50/100 on target hardware | Browser not run; FPS not observed; preview is a fallback image |
| G6 preview | Exact exported GLB loaded in usable website and screenshot when tested | Missing site/model or preview not same GLB hash |

**Release rule:** An animated high-fidelity character is PRODUCTION_READY only when all applicable critical gates have evidence. Numeric `GLB PASS` cannot override REVIEW_REQUIRED aesthetics or NOT_TESTED target WebGL. Pass thresholds in `reference_review.py` are explicitly reviewer-rated and shouldn't be represented as objective model similarity scores.

## v4.1 per-part evidence enforcement

Use the HEAD → TORSO → ARMS_HANDS → LEGS_FEET → OUTFIT_GEAR → INTEGRATION pipeline. Reproduce every saved PASS from its current assessment; require the expected part, complete image/mask hashes, distinct landmarks and all mandatory critical criteria. Check original reference hashes where captured. Reject blank/copied image evidence and modified PASS reports. Require fresh per-part assessments from the assembled GLB at integration.

Identify the independent reviewer as HUMAN or AI and distinguish their identity from the model author. An AI reviewer may provide useful independent critique; it cannot create a human approval record. For inconsistent concept sheets, keep approximate fits diagnostic or proceed against an explicitly accepted design interpretation with its original source, approval evidence and limits preserved. See [fidelity-measurement.md](fidelity-measurement.md).

Show the actual current/previous geometry in a stage preview and retain Blender render provenance. These scripts verify evidence structure and reproducibility, not the truth of reviewer identity, render authorship, source mask annotation or artistic likeness. Passing shape stages does not complete rig or WebGL runtime acceptance.
