# UV, PBR texturing, and baking standards

## UV0 layout

- Main face: large, unique front-facing island; no mirror overlap when the face needs asymmetrical freckles, brows, or scanned/painted color.
- Scalp/back: secondary islands; hidden scalp seams; ears separated only where necessary. Avoid islands or seams bisecting eyes, upper forehead, or lips.
- All texture-driven meshes must have UV coordinates in `[0,1]` after final packing. UDIM may be used in authoring, but rebake to a single 0–1 atlas for default web GLB.
- Apply checker texture with equally spaced squares; inspect nose tip/ala, eyelids, lips, ears, and the brow zone under angled views. UV bounds alone cannot reveal overlaps or stretching.
- Suggested padding: 8–16 pixels at a 2048px atlas (increase for mipmapping or downsampling); prioritize even face texel density. A smooth face UV must be reviewed manually, not inferred from the success of an unwrap operator.

## Maps and color spaces

| Map | Encoding / convention | Purpose |
|---|---|---|
| BaseColor / albedo | sRGB | Pigmentation; no baked direct lighting or specular streaks |
| Normal | Linear/Non-Color, **OpenGL +Y** | Tangent-space high-to-low detail; inspect at UV seams |
| Roughness | Linear/Non-Color | Natural local variation; avoid uniform plastic finish |
| Metallic | Linear/Non-Color, **0 for skin** | Metallic/roughness packing; no skin metal |
| AO | Linear/Non-Color | Optional restrained local occlusion, not fake lighting |
| Opacity / masks | Linear for numeric masks; author carefully | Brows/lashes/hair cards; soft antialiased edges |

For core glTF metallic-roughness packing: roughness is the **green** channel and metallic the **blue** channel of the metallicRoughness texture. The red channel is unused by this texture; it may separately carry AO when deliberately wired. Avoid plugging a grayscale roughness image into metallic-roughness without correct packing and material configuration.

## Bake sequence

1. Finalize topology, object transforms, and UV0; set correct UV active for both render and bake.
2. Align high-poly sculpt and low-poly, avoiding intersecting separate parts. In Blender Cycles, use **Selected to Active** normal baking with correct high-poly sources and active low-poly destination.
3. Create dedicated image texture targets, enough margin/dilation, and a tuned ray distance or cage to avoid nose, ear, and lip projection errors.
4. Bake tangent-space normals. Inspect seam edges and orientation in target GLTF viewer (OpenGL +Y; flip green only if source is genuinely in DirectX -Y convention).
5. Paint or transfer albedo and paint roughness. Overlay microdetail at correct physical scale, combine with macro normals, and bake to *image-backed* nodes for glTF interoperability. Blender procedural nodes that look good in Cycles may not export intact.
6. Save external texture master files before exporting; connect Principled BSDF image textures in a glTF-compatible arrangement, inspect export warnings, and verify embedded textures after GLB import.

## Facial surface realism

- Use restrained oil/roughness changes across forehead, nose, cheeks, lips, and under eyes rather than identical values across the entire face.
- The skin base color needs subtle uneven pigmentation; do not bake highlight dots, window reflections, shadow contouring, or subsurface shading into albedo.
- Use natural pores only at close zoom; a pore normal with high strength creates a waxy/orange-peel effect.
- Distinguish source beauty shaders from web materials: **full subsurface scattering is not a core glTF 2.0 PBR feature**. Verify actual browser appearance and compensate through balanced base color, lighting, and compatible material controls rather than claiming automatic transfer.
- Optional brow variants: use a dedicated transparent PNG layer/decal or separable mesh with consistent placement; arrange tapered individual strokes with varying thickness, density, and direction. Avoid z-fighting and multilayer alpha sorting artifacts.
