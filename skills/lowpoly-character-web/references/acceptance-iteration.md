# Outcome-based acceptance and revision policy

## Golden rule

For reference-guided character creation, the deliverable is an artistically plausible and technically usable model. An inspector's PASS says the file is parseable, not that the character resembles the supplied image. The skill must maintain **error evidence and corrective loop** until visual, rig and runtime gates are accepted or explicitly unresolved.

## Mandatory artifact loop

1. Make source/reference pack with aligned four-view crops and subject-aware feature list, not only text description.
2. Lock global scale guides, then build HEAD only and render clay front/back/left/right with the same supported camera framing; make a side-by-side board before proceeding to TORSO. Do not independently fit each model silhouette to the source bounds.
3. Reviewer marks each feature 0..5 + evidence per view. Critical head/hair/face and body silhouette need >=4 each, weighted score >=4.3/5; this is a project **review policy**, not objective proof or CV-computed similarity. Record an independent reviewer as HUMAN or AI, with actual evidence and identity distinct from the author; never describe AI review as human approval. Missing ratings/evidence => REVIEW_REQUIRED.
4. Prioritize corrections: (a) distorted silhouette/head/leg lengths, (b) inaccurate face/hair, (c) disconnected/penetrating shoulders/hips and hands/feet, (d) large clothing/gear shape, (e) small badges/colors/roughness.
5. Re-render same cameras after geometry changes; review again. Never use shaders, image generation or camera tricks to hide bad geometry. Show comparisons before/after.
6. After shape approval, do deformation retopo and 45°/90° bend frames; fix any implausible joint fold, broken wrist/feet or salute hand obscuring the face. No numeric-only rig QA.
7. Apply LOD reduction and crowd performance test **without losing important 4-view identity at target screen scale**; verify every new LOD and clip after optimization.

## Release vocabulary

- `ART_PROTOTYPE`: geometry exists but fidelity or topology not approved.
- `RIG_PROTOTYPE`: animated skin exists but bends/poses not artist-approved.
- `WEB_PREVIEW_ONLY`: site files built, browser runtime not tested.
- `SIMULATION_BUDGET_PENDING`: estimated costs reported, real runtime not measured.
- `PRODUCTION_READY`: all requested reference, artistic, deformations and target runtime tests have run and passed with stored evidence.

If tools cannot create a high-quality result, prefer a truthful partial prototype and clear instruction to finish it in Blender over a low-fidelity "production" label.

## Diagnostic evidence from Sentinel S3 v2 prototype

The previous build used scalar distance volumes merged into a single connected body via `marching_cubes` (confirmed from `build_sentinel.py`), and reported ~9,134 total triangles, 17 GLB render primitives, 23 materials, 22 skin joints, 4 named clips. Its existing release report already marked silhouette and manual deformation topology REVIEW_REQUIRED, and browser WebGL NOT_TESTED. The generated four-view preview showed hair spiking/oversimplified rear silhouette, a face lacking source character, rudimentary hands and details and a salute hand obscuring the eye/forehead. These are geometry/art-direction and animation issues, not proof that the reference image was unreadable. Neither 1 connected body mesh nor 4 clips guarantees production quality.

## Why a skill cannot enforce artistic skill with instructions alone

A skill can mandate staged tests, quality rubrics, tool routing, measured budgets and feedback loops. It cannot turn a generic procedural modeler into an expert human sculptor, guarantee faithful reconstruction from ambiguous 2D drawings, or validate real WebGL performance without running browser/hardware. The most effective change is choosing a better base topology/modeling tool **and** making side-by-side visual failure block delivery.
