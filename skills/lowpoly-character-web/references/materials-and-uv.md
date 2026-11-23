# Low-poly materials, UV maps and texture policy

## Choose the least complex material system that expresses the art

1. **Solid palette PBR**: glTF material `baseColorFactor`, metallic=0 for non-metal fabrics/skin, adjustable roughness. No image texture is needed; UV0 can legitimately be absent.
2. **Vertex colors**: compact per-vertex color accents on faces; verify exporter preserves `COLOR_0` and material multiplies colors rather than tinting unexpectedly.
3. **Texture atlas**: one small image for face, hair, costume, emblem or painted stylization. Requires valid UV0 for every mesh primitive using it. Reserve texels for face and important accessories.
4. **Handpainted PBR**: separate BaseColor, Roughness/Metallic, optional Normal, alpha only where necessary. Use OpenGL tangent-space normal convention; non-color maps are interpreted as data, not sRGB albedo.

## Authoring and quality rules

- Use flat, deliberately faceted, or selective smooth normals according to the art brief; not every low-poly asset must use flat shading.
- Do not generate pore or photoreal skin microdetail by default; preserve clean shape planes and material-family separation.
- Use UV0 inside `[0,1]` for normal single-tile atlas delivery. UV overlap/mirroring may be intentional for shared repeatable color, but is unsafe for unique decals/baked AO or per-side lettering; flag the intended strategy.
- Check UV stretching on face, hairline, collars, knee/hip bends, gloves and boots. Leave padding proportional to texture resolution/mipmapping.
- Test textures with a checker; remove checker before final export. Do not bake studio shadows into albedo unless intentionally handpainted for a fixed-light game aesthetic.
- Separate transparency by design; numerous overlapping alpha planes in hair incur sorting and overdraw costs, especially on mobile.
- Manage draw calls: numerous small material/mesh parts can be more expensive than triangles. Profile actual scene instance count rather than blindly merging assets that need independently animated parts.
- Keep master textures separate from runtime-optimized atlases when a source authoring project exists.
- For compression (KTX2, Meshopt, Draco) require loader capability test in the actual website and do not claim a compression gain without file comparison.

## Material review checklist

Matte skin/hair/cloth distinct under normal light; shoes visibly grounded; no emissive surprise; no PBR metallic=1 on plastic; no z-fighting eyebrows, decals or thin cloth; correct alpha blending or cutoff; palette legible in grayscale and small thumbnail; consistent light response in glTF versus Blender.
