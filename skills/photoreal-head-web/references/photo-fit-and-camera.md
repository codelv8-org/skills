# Camera, photographic matching, and objective visual overlays

The target is **a believable 3D sculpture in multiple views**, not a 2D image with a face painted on it.

## Reference quality hierarchy

1. **Best:** authorized multi-view scan or calibrated photogrammetry / 3D stereophotogrammetry, with usable mesh/camera and license.
2. **Good:** front + left and right profile + 3/4 photos of the same subject, neutral expression and similar lighting, plus camera metadata/scale when available.
3. **Limited:** a single frontal photo. It cannot constrain nose projection, ear depth, posterior skull, nostrils or occluded contour. Mark these as inferred and request side views only if likeness is the goal and the missing evidence changes the outcome.
4. **Generic:** written face description + anatomically credible licensed base mesh; do not imply match to a real individual.

Before landmarking: check face alignment/neutral expression, facial occlusions, camera tilt, camera yaw/pitch/roll, focal length and cropping. Avoid distortion from close phone selfies. When photographing intentionally, place camera farther away using an appropriate portrait focal length and face level; exact settings are context dependent. For model comparisons, **replicate the source camera projection** where possible rather than force an orthographic render to match a perspective reference.

## Rendering registration

- Save separate front, 3/4 left/right, profile left/right, and subnasal clay renders; preserve fixed cameras for repeatable iterations. Use the same neutral expression as references.
- Annotate a JSON of *visible* 2D landmarks in each reference photo and corresponding Blender-render screenshot. In each record, `coordinate_space=image_pixels_xy_down`, `image_size=[width,height]`, `view` matches exactly, and `points` contains names mapped to `[pixel_x,pixel_y]`.
- For a **front** image, provide at least 3 eye-corner anchors from `en_l/en_r/ex_l/ex_r` and >=5 common points overall. For a **profile**, provide at least 3 anchors from `n/prn/sn/gn` and >=5 common points overall. Record ears where unobscured.
- Run `scripts/compare_photo_landmarks.py`. It performs scale/rotate/translate **similarity registration only**; residuals are normalized to outercanthal distance for frontal views or `n`-`gn` distance for profiles. It does not recover camera intrinsics or 3D depth.
- Inspect the per-feature errors and overlay image. A high nose-tip error means investigate nasal profile, but first exclude camera mismatch or mislabeled points. An apparently close match in one camera is not enough; review side views.
- The default relative RMS threshold `0.04` is an **engineering starting point**, not an anthropometric law, a validated biometric metric, or a promise of likeness. When reference fidelity/camera is poor, flag *camera mismatch* before modifying a healthy anatomical model to fit a bad photo.

## Example

```bash
python scripts/compare_photo_landmarks.py \
  inputs/reference_front_landmarks.json inputs/render_front_landmarks.json \
  --threshold 0.04 --json reports/front_photo_fit.json \
  --overlay reports/front_landmark_overlay.png

# Optional, only when the individual has authorized use of the photo locally:
python scripts/compare_photo_landmarks.py \
  inputs/reference_front_landmarks.json inputs/render_front_landmarks.json \
  --photo inputs/reference_front.jpg --overlay reports/front_on_photo.png \
  --json reports/front_photo_fit.json
```

**Result** `PASS_PHOTO_FIT_ONLY` means only camera-aligned annotated points fall within engineering threshold. `REVIEW_REQUIRED` means model/annotation/camera must be inspected; `BLOCKED` means input data is insufficient/invalid. Never promise person-identical reconstruction or biometric matching.

## Automatic detector option (do not over-interpret)

Google MediaPipe Face Landmarker currently exposes 478 estimated 3D facial landmarks from RGB images, but its coordinates are image-normalized (`x/y`) and `z` is relative rather than a metric depth scan. Use x/y to *assist* 2D annotation only, manually verify landmarks and camera correspondence; do not use the estimated `z` as physically measured nose projection or posterior head shape. Ear anatomy is outside the typical dense facial mesh. Make detector installation optional; never upload a person's face to third-party services without permission.

## Privacy and references

Use photos with permission and rights to process. Keep input/source portraits locally if the workflow calls for ephemeral data; do not bundle reference images into downloadable public assets unless expressly authorized. Track base-mesh/license attribution. Camera calibration and matched render images are part of evidence, not optional decoration.
