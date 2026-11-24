# Surface and material evidence gates (v3)

Retain G0–G3 anatomy gates. Split G4 onwards into independent decisions. All failed checks loop back to the earliest failing stage; never disguise with lighting/noise. Report `BLOCKED` / `REVIEW_REQUIRED` for missing tools, maps, screenshots or authorization. Drafts remain available; final export is a promotion of the **exact reviewed candidate**.

| Gate | Required evidence |
|---|---|
| G4 Topology and UV | Anatomically placed seams; directional checker front/profile/3/4; uncompressed candidate, numeric atlas QA + anisotropy/density heatmaps, manually reviewed seams/UV padding and critical regions |
| G5 Registration | Atlas version/hash; actual GLB triangle/barycentric anchors plus independently annotated texture landmarks; source rights and unseen areas; no shifted or mirrored features |
| G6 Skin maps | Unlit diffuse, image-backed normal and MR maps; region masks, provenance, explicit skin material and non-metallic; inspect channel/color space, pore scale, tangents, roughness and bake errors |
| G7 Multi-light QA | Fixed-camera soft/side/rim lighting and detail close-ups; manually compare to reference or credible generic human surface; don't equate procedural noise with measured skin |
| G8 Runtime and release | Actual browser front/profile and brow-switch screenshots; structural GLB audit; desktop/mobile budget and actual runtime checks; exact candidate hash matches anatomy export and surface manifest |

Commands (relative to the skill folder):

```bash
# Export anatomy-gated candidate after geometry and baked maps are ready.
blender -b source/head_uv.blend --python scripts/blender_export_head.py -- \
  --collection HEAD_WEB --output export/head.candidate.glb --report reports/export_qa.json \
  --release --anatomy-report reports/anatomy_qa.json --manual-anatomy-reviewed
# For specific likeness also pass --likeness-requested and relevant --photo-fit-report files.
python scripts/inspect_glb.py export/head.candidate.glb --max-triangles 90000 --max-mb 25 --json reports/glb_qa.json
python scripts/validate_head_surface.py export/head.candidate.glb --skin-material Skin --winding cw --report-dir reports/surface
# Set winding only after checker verification; cw is an EXAMPLE, not a universal convention.
# Fill surface_manifest.json from actual candidate, verified atlas and independently annotated features; review and hash evidence images.
python scripts/validate_head_surface.py export/head.candidate.glb --skin-material Skin --winding cw --report-dir reports/surface \
  --manifest reports/surface_manifest.json --anatomy-export-report reports/export_qa.json --promote export/head.glb
```

Requires Python 3, NumPy, Pillow for surface and regionalization tools. Keep `--promote` off while iterating. `PASS_NUMERIC_ONLY` is not final. `PASS_SURFACE_EVIDENCE` verifies files, numeric registration, hashes and attestations, not the authenticity of the screenshot or a guarantee of realism. No model may be described as browser-validated without actually opening it; fill reviewer, specific observations, and report device/browser/metrics when measured. A screenshot's hash binds the reviewed file; reviewer must verify it represents candidate and lighting conditions. Do not fabricate evidence or set flags programmatically without review. Final promotion additionally requires anatomy exporter report status and matching GLB SHA-256. It also reruns the structural GLB inspector (default 90k triangles / 25 MB, normal map required); change budget deliberately in a reviewed project-specific version rather than bypass the gate. It copies bytes without rebaking/re-exporting; any change invalidates review. If existing final path is occupied choose new revision, never overwrite. `browser_brow_switch` may show two variants in a contact sheet; if not requested, show neutral skin and document scope. Inspect both sides where available. Source .blend, photos, masks and master maps remain private unless explicitly authorized.

Use the manifest templates as blank forms, not passing fixture data. Require unique skin atlas, uncompressed GLB and embedded PNG/JPEG for validation. For compressed assets run all visual/structural checks again on final compressed file with appropriate decoder; this release path intentionally does not certify compressed files. Do not label compressed delivery as checked based on an earlier uncompressed candidate.
