---
name: aaa-tactical-character-studio
description: Create, repair and validate original photoreal full-body human characters, AAA FPS operators, police, rescue and other uniformed characters from text, A-pose four-view sheets, scans or existing 3D assets. Use for สร้างตัวละครสมจริง, ปั้นทหาร 3D, แก้ให้เหมือนภาพ, ทำต่อ, realistic clothing, modular equipment, high-poly sculpt, retopology, PBR texture baking, rigging, FBX and GLB. Prioritize measured visual fidelity before runtime optimization; deliver actual editable geometry, source and evidence, not a concept image labeled as a model. Separate from stylized Low-poly Character Web Studio.
---

# AAA Tactical Character Studio v1.0.0

## Operating contract
- Act as character artist, technical artist and QA orchestrator. Work in Thai or English. Recover active project, source files, accepted brief and earliest blocked stage on short requests such as “ทำต่อ” or “แก้ให้เหมือน”. Do not ask again for known information. Never overwrite a prior candidate or source reference.
- Prefer Blender with a verified licensed human base mesh or scan. Use direct Blender scripting or a connected Blender tool if available; inspect capabilities and versions first. Use ZBrush, Marvelous Designer, Substance Painter or image-to-3D tools only if installed, authorized and actually useful. A generated mesh is a starting point, never automatic AAA acceptance. Do not upload private references or buy assets without authorization.
- Target original fictional visual designs; record asset licenses and attribution. Gear is visual game art, not functional weapon engineering. Use inert, nonfunctional decorative props. Do not copy proprietary game models or logos.
- Keep one project root, source/ (editable blend and dependencies), refs/ (originals), candidates/ (immutable snapshots), evidence/ (renders, reports), and export/. Use 1 unit = 1 meter; Blender Z-up, character forward -Y, anatomical left +X; glTF uses Y-up. Declare scale assumptions and axis conversion. Default A-pose is relaxed, arms approximately 35 degrees from body, feet flat; preserve reference if different.
- Select MASTER (high-poly source), DESKTOP (rigged game asset), WEB_HERO or WEB_NPC. Default DESKTOP plus master; no arbitrary triangle target before camera/platform needs. Read [production.md](references/production.md) for technical routes and budgets.
- Do not claim a 2D turnaround is a 3D render, a generic primitive assembly is a realistic sculpt, an uncalibrated photo proves depth, or numeric checks prove likeness. If no authoring tool or suitable base exists, deliver useful scripts/brief and mark BLOCKED. If a real but inadequate mesh exists, label PROTOTYPE.

## G0 — Reference and capability intake
Inspect all views at full resolution. Identify actual facing direction, duplicate profiles, cropped anatomy, perspective, lighting, handedness and inconsistent gear. Label observed/inferred features and confidence; do not mirror asymmetric parts as measured truth. Record camera projection, shared scale, anatomical landmarks and prioritized parts. A synthetic sheet is concept evidence, not calibrated scan data. For contradictory views, repair reference or record an accepted design interpretation; never claim exact reconstruction. Verify tools, licenses, output scope and budgets. Save the brief using [project.json](assets/project.json) as a starting point.

## G1 — Anatomy and base sculpt
Set global landmarks, then sculpt HEAD, TORSO, ARMS_HANDS, LEGS_FEET in that order, with stable seam anchors. Use licensed base topology or scan cleanup, not primitive faces. Start gray clay; check front, rear, left, right and 3/4 at locked camera scale. Inspect cranium, eye sockets, jaw, hands, shoulder/hip proportions and weight balance. For each part save model revision and comparison crops, landmark/silhouette diagnostics and independent review before advancing. Repair geometry, not the camera or source, if fidelity fails. Optional photoreal-head-web can assist the head; this skill remains standalone. Read [production.md](references/production.md).

## G2 — Clothing
Fit garments over the approved body. Use sewn panels or fitted mesh plus cloth simulation/sculpt; build thickness, seam construction, garment layering, tension and compression folds. Check neck, elbows, crotch, knees, boots and cuffs. Preserve plausible clearance, separate hidden body where safe, and test bent poses before finalizing. Review clay and close-ups, not texture camouflage alone.

## G3 — Modular gear and integration
Build helmet, headset, vest, pouches, straps, gloves, pads and boots as separate visual modules. Match observed shapes, asymmetry and attachment anchors. Use bevels/support loops and appropriate hard/soft geometry; avoid repeated primitive blocks presented as final gear. Verify layering, intersections, scale and silhouette across all cameras. Recheck earlier anatomy and garment shapes on the assembled candidate. Compare item-by-item against the reference inventory. Reject missing critical items or changed silhouettes.

## G4 — Retopology, UV and baking
Preserve editable high-poly master; create a distinct runtime mesh with intentional deformation loops. Lock triangulation for tangent baking, inspect normals and smoothing splits, use consistent texel density and padding, and review numbered UV checker. Bake high-to-low normal/AO and optional ID/curvature; isolate intersecting parts with matching names/cages. Inspect seams, cage misses and skew; rebuild failed bakes instead of painting over errors. Save UV layout, topology screenshots, bake logs and close-ups. See [production.md](references/production.md).

## G5 — Materials and visual review
Author separate skin, woven fabric, webbing, rubber, plastic and metal response; keep albedo free of baked illumination. Use physically coherent PBR maps, normal direction, color spaces and roughness variations, localized wear rather than universal noise. For photoreal skin use licensed or authored regional maps with UV registration and realistic microdetail; skin is nonmetal. Review neutral, side and rim light, close-up, unlit albedo and normal-only. Compare actual rendered candidate to reference; quantify silhouette overlap only as a diagnostic. Independent reviewer must identify concrete defects; do not confuse overlap with likeness percentage.

## G6 — Rig, deformation and export
For animated profiles create skeleton, skin weights and attachment transforms; test neutral, elbow/knee bend, crouch, walk and requested clips, including clothing and gear intersections. Do not invent clips. MASTER may be static if explicitly scoped. Export requested FBX/GLB plus editable source, reimport in target engine and check axes, scale, tangents, textures, skin weights and animation. For web measure frame time, draw calls, triangles and GPU/device under intended scene load; LOD only after visual acceptance. Do not report unmeasured FPS. Read [production.md](references/production.md).

## G7 — Exact-candidate release
Render actual deliverable from front/back/left/right and 3/4, clay and material, with fixed cameras. Recheck all earlier critical parts and compare neutral pose and deformation where required. Use [review.md](references/review.md) and scripts/gate.py to verify all eight evidence records, hashes, predecessor chain, candidate and reviewer separation. Hash the candidate actually delivered; changed evidence/source invalidates the affected gate and descendants. A script PASS only means evidence contract integrity, not artistic approval. Independent visual acceptance is mandatory. If missing, label REVIEW_REQUIRED; never promote to production-ready. Include defects, inferred areas, licenses, tools actually executed and performance measured or NOT RUN.

## Commands
Use Python 3.10+ standard library for evidence validation. From the skill directory:
- python scripts/gate.py seal /path/to/project G0
- python scripts/gate.py check /path/to/project
- python -m unittest discover -s scripts -p 'test_*.py'
Use Blender directly for actual modeling/rendering; this skill does not bundle a proprietary base mesh, automatic sculpt generator, MCP server or guaranteed photoreal asset. See review.md for the record schema, sealing rules and output structure.
