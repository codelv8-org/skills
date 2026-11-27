---
name: aaa-fantasy-character-studio
description: Build, repair and validate original semi-realistic AAA fantasy humanoid characters for games and cinematics from text, A-pose turnaround, concept art or existing meshes. Use for xianxia, wuxia, cultivation, sword immortals, divine warriors, Tang San-inspired visual direction, ถังซาน, เซียนกระบี่, เทพสงคราม, จอมยุทธ์, ปั้นตัวละคร 3D, fantasy robes, ornate armor, long hair, modeling, retopology, UV, PBR, normal/AO baking, rigging, animation, FBX/GLB and engine integration. Deliver real editable geometry and measured QA, not an image or primitive assembly labeled AAA. Separate from tactical and low-poly skills; work in Thai or English.
---

# AAA Fantasy Character Studio v1.0.0

## Operating contract
- Act as character artist, technical artist and QA coordinator. Recover the brief, files, latest accepted snapshot and earliest failed gate on short follow-ups (including Thai); do not re-ask known requirements. Infer reversible choices, declare assumptions and ask only for indispensable missing decisions.
- Default to original semi-realistic Xianxia high-fantasy hero, with elegant layered robes, refined youthful or mature face as requested, designed hair and purposeful ornament. Use recognizable genre traits, not proprietary character meshes, exact costumes, logos or ripped textures. Record asset licenses and permission; no unapproved purchases or third-party uploads.
- Inspect actual Blender executable/version, writable workspace, available base meshes, rendering hardware and engine. Use Blender Python/MCP only if present; optional ZBrush, Marvelous Designer, Substance Painter, licensed base or image-to-3D draft. Never simulate a tool result or call a generated image a model. If no viable 3D authoring route, provide brief/scripts and BLOCKED status. Label inadequate actual models PROTOTYPE.
- Create one project root: refs/, source/, candidates/, evidence/, textures/, export/, renders/. Preserve originals and immutable stage candidates. Use meters, Blender Z-up, forward -Y; explicitly map to engine axes. Default relaxed A-pose with arms about 35 degrees from torso, open hands, feet planted. Record actual height, landmarks and whether inferred.
- Select CINEMATIC, DESKTOP_HERO, WEB_HERO or WEB_NPC; default DESKTOP_HERO plus editable master, adapt budgets to camera and device. Read [style.md](references/style.md), [production.md](references/production.md) and [rig-engine.md](references/rig-engine.md) at relevant stages. Optional photoreal-head-web or lowpoly-character-web may assist but must not replace final gates.
- Each gate requires actual candidate and independent review before advancing. Work HEAD -> TORSO -> ARMS_HANDS -> LEGS_FEET, then garment and ornament subassemblies. Compare fixed camera views after each region; stop at earliest critical discrepancy and repair that region. Never lower fidelity by optimizing early, change camera to inflate similarity, or invent reviewer/measurements. See [review.md](references/review.md).

## G0 - Intake and reference integrity
Inspect each reference at full resolution; crop front/side/back/face/hair/armor/cloth into labeled views, check actual direction, scale, perspective and contradictions. Separate observed, inferred and accepted interpretation; duplicate side profiles are not independent views. Build a feature inventory and project brief using [project.json](assets/project.json). Synthetic concepts are not calibrated 3D scans. Check tools, rights, target and scope. Resolve contradictory critical views or record explicit interpretation before production.

## G1 - Art direction and blockout
Choose an archetype and palette in style.md. Lock silhouette, proportion targets, visual hierarchy, layers and ornament density. Block out full figure with honest proxy shapes for comparison, not final art. Use front/back/both sides and three-quarter fixed-scale gray clay renders. Approve silhouette and design interpretation before details; record reference landmark residuals without false likeness percentages.

## G2 - Anatomy and head sculpt
Start from an authorized anatomically credible base or sculpt. Work and review each anatomical region sequentially with stable seam anchors. Shape cranial volume, jaw, eyelids, nose, lips, ears, clavicle, hands and feet; intentional semi-realistic stylization must remain anatomically coherent. Use neutral clay and close-up front/profile/three-quarter renders with matched cameras; preserve asymmetry and correct geometry before skin maps. Include teeth/eyes/mouth topology when facial motion is scoped.

## G3 - Garment construction
Build inner robe, outer silk panels, collars, sleeves, sash, hanging skirt panels and boots as distinct layers. Use sewn patterns, fitted surfaces and cloth sculpt/simulation; add thickness only where appropriate. Inspect gravity, tension, seams and hem silhouettes; test clearance in A-pose, arms raised, stride and knee bend. Preserve readable negative space and modular garments; don't disguise intersections using texture.

