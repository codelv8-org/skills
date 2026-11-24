# Real head benchmark protocol (v3.1)

Use separate evidence classes. Do not call rendered views photographs or treat real geometry as a measured human scan. Do not use the same image to fit and evaluate appearance.

| Level | Evidence | Interpretation |
|---|---|---|
| B0 | Synthetic triangles, calibrated cameras, masks and controlled colors | Numerical regression (raster, depth, PnP, exposure, leakage) only |
| B1 | Existing textured head GLB, training renders vs held-out renders | Actual asset round-trip benchmark; same mesh and renderer, optimistic color accuracy |
| B2 | Authorized textured scan / scanned head with reference maps | Scan-derived asset round-trip; geometry and reference map may still contain error |
| B3 | Independently acquired, calibrated human photographs with matching neutral mesh/scan, masks, separate train/holdout | Real-photo appearance validation; not necessarily measured albedo |
| B4 | Calibrated reflectance/polarization capture, independently reviewed maps, real browser multi-light comparisons | Higher-confidence material validation; still require v3 gates |

## Run a real asset round-trip

`python scripts/benchmark_head_projection.py head.glb --skin-material 'Skin PBR' --out private/bench --size 1024 --view-size 768 --front-axis +z`

Use Y-up neutral head with known +Z or -Z front, exact UV0 and embedded source BaseColor. This tool renders unlit colors at 8 training yaw angles and 5 held-out angles. Compare front-only and multiview using same cameras, geometry, target skin and render settings. Source atlas is used ONLY by the renderer to synthesize observations and reference truth; projection engine sees RGB images and masks, not atlas data. Holdout angles are disjoint but not statistically independent human captures. Output atlas coverage and MAE/PSNR on observed texels, per-view holdout coverage and color error, and paired same-pixel support. No score for missing texels; always report missing fraction. Gray = missing, not a legitimate texture. View support near hairline/ears and narrow UV seams; inspect visually. Repeat with higher texture detail and real captured photos before assessing generalization.

## Real-photo/scan benchmark

- Use a licensed or consented real scan with synchronized camera poses/photos/masks where possible. Verify consent, license and attribution separately for mesh and images. Keep assets private; do not download or distribute restricted data automatically. HumanScanRepository free sample packages advertise RealityCapture, photographs/masks and metadata: https://humanscanrepository.com/free-3d-human-models/ ; Digital Reality Lab offers credited sample head scans: https://www.digitalrealitylab.com/sample-model/ . Check terms before use and do not assume redistribution/AI rights. Large datasets require local storage. No scan or photos bundled.
- Pre-register protocol: same neutral head/atlas hash, color-calibrated capture, fixed target geometry, approved masks, distinct train/holdout IDs and image hashes, fit/validate anchor sets, source rights, front-only and multiview baselines. Use held-out real photos only for evaluation (not camera-training texture or manual painting). Fit holdout camera to separate shape anchors, not candidate texture. Keep lens and lighting consistent. Inspect exact atlas UV using v3 tool, including winding, density and overlap; diagnostic benchmarking of a blocked mesh does not qualify for release.
- Use `project_face_texture.py`, then `evaluate_photo_holdout.py` on withheld calibrated photos. Set `source_kind:real_photo`; the label is operator provenance, not automatic authenticity verification. Record camera validation, IoU, own-support coverage and common-support residual, regional brow/nose/cheek/lip/ear findings, seams and inference masks, prior baseline, and fixed-light renders. Declare blocked or not tested when missing evidence; compare coverage and residual together, not MAE alone. Do not invent universal threshold or percent likeness. Log benchmark repeatability and runtime separately from perception.
- For true measured reflectance compare with independently acquired cross-polarized diffuse/roughness/specular/normal sources; render under held-out lights in Blender and actual Three.js. Use original v3 anatomy/surface release gates; benchmark cannot authorize release.

## Recorded v3.1 development case

Existing authored head asset derived from CC0 MakeHuman base, 33,940 skin triangles, opaque eye/hair occluders, transparent eyebrow decals excluded. B1 only. 1024 atlas, 768px views; 8 training views vs 1 front baseline; 5 held-out views. UV exact QA found 92 opposite-winding triangles, 0 overlap pairs, 0 degenerate, 0 out-of-bounds; status BLOCKED. Benchmark run is diagnostic; not a fixed or approved model. The public skill contains no source photo, mesh, texture or personally identifying benchmark output. See locally produced benchmark report for measured results. B2/B3/B4 not performed in this development run.
