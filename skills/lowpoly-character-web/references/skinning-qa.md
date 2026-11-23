# Character skin QA for animated organic silhouettes

## Numeric checks performed automatically

Run both inspectors on the actual exported GLB:

```
python scripts/inspect_character_glb.py final.glb --require-skin --require-animations --profile balanced --json qa/structure.json
python scripts/inspect_skinning.py final.glb --required-clips Idle Walk Run Salute --json qa/rig.json
```

`inspect_skinning.py` verifies: declared `skins`, scene nodes binding those skins to actual meshes, per-vertex `JOINTS_0`/`WEIGHTS_0`, index range and type, normalized sums near 1, finiteness of inverse-bind matrices, animation time monotonicity, required clip names and targeted skin joint nodes. It reports blended-vertex ratio and topological connected components **within individual indexed primitives**.

Limitations: UV seam duplicated vertices, separate material primitives, intentional boots/vest mesh objects may cause topology reports not to represent the complete character; a large connected component also does not prove edge flow quality. Numeric blend counts do not prove shoulder weights are good. Normative glTF conformance requires Khronos Validator. Default `inspect_skinning.py` intentionally FAILS on the old Cyber Police v2 GLB because it has animated rigid nodes but **no skin**. Use `--allow-rigid` only when that style is explicitly chosen, and report it as segmented.

## Human/artistic gates

Capture real screenshots at these tested poses:

| Region | Pose | What to check |
|---|---|---|
| Shoulder | 0°, 45°, 90° arm lift | Deltoid-to-chest volume, armpit collapse, sleeve stretching |
| Elbow | 0°, 45°, 95° | Elbow folds smoothly; no cap-like detachment or intersecting cuff |
| Hip/groin | Walk stride ~30°, run ~50° | Waist belt and groin distortions; no implausible crotch gap |
| Knee | 0°, 45°, 95° | Pants silhouette, kneecap volume, boots follow shin |
| Wrist/hand | Salute and gestures | Thumb/palm orientation, finger-to-brim contact, no head penetration |
| Head/neck | Turn left/right + tilt | Hair/hat/ear continuity, detached collar |

Set C2 or C4 to `REVIEW_REQUIRED` until actual joint pose images are inspected. `POSE_PASS` requires credible motion and foot grounding, not merely GLB metadata or preview scrubbing.

## QA status vocabulary

- `C0_SOURCE`: permissions, original art and design brief.
- `C1_SILHOUETTE`: anatomical multi-angle images and stance.
- `C2_RET0POLOGY`: wireframe joint loops + topology connectivity.
- `C3_MATERIAL`: material atlas/colors/texture/UV as applicable.
- `C4_RIG`: skin weights; clips; bent joint screenshots.
- `C5A_GLB`: structural inspectors; Khronos Validator if available.
- `C5B_BROWSER`: exact GLB loaded, interactions and animated views captured.

Each gate is independently `PASS`, `REVIEW_REQUIRED`, `BLOCKED`, `NOT_TESTED`, or `NOT_APPLICABLE`. A web screenshot is not proof of a deformation-safe topology. A static original character need not have skeleton weights unless requested.
