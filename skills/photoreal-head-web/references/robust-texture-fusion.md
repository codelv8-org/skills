# Robust multi-view texture fusion (3.1.1)

## Diagnose and repair

Use this module for seams, inconsistent exposure/color and ghosting diagnostics after G4 UV and G5 camera/registration checks. Color consensus is not anatomical correspondence, delighting, or a substitute for source masks. If source images differ in geometry, expression, occlusion or camera alignment, fix those first. Color disagreement can reflect legitimate directional lighting/specular response; never infer that the median is measured albedo.

1. Reserve independent holdout views before fitting. Keep authorized, rectified skin-only training images and calibrations local; no automatic external upload. Record the exact GLB hash and current UV gate. Do not promote a diagnostic projection from invalid UV.
2. Set `blend_mode:robust_consensus` and `consensus_threshold_srgb:0.06` (engineering starting threshold, not Delta E or a universal skin tolerance). The old `weighted_mean` remains available for reproducible comparisons. Prefer measured color correction; `exposure_match:off` is order independent, whereas overlap scalar correction is order dependent and only corrects exposure. Verify no duplicate train images, including resized copies manually.
3. The engine computes per-texel sample visibility and geometry weights as before. It compares observations with component-wise median in sRGB, requires a coherent strict majority of at least two out of three or more observations, and discards discordant samples only in that case. Fuse accepted values in linear RGB. Two conflicting samples or incoherent majority remain ambiguous; preserve a weighted draft, not a trusted measurement. One sample is low evidence, not consensus. Unseen remains transparent. Storage is limited to five million sparse records; reduce atlas size/views if budget exceeds this, without claiming lower resolution preserves all microdetail.
4. Inspect `ambiguous_mask.png` (unresolved), `view_disagreement.png` (maximum sRGB channel spread), `outlier_rejected_mask.png` (where rejection occurred) and `single_view_mask.png`. `view_support.png` counts original geometrically valid views, not final accepted observations or a confidence probability. Per-view report records eligible consensus texels and rejected fraction; flag a view for inspection if at least 512 eligible texels and rejection fraction >=30%. These are review heuristics, not an automatic decision to delete a view.
5. If a view is suspect, compare its pose overlay, source color/white balance and mask with training evidence; recapture/correct or explicitly quarantine it in a new manifest. Save both original and candidate reports; choose using training evidence and inspect independent holdout only for evaluation. Reproject without modifying UV. Compare same-pixel error and coverage; do not trade away difficult areas silently. Request independent review when coverage is insufficient or disagreements remain. Do not release unresolved ambiguous areas. `compose_skin_atlas.py` requires a nonempty `--ambiguity-review-note` for draft composition if conflict/suspect views remain; it checks the ambiguity mask hash and retains that mask. This is not a release attestation.

## Reproducible B1 stress benchmark

```bash
python scripts/benchmark_projection_robustness.py head.glb --skin-material 'Skin PBR' --out private/stress --size 1024 --view-size 768
```

Fixed 8 train yaw angles and 5 distinct holdout yaw angles. Apply +0.16/-0.09/-0.10 sRGB channel shift to one predetermined +45 degree training skin image only. Compare clean mean, clean robust, tinted mean, tinted robust, and reviewed quarantine (remove the predetermined corrupted view, not an automatic decision using holdout). Source atlas is used only to synthesize training and held-out images. Compute pixel-weighted MAE on common support of ALL candidates across all held-out views, and own-support coverage separately. Inspect before/after images, disagreement masks and reported region failures. Do not fit, threshold-tune or select views on holdout. Run repeat stress with other capture defects and independent licensed scans/photos before generalizing.

### Recorded Ban5 diagnostic example, 2026-11-24

| Method | Common-support MAE (sRGB, 0-255) | Whole skin UV coverage |
|---|---:|---:|
| Clean weighted mean | 0.2578 | 46.8244% |
| Clean robust | 0.2577 | 46.8244% |
| Tinted weighted mean | 6.0466 | 46.8244% |
| Tinted robust | 0.8807 | 46.8244% |
| Reviewed quarantine | 0.2616 | 46.5954% |

33,940 skin triangles; 1024 atlas; 768px views. Tinted robust rejected 102,495 samples across 102,495 texels, including all 102,491 eligible observations of the deliberately tinted view. Only +45 degree view flagged. 12,546 ambiguous texels remain, and 18,354 observed texels have one view. Removing the known faulty view lowers coverage by 0.229 percentage points; held-out own coverage remains 98.08-98.64%, 21 unresolved ambiguous texels remain. The clean robust run still had 37 ambiguous texels, so review is necessary even on clean rendered inputs. These are controlled B1 results, not photorealism or real-photo proof. Prior exact UV gate still BLOCKED (92 opposite-winding triangles); no geometry/UV repair, new final head GLB, Blender lighting/browser check or B2/B3/B4 run. Never publish private source asset or capture data.
