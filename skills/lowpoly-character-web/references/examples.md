# Trigger examples and expected behavior

## Example A - Original low-poly web NPC

Prompt: "Create an original low-poly office support NPC for my Three.js monitoring dashboard, in A-pose, with outfit and simple face."

Behavior: infer original design, confirm no protected franchise copy, generate shape-sheet assumptions, use a 6-head stylized body if no preference, construct all sides, ensure leg/foot floor contact. Use `generate_blockout.py` for first look when Blender isn't available; do not describe the procedural output as final licensed quality or rigged. If Blender is available, make editable `.blend`, refine topology, export real `.glb`, report measured triangles and preview shots, test actual site where possible.

## Example B - Rigged NPC with clips

Prompt: "Make a rigged lowpoly humanoid with Idle/Walk/Wave for React Three Fiber."

Behavior: choose SKINNED route; model joint-safe geometry, create an armature, normalized skin weights, clips with exactly stated names and duration, inspect bend poses and actual GLB. QA with `--require-skin --require-animations`. Without armature authoring tools, produce procedural static base ONLY as partial work and accurately state rig/clips not created.

## Example C - Stylize a user-owned GLB

Prompt: "This .glb looks wrong in the profile; eyebrows are too long and ears float. Make it low-poly."

Behavior: inspect actual mesh, licenses and render evidence; preserve source copy, correct 3D shapes from multiple views with clay material, repair facial forms and rear volume BEFORE polygon simplification. Retopology is usually better than indiscriminate decimation near jaw, ears, eyebrows, eyelids. Re-export GLB and re-test, report before/after quality gates.

## Example D - Mobile mascot crowd

Prompt: "Build 20 animated animal mascots for a web dashboard, under mobile constraints."

Behavior: nonhuman anatomy branch; pick a family shape system and reuse skeleton only when topology allows it; reduce per-instance triangles/materials, leverage texture atlases and instancing only where incompatible skinning doesn't undermine it. Validate a scene containing 20 concurrently visible characters on target mobile hardware. A single fast character does not establish crowd performance.

## Example E — Fix former Cyber Police rigid-action problem

Prompt: "Upgrade my Cyber Police with Idle/Walk/Run/Salute, avoid assembled-object joints, and let me open a web preview immediately."

1. Inspect input GLB with `inspect_skinning.py`, not only animation count. Previous v2 has zero skins; classify `RIGID_OR_STATIC`.
2. Preserve v2 as design-only reference, retopologize a deformable uniform/body with fitted Armature in Blender; do not simply Join mesh objects or pretend automatic weights will weld seams.
3. Paint normalized weights, author and export the four clips. Inspect actual bent-joint body and salute contact.
4. Build website with `build_preview_site.py --serve --open`, load actual exported GLB, choose all four clips, inspect multiple angles and capture screenshot.
5. Return GLB, website ZIP, source file when authored, multiview images, weight/clip QA report. If Blender is unavailable, do not substitute a false skin claim; deliver a clearly labeled test demo separately.
