# Materials, rendering and GLB verification

## Portable materials and source look development

`reference_finish.py` creates original image textures and nonmetallic Principled materials. Petal UVs run across width in U and base-to-tip in V. Base-colour images are exportable; fine Blender bump/subsurface is additional look development and is not automatically baked. Do not claim identical web appearance solely from identical material names.

The [official Blender glTF guide](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html) describes recognised node connections. Direct Image Texture to Principled Base Color supplies a portable colour image. Constant roughness and metallic values export directly. Packed roughness/metallic uses green/blue channels. Unsupported graphs need an actual bake or a verified runtime shader.

## Surface checks

- Follow real sheet grain through leaf folds and across the centre floor.
- Run pink gradients from pale base to coloured tip, not one flat colour per layer.
- Give bread a crumb/crust distinction on visibly thick slices.
- Give clay a real inner wall and rim; speckles cannot substitute for a cavity.
- Keep micro-bump small relative to metre-scale geometry. Inspect normals before blaming texture resolution.

Roughness, bump, subsurface, colours and lighting are adjustable artistic values, not measured reference properties.

## Presentation

Render three-quarter/front/top views. Match screenshot camera elevation, perspective and crop. Use soft lighting; a cool dark background and warm accent may match presentation but must not obscure geometry. Keep stage water/floor, cameras and lights outside the exported asset collection.

## Export gate

1. Export selected asset meshes in metres, glTF +Y up, with applied transforms.
2. Inspect GLB JSON/image payloads for embedded textures, assignments and unintended external paths.
3. Reimport into a clean scene with `check_reference_model.py`.
4. Check bounds, finite vertices, nonempty mesh data, actual triangle/material budgets and missing images. Overlapping craft parts need not be mislabelled as one watertight solid.
5. Render the reopened GLB with the same camera when visual fidelity is a deliverable. Compare portable-layer differences against the source render.
6. Leave visual status `needs_revision` when silhouette, layers, folds or materials still mismatch, even if every structural check passes.

Keep the editable source and produce a separately reviewed web LOD. Preserve silhouette and thin fold edges before reducing subdivisions. Compression requires compatible loaders and measured quality/performance; do not invent FPS, draw calls or mobile results.
