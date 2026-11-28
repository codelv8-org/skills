# Rig, deformation, rendering and engine integration

## Skeleton and motion
Keep a clean export deformation skeleton with stable names and root/pelvis hierarchy; control rig may use IK/FK, constraints and helpers but bake final clips onto exported bones. Define bind pose (A/T) and record retarget pose separately. Normalize weights and respect engine influence limit (commonly four for portable baseline; verify). Use rigid bone-parented ornament sockets, not broad automatic weights on hard plates. Add secondary chains for front/side hair locks, ponytail, sleeve ends, sash, skirt panels and cape; keep plausible pivots and collision proxies. Face: blendshapes or joint-based expression as required; include blink, jaw, lip closure and eye tracking if scoped. Test actual deformation, not just rig controls.

Use pose battery: neutral, elbows bent, arms raised, shoulder twist, step, deep knee bend, torso twist, wrist grip and requested action poses. Inspect face close-ups, cloth/hair intersections and armor clipping at motion extremes. Test idle, walk/run loops, requested casting or sword forms; record clip length, FPS, in-place/root-motion convention, loop seam and file names. Check frame sampling and retarget scale. No invented clips.

## Export and validation
- Unreal: export skeletal FBX with baked animations, map skeleton/retarget pose, set cm conversion and verify measured height. Import materials and textures, verify normal-Y convention, separate groom binding/cloth setup if supported. Test exact skeletal mesh in animation preview and gameplay scene.
- Unity: import FBX, configure Humanoid/Generic avatar, validate mappings, scale, clips/root motion and shader/material remapping. Test target pipeline (URP/HDRP/built-in), not just Scene view.
- Three.js/WebGL: export GLB with Y-up, embedded images, supported materials and skin/animation; convert unsupported shader nodes, simulation and groom to portable alternatives; verify loading with target GLTFLoader/renderer. Run Khronos Validator and bundled GLB metadata inspection (limited diagnostic, not full validation). Check alpha mask/blend artifacts and actual performance. Record browser/device, viewport, scene load, frame-time sampling window and p50/p95; never assume FPS from triangle count.
- Godot or other engine: inspect actual importer, axes, units, skeleton, PBR channel packing, animation and LOD support; choose GLB/FBX per target version.

Render locked ortho front/back/left/right and three-quarter clay and PBR; include neutral face and material crops, wireframe, UV checker, bake-only and deformation sheets. Render cinematic beauty separately with restrained VFX, no concealment of flaws. Capture actual engine viewport and note material parity or deviations. For every LOD validate silhouettes, bone weights, material assignment and visible animation; compare at intended distance. Measure budgets from exact exports; document unsupported features and scoped exclusions.

## Delivery
Package editable MeshIR plus reproducible authoring code or .blend when available, game mesh, external dependencies, FBX/GLB (as supported and required), source and packed texture maps, rig/animation, LODs, provenance, render sheets and QA. Add import/retarget notes and preview if built; preview must load actual asset. Include tool versions and reproducible commands. CINEMATIC-only may exclude game import if explicitly scoped; any game profile needs actual engine verification to qualify as production-ready.

References: https://docs.unrealengine.com/ ; https://docs.unity3d.com/Manual/ ; https://threejs.org/docs/ ; https://github.com/KhronosGroup/glTF-Validator
