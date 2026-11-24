# Digital skin: acquisition, regional properties and web shading

## Skin is a layered dielectric

Study surface specular, pigment-driven diffuse and shallow/deep subsurface scattering separately. Epidermal melanin and dermal hemoglobin influence color; sebum, skin microgeometry and local hydration alter reflectance. Do not infer demographic traits or universal color from photos. Natural variation is subject- and lighting-dependent. Avoid excessive saturated red, repeated freckles/noise or baked ambient highlights.

| Region | Texture/material direction (validate against reference) |
|---|---|
| Forehead | Restrained T-zone oil variation, forehead lines following anatomy; never uniform orange-peel texture |
| Nose/ala | Regionally visible pores, curvature and subtle local sheen; avoid oversized black dots and baked nostril shadows |
| Cheeks | Fine irregular pores, pigment variation, possible vellus hair; preserve source asymmetry |
| Eyelids/periorbital | Delicate thin skin, fine folds; low generic pore intensity; preserve lid geometry |
| Lips | Separate vermilion color/roughness with directional fine creases; no generic face pores or wet-look plastic |
| Chin | Region-specific pores and hair stubble if appropriate, not repeated pattern |
| Ears | Fine folds and skin detail, subtle scattering difference under backlight, preserve helix and concha geometry |
| Scalp/hairline | Hair follicles/transition only if justified by reference; avoid abrupt pasted hairline |

## Map contracts and authoring

- BaseColor: sRGB, diffuse/pigment only. De-light source photos, use broad and regional variation before microdetail. Do not fabricate photoreal albedo from procedural noise. Texture independently from macro form; high frequency is not a substitute for skin albedo.
- Tangent normal: non-color OpenGL +Y, MikkTSpace-compatible bake with matching triangulated runtime mesh. Preserve real macro normal; layer detail via reoriented normal mapping (RNM) or physically scaled height bake, never naïve RGB addition. Inspect side/rim light and seams. A validator cannot infer Y convention from raw pixels; compare to known directional bump test.
- Roughness: non-color, moderate regional variation not arbitrary fixed thresholds. Use cross/parallel polarization, licensed measured maps or careful painting; use `regionalize_skin.py` only for generic/assisted microdetail. Its region polygons MUST be annotated on actual atlas; it saves masks, a coverage image, modulated micro normal and roughness, not a finished face. Artist controls are heuristics, not measurements. Tune pore size in millimeters versus texel density; avoid tiled repeats, overly steep normals and lip/eyelid pores. Use 16-bit displacement/height source when needed and bake to normal for web.
- Skin metallic effective value = zero. glTF metallic-roughness uses G=roughness, B=metallic, factors multiply texture. R may carry AO when separately wired. Avoid darkening albedo with strong AO. Include optional specular/thickness/scatter/fuzz/displacement master maps and disclose unsupported channels. Specular default dielectric F0 is a starting point, not a guarantee.
- Create masks from actual anatomy/UV: brow region, T-zone, cheeks, periorbital, lips, ears, scalp. Feather between regions and check overlaps, coverage, seam continuity and physical size. For brow catalog keep neutral skin and separate aligned transparent brow design; use tapered strokes with localized density/direction, prevent z-fighting. Do not bake real brows into reusable neutral texture unless explicitly requested.

## Runtime tiers

1. **Mobile:** glTF core BaseColor/Normal/MR + restrained AO; opaque skin, alpha only where appropriate on brows/lashes. Use environment lighting and neutral exposure; no fake scattering baked into color.
2. **Enhanced:** Three.js GLTFLoader + image-backed maps, optional supported KHR_materials_specular, separate detail normal shader with mip/scale safeguards. Treat extension support as version-dependent; test actual browser. Avoid clearcoat on ordinary skin as a default. Correct sRGB for color; non-color for data maps; GLTFLoader handles UV convention, manual replacement textures require correct colorSpace and flipY=false for glTF maps. Use consistent tone mapping, environment, exposure and renderer version.
3. **Cinematic:** custom diffusion/SSS approximation with thickness/region mask and light-dependent scattering, offline Cycles Principled subsurface for source look. Compare real-time renderer under front/side/rim lights. Blender SSS does not export as core glTF PBR; transmission/volume and glass-like transparency are NOT equivalent to diffuse subsurface scattering. Only claim implementation when shader is actually provided/tested. Keep mobile core fallback.

## Diagnose from observable symptoms

| Symptom | Isolate first | Correction |
|---|---|---|
| Face looks painted-on or eyes/nose texture shifted | Unlit base color and landmark registration | Fix camera/visibility/UV correspondence, rebake |
| Waxy/plastic | Flat roughness, overly smooth albedo or too strong specular | Region-driven roughness, calibrated albedo and subtle detail, realistic lighting |
| Orange-peel / sandpaper | Normal-only under raking light | Reduce intensity/scale, region masks, use licensed measured pores |
| Dark/bright seams | UV checker, bake cage, tangent basis, padding/mips | Fix islands, bake dilation and tangent basis |
| Lip/eye texture on wrong region | Region overlay and independent UV features | Correct atlas registration; never hide via filters |
| Blender good, browser wrong | Compare same HDRI/exposure; inspect embedded image/channel settings | Bake unsupported nodes, correct color spaces/normal convention, check extensions |

## Source study

- Weyrich et al., *Analysis of Human Faces using a Measurement-Based Skin Reflectance Model* (SIGGRAPH 2006): https://www.cs.princeton.edu/~smr/papers/skinreflect/ (measured spatial variation; consult original publication).
- USC ICT, *Practical Modeling and Acquisition of Layered Facial Reflectance*: https://vgl.ict.usc.edu/Research/LFR/ (surface and subsurface components).
- NVIDIA GPU Gems 3, chapter 14, *Advanced Techniques for Realistic Real-Time Skin Rendering*: https://developer.nvidia.com/gpugems/gpugems3/part-iii-rendering/chapter-14-advanced-techniques-realistic-real-time-skin
- Epic Games, MetaHuman materials and textures: https://dev.epicgames.com/documentation/metahuman/metahuman-materials-and-textures (production map separation; not automatically portable or reusable).
- TexturingXYZ: https://texturing.xyz/ (multichannel scan detail; license required).
- Three.js color management: https://threejs.org/manual/en/color-management.html ; Khronos glTF PBR: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
