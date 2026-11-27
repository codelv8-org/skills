# Azure Celestial Sword Immortal — G1 diagnostic case

**PROTOTYPE_NOT_AAA. Not a game-ready or production-ready character.**

The original reference is an AI-generated concept sheet from the user's conversation. The full front and one small side view were manually traced; the back and detail views are visual context, not calibrated depth. The 1.85 m head-to-floor scale is assumed. A rounded cross-section visual hull was sampled and converted to triangles. An initial 84,998-triangle candidate was repaired for sampling banding and detached fragments; v1 remains a fused silhouette with a featureless head and cannot satisfy G1. No proprietary mesh was reused.

The GLB contains a neutral material, real geometry, 29 inferred skeleton joints, up to four normalized weights per vertex and a 2-second diagnostic bend. This is a G1 technical feasibility experiment, **not** G9 production rigging. The face, hair, torso and cloth are not accepted anatomy or separate costume meshes. No UV, texture maps, high-to-low normal/AO, proper retopology, cloth/hair simulation or production clips are provided. The exact export passed binary diagnostics and trimesh geometry reimport; Khronos validation, actual Three.js runtime and independent visual review were not performed here. There are no production gate seals.

## Open the review lab

Serve this folder: `python -m http.server 8000`, then open `http://localhost:8000`. The downloadable local lab uses pinned CDN Three.js modules (internet needed); the GitHub Pages variant uses the repository's existing vendored Three.js. Static CPU-render views and the GLB download work independently of the interactive renderer. The viewer reports load failures rather than pretending to render a model.

## Reproduce and inspect

Install `numpy scipy scikit-image Pillow trimesh opencv-python` in a virtual environment. Keep the original `refs/concept.png` from the local project; the public repo may only include the downscaled preview. Run:

```sh
python source/build_blockout.py
python source/verify_export.py
```

`evidence/export-verification.json` contains the exact GLB SHA-256 and decoded checks. `evidence/gate-status.json` states blocked stages and defects. CPU orthographic renders are approximate shading of the actual mesh, not Blender/Cycles. Source OBJ and NPZ are included in the local ZIP. Do not use this blockout as a replacement for a licensed anatomical human base.

## Next authoring prerequisites

Use an authorized high-quality full-body human mesh or credible sculpt in Blender. Repair G0/G1 with an independent reviewer, then approve anatomy G2 before constructing layered cloth and hair; use the skill's remaining gates sequentially. Do not optimize or publish as AAA based on triangle counts or a passing GLB metadata diagnostic.
