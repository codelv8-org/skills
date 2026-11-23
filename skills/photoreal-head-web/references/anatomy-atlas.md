# Anatomy atlas for genuinely credible human-head sculpting

Read this **before touching subdivisions, UVs, microtexture, or hair**. Use physical anatomical forms as a constraint system, not an arbitrary beauty ideal. Study cranial structures and face soft tissue as 3D volumes in frontal, 3/4, lateral, subnasal, and top-down views. Read [anatomy-sources.md](anatomy-sources.md) for original scientific/production sources (each file is also linked directly from `SKILL.md`).

## Layer 1: skull and bony scaffold

1. **Cranial vault**: Build frontal bone curvature, temporal breadth, parietal vault/back-of-head, occipital transition, and overall depth. The forehead is not a flat billboard and the rear skull must project considerably behind the ear. Do not place features on a stretched sphere while ignoring the vault.
2. **Orbital complex**: Create a real superior/lateral/inferior orbital rim with depth. The brow/supraorbital ridge sits over the orbits, not level with a floating eye. Eye sockets are inset in the frontal/zygomatic/maxillary support; eyeballs do not float outside a flat mask.
3. **Midface**: Construct zygomatic body/arch, infraorbital and malar volume, and maxillary projection. Cheekbone width, cheek projection, nose base and upper-jaw depth define the three-quarter silhouette. The cheek transitions into the mouth muzzle rather than forming planar triangles.
4. **Mandible**: Set ramus, gonial angle, body of mandible, chin symphysis, and mandibular angle. Check jaw depth under the ear in profile; do not use an unrelated V-shaped chin attached to a round head.
5. **Temporal/auricular attachment**: Place ear posterior to outer eye and anatomically attached around the temporal region, not on the same front-facing plane as the eyes. Preserve room behind the ear to the occiput.

**Gate A:** In flat gray, test front + 45-degree oblique + both side views. If skull silhouette, jaw placement, eye-socket depth, or ear attachment is wrong, correct the major masses before shaping individual features.

## Layer 2: soft tissue and underlying function

- **Eyes:** Embed approximately spherical eyeballs into sockets. Sculpt upper and lower lids wrapping over the globe, with visible lid margin thickness, tear caruncle, and inner/outer canthus. The upper lid overlaps part of the iris on a neutral face in many subjects; do not enforce an exact universal overlap. Preserve natural orbital fat/skin and upper lid fold variation; epicanthal folds are normal anatomy, not errors. Sclera is not pure white; avoid overlarge spherical cartoon eyes and painted-on eyelids.
- **Brow:** Build supraorbital ridge, glabella, corrugator/procerus soft-tissue transitions, and underlying frontal contour. Brows must follow the brow bone in volume; flat painted strokes on a featureless forehead look false. For interchangeable tattoo patterns, preserve a **neutral underlying brow region**; keep hair/ink masks separate from facial pigment and normal.
- **Nose:** Distinguish forehead-to-root transition (radix/sellion), bony upper nose, upper lateral cartilaginous middle vault, soft nasal tip/lower lateral cartilages, alae, columella, nostril rims and alar-cheek crease. Nasal width, tip projection, bridge height, nostril opening orientation and alar flair vary independently. Do NOT simply extrude a prism from the face. Inspect profile and underside; nostrils must have plausible openings and wall thickness, not dark painted triangles. Nasion (anatomical point) and sellion (deepest root groove) are NOT interchangeable.
- **Cheeks and perioral area:** Create malar fat pads, lower eyelid/cheek junction, buccal fullness, nasolabial transition, orbicularis oris volume, vermilion borders, philtrum columns, subtle mouth commissure depth, and mentalis-to-chin transition. Lip tissue is volumetric; a flattened mouth decal will fail in oblique view.
- **Ear:** Model helix rim, antihelix and its branches, scapha, triangular fossa, concha bowl, tragus, antitragus, intertragic notch, and cartilage-free lobule. Ear depth and projection matter as much as front silhouette. Both ears are not guaranteed identical. Ears are more complex than thin C-shaped discs.
- **Neck transition:** Include sternocleidomastoid and submandibular mass only as much as required for the requested minimal upper neck. Do not accidentally export torso.

**Gate B:** Inspect five crops without skin textures: left/right eye sockets, root/dorsum/tip of nose, under-nose, ear relief from profile/oblique, lip-to-chin transition. Identify every surface as convex, concave, or transitional; eliminate generic featureless inflation.

## Layer 3: microform and shading, only after geometry passes

- Sculpt wrinkles/folds from skin tension, anatomy and age; never add noise uniformly.
- Keep face pores at a scale consistent with camera distance; roughness microvariation is spatially correlated with skin regions. Avoid stamping large identical circles.
- Natural asymmetry is acceptable and important. Do not perfectly mirror the finished face; avoid algorithmically random asymmetry as a substitute for coherent anatomical differences.
- Use physically grounded skin pigmentation and subtle feature-dependent color. Do not bake directional lighting into albedo.
- Test texture-free clay, texture-only, and combined PBR views to isolate structural vs shading errors.

## Reject / re-sculpt checklist

| Symptom | Likely geometry fault | Required action |
|---|---|---|
| Looks like doll or mannequin | oversimplified socket, eyelids, midface and jaw | revisit bony/soft forms in clay |
| Nose glued onto face | no radix/dorsum/alar/columella hierarchy | build upper bone and lower cartilage masses separately |
| Eyes appear pasted on | no orbital rim or lid wrapping | seat globe deeper and rebuild lids |
| Ears look misplaced | tragion too anterior, ear too flat or wrong vertical span | adjust attachment and ear anatomy; compare both profiles |
| Head seems too thin in profile | missing posterior vault, weak midface projection | restore cranium depth and zygomatic/maxillary volume |
| Brows look like stickers | wrong supraorbital relief or flat decal | fix brow ridge and conform overlay to skin |
| Skin looks real but person does not | anatomy was skipped | remove texture for diagnosis; repeat anatomy gates |

## Population variability and ethical realism

- Avoid treating any single face, Greek/Renaissance canon, golden ratio, or database mean as the definition of a human. Such canons are not universal; published anthropometric studies show broad variation across groups.
- Use **subject-specific** multi-view landmarks whenever an authorized person is represented. For generic models, use anatomically plausible ranges and varied reference examples. Do not assert racial/ethnic classification from a face or enforce group stereotypes.
- Young, adult and older faces have different cranial and soft-tissue proportions. Defaults target a neutral adult only; do not extrapolate adult proportions to children.
- A high score for photo-landmark overlay is not proof that a head is photorealistic: ears, depth, skin, lighting, and occluded geometry remain separate review tasks.
