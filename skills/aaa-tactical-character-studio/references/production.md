# Production playbook

## Select the tool route
Use a licensed anatomically credible base with known rights, or an authorized scan. For text-only concepts design a new character; for a single image label hidden geometry inferred; for multi-view establish corresponding camera directions and landmarks before fitting. Images with two same-facing profiles cannot provide independent left/right evidence. Preserve originals and record an approved interpretation if not corrected. Use Blender Python for deterministic scene organization, export and renders; use sculpt tools for deliberate shape edits. External services require authorization and verified availability; never assume an MCP connection exists.

## Shape and clothing
Keep HEAD, BODY, CLOTHING, GEAR, RIG, HIGH and RUNTIME collections with stable semantic object names. Use full-body front and side skeletal landmarks; use local head landmarks and 3/4 planes. Check fingers, ears, facial features and foot contact. Make each garment from separate panels with seam allowance represented at suitable detail; apply scale, set collision thickness, pin attachments, simulate or sculpt plausible tension/compression folds. Review neutral and bent poses. Keep rigid equipment socketed or weighted appropriately; fabric pouches deform where needed. Use bevels on rigid exterior edges, straps with real width and thickness, and avoid interpenetration. No functional weapon internals or engineering dimensions.

## Surface
Use quad-oriented loops for deforming joints and facial features. Keep high and low meshes separately; bake from named pairs with cages and isolate adjacent parts. UV0 unique where baking requires it; mirrored or tiled islands only where deliberately compatible. Use checker and density maps; verify seams, normals, padding and tangent basis at export. BaseColor sRGB; normal, AO, metallic and roughness data linear. For glTF use roughness G, metallic B, AO R if packed. Use metalness near zero for skin, cloth and dielectric plastic; avoid specular overstatement. Preserve layered source materials; bake unsupported procedural nodes. Inspect shadow-free albedo, close-ups, flat clay and material renders with neutral, side and rim light. For skin separate macro pigmentation, secondary forms and fine pores; never stretch a front image across a skull or treat light/shadow as albedo.

## Planning budgets (not industry standards or acceptance thresholds)
MASTER: editable high-poly, millions of triangles only as needed, layered 4K–8K texture sets if justified. DESKTOP: start 80k–150k triangles and 2K–4K per texture set. WEB_HERO: start 30k–80k triangles and 2K; WEB_NPC: start 8k–20k and 1K. Adapt to visible silhouette, target hardware, material count, memory and concurrent instances. LOD thresholds require visual and runtime measurements, not triangle count alone. Keep FPS arms/camera-facing detail only when requested; separate first-person and third-person variants if needed.

## Rig and engine
Use consistent joint names, normalized skin weights and target-engine constraints; rigid accessories bind to appropriate bones. Check elbows, shoulders, hips, knees, fingers and torso twist with actual deformed mesh, not skeleton-only screenshots. Verify export/reimport of FBX or GLB, texture references, axes, scale, sampled clips and material parity. For a browser use actual target device and representative character count; record p50/p95 frame time, draw calls, triangle counts, memory if available, and test setup. Use glTF validator where available and inspect runtime appearance independently.

## Primary learning references
- Blender Studio: https://studio.blender.org/training/realistic-human-research/ (base mesh, design sculpt, retopology, clothing shapes, baking).
- Blender Manual: https://docs.blender.org/manual/en/latest/ (cloth, sculpt, UV, baking, rigging and export; use installed-version docs).
- Adobe Painter: https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/baking/how-to-bake-mesh-maps (high/low cages and bake inspection).
- Khronos glTF: https://github.com/KhronosGroup/glTF (format and material semantics).
- Marvelous Designer: https://www.marvelousdesigner.com/ (optional licensed garment tool).