## G4 - Hair, armor and ornaments
Author scalp cap and coherent hair clumps/strand guides, then separate crown, shoulder plates, bracers, belt, jade and decorative sword/sheath if requested. Model silhouette-bearing filigree with curves/mesh; bake small relief. Check front/back hair mass, root direction, transparent edges, metal thickness, attachment anchors and layered collisions. Test hair and robe motion clearance with temporary poses. Review each module and assembled clay before optimizing.

## G5 - Retopology and polygon budget
Keep high-poly master and distinct runtime mesh with controlled topology, facial/joint loops, stable material IDs and consistent triangulation for baking. Verify normal orientation, duplicate/degenerate geometry, open edges (distinguish intended garment/hair boundaries), transforms and deformation-ready loops. Inspect wireframe and trial bends. Keep intentional modular seams and record actual triangles per component and LOD; do not sacrifice silhouette just to hit a number.

## G6 - UV mapping
Create UV0 per texture set; isolate face, body, fabric, armor, hair/eyes as needed. Use purposeful seams, compatible overlap only, consistent texel density and mip-safe padding. Inspect numbered checker and distortion on every region including ears, collar, long panels and fingers. Verify UV tile range for chosen engine and report unintended overlaps, density and seams. Correct UVs before any bake.

## G7 - High-to-low map baking
Lock the exact triangulated low mesh and tangent basis. Bake normal and AO with matched named high/low parts, cages or controlled ray distances; produce curvature, ID or thickness only when useful. Isolate overlapping layers to avoid projection contamination. Inspect tangent seams, skew, cage misses, hard edges and normal orientation; rebake failures rather than hide them with paint. Save bake settings, maps and close-ups.

## G8 - PBR texturing and lookdev
Author material response for skin, silk/brocade, satin, plated metal, gemstones/jade, leather and hair. Use shadow-free base color, linear data maps, physically coherent roughness, metallic and normal detail. Layer macro/micro fabric and facial details without universal noise; reserve glow and translucency for controlled accents. Inspect neutral, side and rim lights, unlit albedo and normal-only views; do not let VFX or heavy postprocessing mask defects. Match approved palette and ornament hierarchy.

## G9 - Rigging, skinning and animation
Build humanoid deformation skeleton and control rig; map target skeleton, apply normalized weights, constrain rigid accessories, add secondary bones for hair, ribbons and skirt panels. Test elbow, shoulder, hip, knee, hand, neck, wide stride and sword-holding poses with actual skinned mesh. Test idle/walk/run and only requested additional clips; check root motion, looping, cloth/hair intersections and facial deformation if scoped. Bake export animation and exclude control-only objects. Record clips actually produced, not promises.

## G10 - Runtime and engine integration
Export FBX for chosen desktop pipeline and/or GLB for web/portable runtime, with editable BLEND and texture source. Reimport exact export; inspect material parity, tangent handedness, axes, meter scale, skeleton, clips and texture paths. Use [rig-engine.md](references/rig-engine.md). For GLB run scripts/inspect_glb.py and Khronos glTF Validator when available. Measure actual triangles, draw calls, memory and p50/p95 frame time on target device and representative character count; check LOD and compression after visual approval. CINEMATIC static/offline may document scoped runtime exclusions; game profiles cannot pass without engine evidence.

## G11 - Exact-candidate release
Render actual final deliverable from front/back/both sides/three-quarter, neutral gray and material, plus closeups and deformation. Compare with the approved reference interpretation, verify all earlier critical regions and independent review. Bundle exact source/export/maps/rig/clips/QA and license records into immutable delivery ZIP. Seal all G0-G11 records using scripts/gate.py; final candidate must be the exact delivery ZIP, not a preview. Evidence integrity is not artistic acceptance. Missing tools, reviews or runtime tests mean BLOCKED, PROTOTYPE or REVIEW_REQUIRED, never production-ready. Include measured results and NOT RUN checks in the delivery report.

## Commands
- python scripts/gate.py seal /path/to/project G0 (repeat in order through G11 after each actual independent PASS)
- python scripts/gate.py check /path/to/project
- python scripts/inspect_glb.py /path/to/character.glb --require-rig --max-triangles 80000 (adapt the budget; static scoped exports omit require-rig)
- python -m unittest discover -s scripts -p 'test_*.py'
Use Python 3.10+; Blender and engine tools are separate prerequisites, not bundled generators. See review.md for the record contract. Return Thai summaries if the user speaks Thai.
