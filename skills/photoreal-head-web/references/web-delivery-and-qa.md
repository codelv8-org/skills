# Web delivery and quality acceptance

> **v3:** Preserve the anatomy and general guidance below. For current mandatory UV, texture, candidate export and final promotion use [surface-release-gates.md](surface-release-gates.md) and [anatomical-uv-and-registration.md](anatomical-uv-and-registration.md); any earlier final export command is legacy.

## Quality profiles (planning guidance)

| Profile | Triangle target, entire head scene | Texture delivery | Indicative GLB budget |
|---|---:|---|---:|
| Mobile | 15k–35k | 1K–2K | <= 8 MB |
| Balanced | 35k–70k | 2K | <= 15 MB |
| Web hero | 40k–90k | 2K, 4K source | <= 25 MB |
| Close-up desktop | As needed with measured FPS | 2K–4K | Test against user network/device budget |

These are **targets**, not quality certifications or universal performance guarantees. Hair cards, eyes, brows, eyelashes, and accessories count toward total scene complexity. A single 4K RGBA texture can dominate GPU memory and download size; review image dimensions and compressed GPU memory, not just file size.

## 3-stage validation

**Structural (automated)**: GLB header/JSON parse; glTF 2.0; mesh primitives triangles; POSITION/NORMAL/TEXCOORD_0; no unresolved external images; number of materials and textures; total triangle count and file size; no accidental camera/light/non-head objects. Run `scripts/inspect_glb.py`.

**Artist (manual or tool-rendered)**: Face symmetry/asymmetry is natural; skull silhouette and brow ridge credible in profile; eyes not lifeless; ear/pinna proper; mouths/nostrils do not have collapsed normals; checkerboard texture straight enough; no face UV overlaps or stretched eyes/lips; normal bake seam free; no excessive highlights; transparent brow edges soft and not z-fighting.

**Browser (required for "web-ready")**: Load actual GLB in Three.js/React Three Fiber; inspect under at least studio HDR environment and directional light; front, both profile, 3/4, zoom, mobile viewport. Check frame rate and first meaningful render on the intended deployment device. If no real browser test was run, say "Browser validation not completed".

## glTF and website notes

- Use `.glb` when a single self-contained asset is desired. Load with `GLTFLoader`; React Three Fiber and drei can wrap it.
- Embed UV-mapped image maps via supported Principled BSDF nodes, avoiding unsupported purely procedural shader graphs. For normal maps, use tangent space and correct non-color input.
- Apply texture compression (KTX2/Basis) and geometry compression (Meshopt or Draco) **only with tested matching decoders**. These can reduce transfer size but add runtime wiring; do not silently apply an extension that the site's loader cannot decode.
- Avoid large alpha-blended hair-card layers on mobile; check sorting. Eyebrow decals can use a small plane with clean geometry offset from skin, or a shader/material solution if the renderer supports it.
- Consider 2–3 LODs for multi-head catalogs. A face-close-up viewer may demand sharper brow texture while a grid of 20 head previews should use a lighter asset/thumbnail.
- Assets fetched from another origin require the hosting server's CORS settings. Serve model paths through HTTPS in production.

## Browser starter included

`assets/web/HeadViewer.tsx` is an example React Three Fiber component. Install `three`, `@react-three/fiber`, and `@react-three/drei`; place the `.glb` in the app's static `/public/models` directory and call `<HeadViewer url="/models/head_web_v01.glb" />`. The runtime must test scale/centering and environment-light appearance. For a vanilla Three.js site, use `GLTFLoader`/`OrbitControls` directly instead.

## Final report template

```text
Status: completed / partial (state real blockers)
Input: authorized photo set | generic brief | source mesh
3D tool/version: ...
Output: actual .blend and .glb paths / URLs
Mesh: triangles ..., submeshes ..., axis/scale verified ...
UV: UV0 ..., overlap/stretch reviewed ...
Textures: BaseColor ... / Normal ... / Roughness ... / optional masks ...
GLB: file size ... MB / compression ...
QA: structural PASS/FAIL; Blender visual PASS/FAIL; browser PASS/FAIL
Known limitations: inferred shape; SSS differences; unsupported export options; etc.
```

## Authoritative implementation references

- Blender glTF 2.0 exporter manual: https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html
- Khronos glTF 2.0 specification: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- Three.js GLTFLoader: https://threejs.org/docs/pages/GLTFLoader.html

Check the current Blender and Three.js version before changing exporter flags or compression decoders.
