# Changelog

## 3.1.0 - Real Head Benchmark & Automatic Texture Projection (2026-11-24)

- Add calibrated CPU UV projection with perspective-correct rasterization, depth/mask visibility, angle-weighted linear-light blending, optional overlap exposure matching, PnP RANSAC and independent reprojection validation. Preserve unknown texels and require authorized fallback for composition.
- Add existing-head rendered-view benchmark and independent calibrated holdout evaluator with coverage, same-support error, and duplicate/hash guards. No real-photo or measured-reflectance claim.
- Accelerate exact UV overlap candidate filtering; preserve triangle intersection and release gates. Existing head asset diagnostic: 92 wrong-winding triangles, 0 overlaps.
- Add documentation, manifest templates and regression tests. No source scans or photos bundled.

## 3.0.0 - Anatomical UV & Digital Skin Edition (2026-11-24)

- Preserve anatomy, photo-fit, original GLB tools and viewer. Add explicit canonical atlas/semantic anchors, multiview projection, skin optics and regional material workflows.
- Validate actual GLB UV0 with triangle overlap clipping, winding, degeneracy, bounds, Jacobian anisotropy and relative density heatmaps; inspect embedded skin map channels and numeric landmark registration.
- Add region-mask and supporting microdetail tool driven by actual annotated UV polygons, blank contracts and synthetic regression tests.
- Require anatomy-gated candidate export plus matching candidate/UV hashes, independent landmarks, manual three-light/browser evidence and exact-byte promotion. No automatic claim of realism.
- Blender runtime and real-head visual benchmark remain environment-dependent.

## 2.0 - Anatomy First / Measurement-Driven Edition (2026-11-19)

- Preserve the original Blender UV, PBR microdetail, GLB inspector, UV layout and React Three Fiber viewer tools.
- Add an anatomy atlas covering cranial vault, maxilla, zygoma, mandible, orbital region, nasal bone/cartilage and external ear structures.
- Add curated research references from the FaceBase 3D Facial Norms database, nasal/auricle anatomy studies, Blender Studio and Google MediaPipe docs.
- Add a standard 3D facial landmark vocabulary and explicit Blender coordinate/units rules.
- Add strict optional high-fidelity nose bridge and ear extent markers; quantify subject-specific metric drift when valid independent 3D references exist.
- Add a pure-Python 2D reference-photo vs clay-render landmark registration and overlay, with per-region error summary and non-biometric limitation warnings.
- Add final GLB release evidence gates to the prior Blender export script (draft previews still supported).
- Add JSON templates, manual gray-clay review checklist, realistic head repair prompts and deterministic unit tests.
- Preserve a clear distinction between automatic geometry checks and actual photorealistic appearance.

## 1.0 - Original workflow (2026-11-18)

- Sculpt, retopology, UV0, skin textures, eyebrow decals, GLB export and web viewer workflow.
