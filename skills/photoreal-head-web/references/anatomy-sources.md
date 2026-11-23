# Verified references and scope of evidence

This is a curated reading list. Links are public reading resources; it is NOT permission to bundle their copyrighted photos, scans, commercial meshes, or data into a skill package. Scientific averages are not universal canonical proportions.

## Anthropometry and landmarks

1. **FaceBase 3D Facial Norms**: https://www.facebase.org/resources/human/facial_norms/ . 3D stereophotogrammetry, landmark coordinates, sex/age-related measures and access rules.
2. **3D Facial Norms Technical Notes**: https://www.facebase.org/resources/human/facial_norms/notes/ . Critically important definitions and pitfalls for `n`, `ex`, `en`, `al`, `t`, `sn`, etc. Some soft-tissue points are difficult to position consistently.
3. **Weinberg et al., 3D Facial Norms Project**: https://pmc.ncbi.nlm.nih.gov/articles/PMC4841760/ . Data collection, 24 standardized landmarks, study limits. The data sample of 2,454 participants does not make population means universal.
4. **Expanding the Classic Facial Canons**: https://pmc.ncbi.nlm.nih.gov/articles/PMC9029890/ . Explains why historical facial rules should not be imposed blindly across diverse people.
5. **Three neoclassical canons: Arabian Peninsula young adults**: https://pmc.ncbi.nlm.nih.gov/articles/PMC4369102/ . Demonstrates mismatch of equal facial thirds and simple orbital/nose canons with measured faces.
6. **3D and direct anthropometry comparison**: https://pubmed.ncbi.nlm.nih.gov/31053285/ . Different measurement methods themselves can produce different normative values: avoid mixing methods.

## Specific head features

7. **Anatomy of the nasal profile**: https://pmc.ncbi.nlm.nih.gov/articles/PMC2526105/ . Nasal bone/cartilage and soft-tissue structures; externally root, dorsum, tip, columella, ala and nostrils.
8. **Auricle structure review**: https://pmc.ncbi.nlm.nih.gov/articles/PMC11651859/ . Helix, antihelix, concha, tragus, lobule and attached external-ear structure.
9. **External and middle ear anatomy**: https://pmc.ncbi.nlm.nih.gov/articles/PMC11630884/ . Additional auricular anatomy and cross-sectional explanations.

## Blender, automation, and web

10. **Blender Studio Realistic Character Workflow**: https://studio.blender.org/training/realistic-human-research/ . Professional blockout, base mesh, retopo, sculpt layers, baking, expression design.
11. **Blender Studio Use of Base Meshes**: https://studio.blender.org/training/realistic-human-research/use-of-base-meshes/ . Explicit recommendation to start hyperrealistic heads from an existing base mesh; an example male `.blend` is listed as **CC-BY**, with attribution obligations. Download from source only when licensed/available; this package does not redistribute it.
12. **Google MediaPipe Face Landmarker**: https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker . 478 estimated landmarks, image-normalized XY and relative Z; not measured 3D subject geometry.
13. **Blender glTF exporter**: https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html . Production material channels, normal maps and extension differences to check in Three.js.
14. **Three.js GLTFLoader**: https://threejs.org/docs/pages/GLTFLoader.html . Runtime loading and renderer checks.

## Working rules

- Confirm at the time of use whether a third-party asset/license remains available, and comply with license / attribution.
- Distinguish scientific source landmarks from artist-defined ear-extent points.
- Do not derive ethnicity, sex, medical diagnoses, age or identity from face pixels to choose a template. Use user-stated, authorized character design targets and subject-specific photos when available.
- The package's engineering thresholds (4% normalized 2D RMS, 8% normalized 3D ratio drift) are intentionally **not scientific diagnostic thresholds**. Adapt them based on annotation/camera precision.
