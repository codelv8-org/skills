# Character skeleton, weighting and animation acceptance

## Mode selection

| Mode | GLB requirement | Runtime implication |
|---|---|---|
| Static | Mesh only | Render as a `Mesh`/`Group`; cannot claim animatability |
| Segmented rigid | Pivot hierarchy or transform animations | `Object3D` pivot hierarchy, separate articulated parts; skin is not required |
| Skinned | `skins[]`, node `skin`, `JOINTS_0` and `WEIGHTS_0` for bound primitives | `SkinnedMesh`, bone hierarchy and deformation weights |
| Morph facial | Morph targets in mesh and animation channels if requested | Optional face shape animations |

The provided `generate_blockout.py` generates STATIC geometry only; it intentionally does not fabricate armature, weights or animation metadata. The inspector `--require-skin` correctly fails that blockout.

## Biped baseline

Root/world -> hips/pelvis -> spine -> chest -> neck -> head. Shoulders -> upper arms -> forearms -> hands. Hips -> thighs -> calves -> feet -> toes. Optional fingers, jaw, brows, eyes, facial shape keys, clothing and gear. Mirror bone labels `_L`, `_R` consistently, not viewer left/right. For robots use explicit hinge axes and rigid modules.

- Rig on an intentional neutral A- or T-pose; retain a record of rest pose and scale. Keep one consistent skeleton throughout animation set.
- Set bone rolls and rotations to permit reproducible weight painting and retargeting; inspect transforms and export without accidental nonuniform root scale.
- Use at most four primary influences per vertex when broad compatibility is required; check export behavior when more than four influences are configured. Normalize weights, confirm no vertices with zero weight in a skinned primitive.
- Store clipping limits and inverse-bind matrices as exporters expect. `skin` existence alone does **not** prove weights are correct.
- Hair strands, coats and accessories may be bones, rigid children or separate skinned meshes; verify they don't drift across frames.

## Pose tests (minimum set)

- Arms: rest, raised 90 degrees, overhead, elbows flexed 90 and ~135; inspect shoulder/underarm pinching and wrist twist.
- Legs: knee flexion, hip abduction/flexion, squat and one-leg lift; inspect knee/back-of-knee and pelvis crotch for clipping.
- Feet: standing ground contact, heel lift and toe swing. Inspect foot sliding in Walk and Run, pivot location and sole elevation.
- Head/neck: turn left/right and nod; check hair and collar intersections.
- Hands: basic finger spread and grasp if fingers are included; otherwise state mitten/stylized hands.
- Clip playback: verify `Idle`, `Walk`, `Run`, `Wave` only when **actually present**, and inspect loop transitions. Animation clips may be in-place or carry root motion, but explicitly document which.

## glTF animation compatibility

Blender's exporter supports transform, pose bone and shape-key animations; do not assume arbitrary shader or procedural modifier changes survive. For Blender versions with slotted Actions and NLA export variations, **inspect your installed export options** rather than hardcoding flags. Test the resulting GLB with `AnimationMixer` or drei `useAnimations` in the browser and verify clip names and time ranges. For multi-character scenes with same skeleton, consider reuse after validating that hierarchy/weights and runtime clone handling are compatible.

## Fail criteria

- Any requested clip absent from GLB.
- Mesh visually loses volume or separates under requested bend.
- Bone weights missing on a skinned mesh primitive, even if glTF JSON claims a skin.
- Rigid robot joints intersect unacceptably, or pivot origins are wrong.
- The test was not run but described as PASS.

Do not treat the lightweight structural inspector as a substitute for pose render or web animation QA.
