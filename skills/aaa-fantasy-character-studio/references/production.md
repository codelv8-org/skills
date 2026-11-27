# Modeling, surfaces and bake playbook

## Tool routing
Inspect installed tools and version-specific documentation. Prefer Blender for mesh, sculpt, curves, cloth, UV, bake, render, skeleton and export; optional licensed ZBrush/Marvelous Designer/Substance/RizomUV or authorized image-to-3D starting mesh. Inspect provenance and topology of any external asset; never assume a connector is available. Save editable .blend master with dependencies; external textures use relative paths. Use background Blender for repeatable inspection/export, visual sculpt corrections require credible geometry and review.

## Anatomy and parts
Collections: HEAD, BODY, EYES, HAIR, CLOTH, ARMOR, ORNAMENTS, HIGH, RUNTIME, RIG. Stable IDs per component and _high/_low pair names. Stage gray clay with broad studio light and flat material. Use licensed base mesh or real sculpt, not sphere-and-cylinder anatomy. Shape eyes as cornea/iris with correct placement, not painted-on eyes; preserve skull under hair. Maintain regional seam anchors. Add corrective shapes where necessary; don't erase hidden skin unless garment motion cannot expose it.

## Garments, hair and armor
Construct layers from patterns or fitted meshes with sew lines, pin anchors and plausible fold hierarchy: large gravity folds, medium compression folds, fine weave in normal. Separate rigid ornaments from deforming fabric. Reserve geometric embroidery/filigree for outline and near-camera relief; bake shallow motifs with clean UVs. Use beveled thickness and attachment sockets for jewelry. Hair groom master can be curves/strands; make cards for web or target-supported hair system for desktop. Use scalp cap and overlapping tapered cards with root-to-tip UVs and opacity; check transparency sorting, specular direction, anisotropy and aliasing. Avoid floating hair clumps and plates.

## Retopology and UV
Preserve high-poly sculpt. Build joint loops for shoulders/elbows/hips/knees and facial loops for eyes/mouth; keep quads where useful, triangulate a runtime copy consistently before bake. Report actual triangles, materials, intentional boundaries, nonmanifold issues and degenerate faces. UV0: unique bake islands for asymmetric details, mirrored or tiled only if explicitly compatible. Start at 8-16 px padding for 2K and scale for mip chain; derive final padding from target. Measure density by island area and real surface size; checker should not stretch along sleeve or skirt. Use UDIM in source only when engine/runtime supports it or bake to separate texture sets.

## Baking and look development
Match high/low by object, freeze low triangulation, use compatible tangent space (typically MikkTSpace), explicit cages/ray distances, isolated bake sets and padding. Inspect normal/AO at seams and around thin metallic or overlapping panels. Generate BaseColor (sRGB); Normal, AO, Roughness, Metallic, Opacity and optional curvature/ID/thickness (linear data; emissive color generally sRGB). glTF ORM: R=occlusion, G=roughness, B=metallic. Use separate maps for engine routes that expect different packing; document DirectX/OpenGL normal-Y conversion and check with a test light. No baked studio shadows in albedo. Inspect normal-only, flat albedo and multi-light lookdev.

Skin: dielectric, region-specific pigmentation and roughness, subtle micro-normal/SSS if supported. Silk: directionally coherent weave and specular, smooth broad folds; brocade uses fine patterned relief. Gold/silver: metallic response on actual metal with varying roughness, oxide or paint regions dielectric. Jade/gems: thickness and controlled transmission/reflection, use engine-specific fallbacks. Hair: root-to-tip gradients and alpha cards, restrained shine. Do not use one noisy procedural shader for all materials. Bake unsupported node graphs to portable maps and retain editable material sources.

## Planning budgets (starting points, not guarantees)
| Profile | Triangles for LOD0 | Texture sets | Hair/cloth |
|---|---:|---|---|
| CINEMATIC | as needed, potentially millions | 4K-8K if justified | strands, simulation |
| DESKTOP_HERO | 80k-150k | 2K-4K per set | engine groom or cards, cloth sim/bones |
| WEB_HERO | 30k-80k | 1K-2K per set | cards, bones, limited materials |
| WEB_NPC | 8k-20k | 512-1K | simplified hair and garments |
Measure actual scene load, material draws, alpha overdraw, texture memory, skinned vertices and frame time on target. Choose LOD using projected silhouette and device tests; never decimate before fidelity passes. Use texture compression (e.g. KTX2/Basis where supported) and mesh compression only after validating decoder and appearance.

## Primary references (consult installed-version docs)
- Blender Studio realistic human research: https://studio.blender.org/training/realistic-human-research/
- Blender Manual: https://docs.blender.org/manual/en/latest/
- Adobe Painter baking: https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/baking/how-to-bake-mesh-maps
- glTF specification: https://github.com/KhronosGroup/glTF
- Marvelous Designer: https://www.marvelousdesigner.com/
