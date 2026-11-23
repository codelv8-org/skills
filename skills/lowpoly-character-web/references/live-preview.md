# Mandatory live preview after every GLB build

## Contract

A finished character request must include **(1) actual GLB, (2) ready-to-run preview website, (3) captured multiview images, (4) QA report**. Do not deliver only a six-view image or a source snippet. Do not imply the live website is hosted on the public Internet; generated files are local unless deployed by the user's requested workflow.

## Head-first stage inspection

Create a preview after each stage export, including failed HEAD attempts. Use `build_stage_preview.py` to show the source beside the actual current GLB, switch to the previous attempt, inspect supported material/clay/wire modes and view presets, and read the current QA status. Supply source crops, render evidence and reports that correspond to that snapshot. Keep later parts absent until their preceding gates pass.

```bash
blender -b -t 4 --python scripts/render_stage_blender.py -- stages/01_head/model.glb \
  --out stages/01_head/renders --camera-config review/cameras.json --samples 32
python scripts/build_stage_preview.py --model stages/01_head/model.glb \
  --previous attempts/head_previous.glb --reference-dir review/reference/head \
  --source-sheet reference.png --renders-dir stages/01_head/renders \
  --qa stages/01_head/gate.json --diagnostic-board review/head_comparison.png \
  --out export/head-preview --title "HEAD geometry review" --stage HEAD
```

Omit optional inputs that do not exist. Use the stage renderer's glTF-coordinate camera configuration (`target`, `ortho_scale_m`, `resolution`, and per-view `yaw_deg`/`elevation_deg`) to preserve a deliberate framing. Retain `render_manifest.json`: it records the model/image SHA-256, Blender version and camera settings. `UNVERIFIED` alignment (or an explicit `APPROXIMATE_CONCEPT` configuration) and `REST_STATIC` pose must remain labeled as such; neither proves calibrated comparison or animated deformation. Produce part masks separately with a verified object-ID/alpha workflow.

Report current snapshot bounds, triangles and materials as measured asset statistics. Mark primitive submissions for multiple actors as estimates and FPS as untested unless observed. A head-only preview cannot establish the final character's budget or rig suitability. Label failed/untested fidelity clearly in the UI; a photoreal reference panel or a flattering lit view cannot replace a real geometry comparison.

Use the standard viewer below for final/animated GLBs and test only the capabilities actually supported by the chosen viewer. Do not claim animation playback in a stage inspector designed for static shape inspection.

If WebGL cannot initialize, the stage inspector may use its explicit **SOFTWARE 3D** Canvas2D fallback. It projects the parsed GLB geometry and supports interactive orbit, zoom, view and mode inspection; it is distinct from a static screenshot fallback. Use the per-pixel depth buffer for opaque surfaces and wireframe, and clip triangles before the perspective divide. Keep `gpuVerified: false` visible. Verify overlapping faces and hidden edges with reversed triangle submission order, then inspect the real asset from front, side and back in the browser. Software depth and approximate flat lighting do not establish GPU/PBR correctness, WebGL compatibility or target FPS.

## Standard final preview

Immediately after export:

```bash
python scripts/inspect_character_glb.py export/character.glb --profile balanced --require-animations --require-skin --json reports/structure.json
python scripts/inspect_skinning.py export/character.glb --required-clips Idle Walk Run Salute --json reports/skin.json
python scripts/build_preview_site.py export/character.glb --out export/preview --serve --open
```

`--open` uses the machine's default browser; it may be unavailable in headless or remote environments. If the model is static, omit `--require-skin/animations` appropriately and tell the viewer it is static. Other requested clips should replace names. For standalone generation rather than continuous serve:

```bash
python scripts/build_preview_site.py export/character.glb --out export/preview
python -m http.server 8765 --directory export/preview
# open http://localhost:8765/ in a browser
```

Preview website (`assets/preview/`) comes with THREE self-contained files, no npm/CDN needed:

- `index.html`: user-facing dark inspector UI.
- `style.css`: responsive design.
- `viewer.js`: WebGL2 (with WebGL1 fallback), orbit, reset/front/side/back camera views, ambient+directional lighting, PBR base-color approximation, embedded base-color textures, basic glTF node transforms, skinned GLB with <=64 bones per skin in WebGL2 (24 in fallback), named animation clip selector, scrubbing, speed, pause/play, wireframe, grid, file upload/drop, screenshot.
- `model.glb`: built character, auto-copied by tool.
- `preview_manifest.json`: basic metadata and engine limits.

**Viewer capability and limitations:** Standalone web preview is an inspection renderer, not 1:1 equivalent to Three.js/Blender PBR. Handles normal indexed triangle GLB; external texture URIs, sparse accessors, morph targets, cubic spline animation and required extensions/compression may be unsupported. If assets require those features, use verified Three.js GLTFLoader or R3F viewer with correct decoders and report it. Do not silently fall back to a canvas illustration or a static screenshot when live 3D fails.

## Acceptance testing

1. Open **the exported GLB itself** in the site, not a procedurally redrawn approximation. Verify `window.__viewerQA.loaded` and `webglError === 0` in browser devtools. Confirm asset metrics reflect inspected GLB.
2. Orbit through front, both profiles, 3/4 and back; check camera face direction, grounded feet and rear clothing/hat.
3. Play every requested clip, scrub at multiple timestamps (especially knee and elbow maximum angles). Compare visible frames, not just clip names. If skinned: ensure `skins>0`, real `JOINTS_0/WEIGHTS_0`, and deformer behavior; test collision with clothing and props.
4. Test desktop and mobile widths. Capture screenshot of actual browser canvas/UI; include a 6-angle **offline** fallback when a browser cannot launch.
5. Record browser status `PASS`, `REVIEW_REQUIRED`, or `NOT_TESTED` from actual evidence. If an environment's browser network access blocks a local URL, a controlled in-browser GLB load test can validate the renderer, but **do not claim server navigation was tested**.
6. For user output, archive the entire `export/preview/` folder to a ZIP. Linking only `index.html` is insufficient because it depends on local JS/CSS/GLB files.

## Runtime security

- Bind local HTTP server to `127.0.0.1` by default. Do not publish the model under a public URL without user consent. Avoid uploading private image/face references to remote CDNs.
- Treat imported GLB as untrusted data; bound size in deployment, disallow path traversal and external resource loading. The built-in viewer fails closed on external resources and required extensions it does not support. Validate every uploaded model prior to sharing publicly.
