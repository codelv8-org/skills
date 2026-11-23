# Character design, source fidelity and art direction

## Production decision

Input combinations: text brief / reference image / multiview sheet / existing blend, FBX, OBJ, GLB / licensed mesh.

1. Identify the user's rights to source art and whether they seek an *original* character, a loosely inspired art style or a precisely matched 3D adaptation. Respect IP and source-file licenses.
2. Describe required deliverables: static mascot/avatar, game NPC, animated controllable player character, facial thumbnail/catalog, or environment population.
3. Decide camera and composition: front/side/back orthographic reference for proportions, three-quarter hero for marketing, actual engine camera for runtime QA.
4. Track visible versus inferred details for one-view references. Do not claim the hidden ear/hair/back matched a photo.
5. Offer three *shape* rules per character, e.g., broad trapezoid shoulders + blocky boots + asymmetric triangular scarf. The design should be recognizable without textures.

## Style presets (choose one; mix only deliberately)

| Preset | Silhouette | Surface | Palette | Typical use |
|---|---|---|---|---|
| Faceted hero | Strong recognizable proportions, beveled large masses | 6-12 sided volumes, controlled hard normals | 4-8 material families | Web portfolio / scene hero |
| Chunky mascot | Oversize head and hands, simple body | Large rounded low-frequency polygons | 3-6 colors | Mascot / educational experience |
| Isometric diorama | Simplified faces, readable from raised camera | Geometric planes, low detail in back | Cohesive matte colors | Simulation / dashboards |
| Retro PS1 | Sparse shapes and prominent texture language | Triangles, controlled texture resolution | Painted atlas | Retro game visuals |
| Flat-shaded toon | Angular features, distinct color planes | Faceted normals | 2-6 colors per outfit | NPC crowds |
| Mechanical bot | Strong joint/pivot segmentation | Hard surfaces and intended gaps | Metal/plastic panels | Robot with rigid animation |

These are creative directions, **not polygon-certification labels**. A stylized head is allowed to be 3-5 head-heights in a chibi mascot or 7-8 in a realistic-proportioned avatar. Choose with intent, do not apply a universal rule.

## Consistency

Write a compact character style sheet: character name, role, age-expression if relevant, head/body ratio, shoulder/pelvis width relative to head, color tokens in hex, geometry language, eye/brow/nose complexity, hair shape, outfit/accessories, footwear, target camera, and budget. Distinguish *geometry variants* from *material variants*. Build an asset family from shared shape language; ensure variants retain consistent scale and joint definitions if animations will be shared.

## Front, side and back model-sheet quality

- Match scale and pose; avoid fisheye, changing focal lengths and exaggerated perspective in orthographic references.
- Front: head width, shoulder slope, hip stance, elbow/wrist heights, leg and boot separation.
- Profile: cranial depth, nose/brow projection, ear depth, torso pitch, pelvis depth, heel/toe profile.
- Rear: skull, hair volume, scapula/shoulder, back clothing, accessory attachment and leg volume.
- Three-quarter: overlap/readability of nose, cheek, arms, boots and hair; guard against floating geometry.
- If a reference shows only a front face, treat profile/back as original design choices requiring review.

## Originality check for publication

If a user asks for a recognizable copyrighted franchise character for a publishable product, identify the risk and propose a new design language rather than copying distinctive helmet emblems, color placement, silhouette or costume. A broad genre can inspire a new work, but do not rely on a name change alone. Record licenses for any downloaded reference meshes, textures or motion data.
