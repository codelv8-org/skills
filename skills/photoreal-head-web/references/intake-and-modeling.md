# Reference intake and anatomical modeling

## Decision tree

1. **Only text brief**: design a new, generic adult-like face from non-identifying descriptors. Avoid promising likeness to a real person. Use anatomical baselines and intentional natural asymmetry.
2. **One 2D picture**: estimate depth from visible clues, clearly mark the hidden side/ear/back skull as inferred. Work from a neutral focal-length picture, avoid perspective exaggeration. Do not guarantee biometric match.
3. **Front + profile / 3-quarter images**: align iris and ear landmarks, estimate camera differences, adjust depth, verify eye-to-eye spacing, nasal projection and jaw profile.
4. **Multi-view calibrated photos / licensed scan**: align camera and geometry. If tool availability supports reconstruction/scan cleanup, use it; do not call uncalibrated views "photogrammetry" without reconstruction evidence.
5. **Existing mesh**: inspect license, vertex count, UV sets, material nodes, orientation, normal direction, facial proportions, missing texture references, and rig/shape-key dependencies before modifying.

## Reference shot checklist

- Frontal, both 3/4 views, left/right profile; ideally back/scalp if scalp is visible.
- Neutral expression; eyes open; lips relaxed; hair away from forehead and ears; diffuse lighting; same subject and consistent camera distance.
- Note missing photos but do not block creation of a generic head. Ask for additional views only if exact likeness or geometry cannot be judged otherwise.
- Obtain permission to use reference images and textures; document licensing of scan bases, brushes, and HDRI. Keep source photographs outside public web distribution unless expressly authorized.

## Sculpt order and viewing checkpoints

**Blockout:** cranial vault → mandible/chin → cheekbone → brow/frontal bone → nose → ears. Compare face width, brow-to-eye, philtrum-to-chin, cheek depth, profile silhouette. Avoid using one face-proportion formula for all people.

**Secondary anatomy:** orbital rims; tear ducts, upper/lower lid thickness and crease; septum/alar cartilage and nostril rim; lips and vermillion border; masseter/jaw transitions; pinna anatomy; soft asymmetry.

**Tertiary detail:** pore roughness, pigmentation variations, skin creases, fine peach fuzz; these belong primarily in maps rather than raising web mesh density. Realism usually fails first in proportions, eyes, and lighting, not in polygon count.

**Eyes:** use eyeball mesh with iris/sclera or layered cornea, avoid pure-white sclera, do not bake fake bright glints into base color, test highlight strength and cast eyelid shadows.

**Brows:** keep a separate brow material or overlay for catalog variants. Human eyebrow hairs taper and overlap along several direction fields; repeated identical parallel strokes are conspicuously artificial. Inspect at both portrait framing and 3x zoom.

## Geometry hygiene

- Keep baked/source high-poly meshes separate from real-time meshes.
- Retopologize with rings around eyes and mouth if expressions are planned; static use may prioritize silhouette and shading over deformation loops.
- Weld accidental duplicate vertices; remove internal faces and accidental disconnected shells; repair normals and intentional openings. Use subdivision sparingly in the exported LOD.
- Separate glasses, eyelashes, hair cards, eyes, and facial decals where different transparency/rendering strategies are needed.
- Use real-world proportional dimensions with **1 Blender unit = 1 meter** if the environment allows, and verify the exported glTF axis orientation before hardcoding camera distance.
