# Anatomy-aware low-poly modeling and topology QA

Low-poly characters must communicate plausible mechanics and identity. Artistic stylization is allowed; *accidental* deformation and placement mistakes are not. Evolve the original source skill's 'anatomy before texture' gate to a whole-body check.

## Body landmark logic (humans and humanoids)

Use local authoring axes +Z vertical; -Y facing; +X subject's anatomical left. Landmark names below are **artist QA markers**, not biomedical measurements or universal proportions.

- Crown / brow plane / chin; ear superior/inferior extents; glabella, nose tip and mouth region.
- Neck base and clavicle/shoulder centers; sternal/cage mass; ribs-to-waist transition; pelvic crest and crotch.
- Shoulder -> elbow -> wrist -> knuckles; hip -> knee -> ankle -> toe pivot. Verify left/right naming and horizontal symmetry unless design is intentionally asymmetric.
- Primary volume ordering must hold in the neutral upright pose; the mesh must have a visible posterior skull, chest depth, hips and foot soles.

## Proportion as an art-directed variable

| Visual type | Starting head-count guide | Characteristic adjustment |
|---|---:|---|
| Chibi | 3-4.5 | Larger head/eyes, short limbs, large feet for balance |
| Soft cartoon | 4.5-6 | Hand/foot emphasis, simple torso |
| Stylized hero | 5.5-7 | Readable shoulder, head and hand shapes |
| Human-proportioned | 7-8 | More natural limb length, still simplified geometry |

These ranges are *artist guides*, not anthropometric facts, scientific thresholds or mandatory acceptance criteria. Different ages, bodies, species and character archetypes vary. Base all decisions on the character brief and multiview silhouette.

## Face quality at low resolution

- Build a convincing 3D cranium, jaw and eye/brow plane; a scaled cube with painted features is a stylistic option only if that is the explicit design.
- Maintain visible separation between eyebrows and eye mass; check brow start/end in frontal and oblique views. Avoid tails that extend unusually far beyond the lateral eye region without stylized intent.
- Eyes should be recessed/attached to the facial volume and not hover far in front of cheeks. Simplified black spheres or polygon decals may be valid for cartoons if intersection and silhouette are intentional.
- Nose supports front and profile identity; simple triangular nose is fine if aligned, not a random prism jutting from a spherical face.
- Ears are laterally attached, with believable size and thickness; compare left/right profile and front, avoid flat discs pasted to front.
- Lips/mouth need at least mouth-line placement and a volume decision; avoid intersections with chin/face.
- Hair is a **volume** viewed from behind, not only front bangs. Preserve distinctive silhouette and clearance for animation.

## Joint deformation topology

**Skinned deformation route:** Place usable edge loops around shoulders, elbows, groin, knees and wrists. Keep enough vertices for bends. Plan topology along deformation flow instead of blindly reducing an already weighted model. Preserve face loops if facial animation/morphs requested. Avoid thin triangles at high curvature, inverted normals, loose edges, zero-area faces and winding errors.

**Segmented rigid route:** Build joints around designed pivots, hide intended overlap (e.g. shoulder armor, knees), avoid gaps from rotations and verify rigid parent hierarchy. It does not need smooth skin weights but must still pass motion checks.

**Static route:** Disconnected clothing/hair pieces may be acceptable; remove accidental penetrations, z-fighting, open backs and duplicate faces. Mesh manifoldness depends on material design and whether the part is intended as closed volume; do not mark an intentionally open cape as invalid solely for non-manifold edges.

## Non-human route

Before evaluating anatomy identify skeleton model: biped, quadruped, winged, serpentine, mechanical. Replace human head counts and joints with the correct species/fictional body's mass distribution, limb articulation and pivot convention. Render motion from side and above, not only front.

## Multiview proof minimum

1. Clay front, front 3/4, left profile, right profile, back and back 3/4.
2. Face close-up front and side for facial character.
3. Wireframe front/side and joint close-ups for skinned assets.
4. Bent elbow/knee/shoulder/hip poses for rigged assets.
5. Thumb-sized silhouette on the intended background.

If images cannot be produced in the current environment, report `NOT_TESTED` and provide exact reproduction commands; never claim to have rotated a browser viewer that was not actually run.
