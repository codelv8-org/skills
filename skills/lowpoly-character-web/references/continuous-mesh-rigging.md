# Continuous-body low-poly character modeling and rigging

## Correct the previous mistake

The Cyber Police v2 prototype used a group-of-objects/rigid-pivot hierarchy. It **contains animation clips**, but has **zero glTF skins** and **no JOINTS_0/WEIGHTS_0**. It cannot bend a continuous elbow/knee/shoulder surface. Rotation around independently placed pivots is not equivalent to skeleton skinning. `Ctrl+J`/Join or placing parts in a parent group does **not** weld seams or create skin weights. Do not use those as the default for an organic/human character.

## New animation architecture

**Preferred human/animal route: `DEFORMABLE_SKINNED`**

1. Design anatomy + clothing silhouette from front/profile/rear with compatible joint pose (A-pose is preferred).
2. Build a **continuous body surface** from a licensed/own base mesh or deliberate manual retopology of a blockout; all deforming areas must have coherent vertices/face flow across joints. A connected body can be **one Blender mesh object** with multiple materials. Seams at intentional clothing divisions can still be skinned and behave correctly if surfaces overlap or match, but test the pose.
3. Topology first at head/neck, shoulder/axilla, elbows, hip/inguinal, knees and ankles. Place additional quad loops on both sides of the bending center; avoid long triangles crossing entire joints. Keep facets coherent without indiscriminately decimating joint loops.
4. Model clothing as (a) contiguous garment sharing or fitting the rig, (b) independent **skinned** coat/vest mesh that references the same armature, or (c) rigid hat/badge/handheld accessories bone-parented or weighted 1.0 where appropriate. **Do not confuse multiple render meshes with a rigid character**: a mesh may be separate and still skin-deformed by the same skeleton.
5. Fit an armature: pelvis/root, spine/chest, neck/head, clavicles/upper arms/forearms/hands, thighs/shins/feet; optional twist bones and fingers by quality target. Align bone pivot to actual joint rotation axes. Keep root motion separate from foot gait when requested.
6. Initialize weights using Blender `Parent > With Automatic Weights` only as a starting point. Normalize and manually repair influence around shoulders, armpits, elbows, groin, knees, wrists, boot intersections. 2-4 influences per vertex is a practical web target; not a glTF hard limit. Check BOTH left and right mirrored bends.
7. Author named Actions/Clips, export actual glTF skins and animations; test on the **exported** GLB with browser renderer. Suggested standard clips: Idle, Walk, Run, Salute, with true meaningful change of skinned joint matrices. Salute must visually reach temple/hat brim; filename alone is not evidence.
8. Validate with structural and numeric inspectors, wireframe + bent-pose screenshots, and browser playback. A model with `skins=0` cannot pass the animated-human release gate.

**Valid alternative: `SEGMENTED_RIGID`** for robotic exoskeletons, mechanical dolls, armor plates with hard hinges, or when the user explicitly chooses deliberate disjointed styling. It may contain animated nodes and no glTF skin; must be labeled distinctly.

## How to handle a rigid segmented GLB submitted for repair

- Import its geometry as **non-destructive design reference**. Retain silhouette, face, palette, insignia and props where legally permitted.
- Determine if the source already contains an underlying continuous humanoid body or only detached capsules/cuboids. If detached, do **not** claim a one-click `Join` or automatic weight operation solves continuity.
- Retopologize from a continuous base, keep joint loops and A-pose, then optionally project source clothing shapes/materials onto the new rigged mesh. Rebuild cuffs/plates as separate weighted clothing or rigid attachments.
- Provide A/B screenshots of the same 30-90 degree elbow and knee bends. If no Blender/retopo artist is available, say **DEFORMATION_NOT_IMPLEMENTED** and deliver the segmented original only as a provisional file, NOT a new skinned edition.

## Anti-patterns

| Anti-pattern | Why it fails | Better method |
|---|---|---|
| Boolean/voxel union then assume deformation-ready | Voxel grid does not follow shoulder/elbow/knee flow; Blender documents this limitation | Manual quad retopology after shape fusion |
| `Join` all arm/leg mesh objects | Joins objects but generally leaves disconnected vertex islands | Merge/weld meaningful boundaries and retopo joint loops |
| Parent mesh objects to separate pivot nodes | Produces rigid action but no vertex deformation | Same armature + smooth normalized weights |
| Animate skin without checking vertex weights | Missing/unbalanced weights cause detached or distorted parts | Numeric weight QA + bent-pose review |
| Skin every accessory to many bones | Belts/holsters/visors deform like rubber | Bone-parent rigid pieces; skin flexible cloth |
| Excessive smooth subdivision after export | Inflates triangles and loses intentional low-poly style | Preserve planar silhouette facets and localized loops |

## Primary technical sources, checked November 2026

- [Blender Manual: Retopology and remeshing](https://docs.blender.org/manual/en/dev/modeling/meshes/retopology.html): automatic remeshing is **not recommended** for final character deformation topology.
- [Blender Manual: Armature Deform Parent](https://docs.blender.org/manual/en/5.4/animation/armatures/skinning/parenting.html): automatic weights are a convenience, not a guarantee; artist corrections are often required.
- [Khronos glTF 2.0 specification — Skins and joint attributes](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html): `skin.joints`, `inverseBindMatrices`, per-vertex `JOINTS_n` and `WEIGHTS_n`, normalization.
- [Blender glTF 2.0 exporter](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html): export of pose-bone animations, Actions / NLA track grouping and exporter configuration.
- [Three.js GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html): loading rendered glTF and animation clips in web apps.
