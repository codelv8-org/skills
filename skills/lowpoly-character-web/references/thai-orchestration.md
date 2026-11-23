# Thai-first orchestration: คำสั่งสั้น บริบทต่อเนื่อง หลักฐานจริง

## Contents

- [Responsibility and defaults](#responsibility-and-defaults)
- [Resolve short requests](#resolve-short-requests)
- [Persistent project records](#persistent-project-records)
- [Structured request contract](#structured-request-contract)
- [Resume and invalidate correctly](#resume-and-invalidate-correctly)
- [Tool orchestration and checkpoints](#tool-orchestration-and-checkpoints)
- [Structural correction and stagnation](#structural-correction-and-stagnation)
- [Profile mapping and honest status](#profile-mapping-and-honest-status)
- [Short Thai examples](#short-thai-examples)

## Responsibility and defaults

รับเป้าหมายจากผู้ใช้แล้วจัดการงานที่เหลือเองภายในขอบเขตที่อนุญาต ใช้ภาษาไทยสำหรับคำอธิบาย สรุปความคืบหน้า และ UI ใหม่ เว้นแต่ผู้ใช้หรือ brief เดิมเลือกภาษาอื่น เก็บชื่อไฟล์/API/สถานะภาษาอังกฤษที่ต้องใช้จริงได้

| Actor | Responsibility |
|---|---|
| User | Supply a goal/reference and changes; resolve a material design choice only when available evidence cannot settle it. Do not require CLI commands or routine part approvals. |
| Authoring agent | Read images/context, resolve meaning, select tools, create geometry, document assumptions, assemble evidence, fix failures, checkpoint artifacts and carry work forward. |
| Independent reviewer | Inspect the exact source/model evidence, identify defects and record a real decision. Label AI review as AI, never HUMAN. |
| `studio_project.py` | Validate explicit request fields, preserve project preferences, register artifacts and plan the next work. It neither understands arbitrary Thai nor sculpts or approves a character. |

Apply precedence **new explicit instruction → saved accepted brief → declared default**. Announce only material new assumptions once, then proceed. Preserve existing preferences when the user changes one field. Do not present a questionnaire for optional input that can safely remain assumed or unverified.

| Missing input in a new project | Working assumption and limit |
|---|---|
| Language | `th`: Thai for explanations and new previews. |
| Style/detail/type | `STYLIZED_LOW_POLY`, `BALANCED`, `UNSPECIFIED`. Inspect the source and refine these assumptions; preserve observed silhouette, proportions, hair, garments and salient equipment. Do not add a demo backpack/palette. |
| Scale | Metres, glTF +Y up, +Z forward and ground y=0; the helper leaves `height_m: null`. Set a declared staging height before modeling. An adult humanoid may use 1.7 m when appropriate; derive no physical height from an uncalibrated image. Choose an appropriate assumption for other characters. |
| Population/tier | The helper starts with `actor_count: 1` and `runtime_tier: NPC`, both assumed planning values for inspection, not a deployment claim. Revise tier using projected size and actual scene needs. |
| Target device | `UNSPECIFIED`. A responsive web preview is useful, but hardware, FPS and mobile capability remain unverified. |
| Clips | Invent none. Use only clips requested now or already in the accepted brief. |
| Rig | The helper starts with `STATIC` and no clips. For a requested animated humanoid explicitly set `rig: DEFORMABLE_SKINNED` along with the requested clips; use `SEGMENTED_RIGID` only for a deliberate mechanical brief. Keep rig intent separate from clips. Initial shape previews are static even when the final model requires a rig. |
| Camera/hidden surfaces | Record unknown projection and inferred surfaces. Use the existing diagnostic/accepted-interpretation branch; missing information cannot become a fidelity PASS by default. |

For an existing project whose brief requests `Idle`, `Walk`, `Run`, `Salute`, “ทำต่อ” retains all four. A later “เอา Walk อย่างเดียว” explicitly replaces the requested clip list. “ไม่ต้องทำ animation แต่เตรียม rig ไว้” means an empty clip list with a rig, so skin/deformation QA still applies.

## Resolve short requests

Read the complete utterance with attachments, conversation decisions and the active project's brief. Resolve negation, scope, exceptions and mixed Thai/English as an agent. Do not choose intent by finding a word in a regex: “ยังไม่ต้องใช้บนมือถือ เอา desktop ก่อน” must not select mobile merely because it contains “มือถือ”. Normalize Thai digits to numeric values when writing structured fields, while retaining the raw text.

| Short instruction | Operational meaning |
|---|---|
| “สร้างจากภาพนี้” | Use the explicitly indicated/current attached reference; inspect the original and route its actual layout. |
| “ทำต่อ” | Recover the accepted brief, recheck evidence and perform the earliest unresolved prerequisite. |
| “แก้ให้เหมือน” | Compare current geometry against the selected source and existing critique; change the underlying geometry and re-render. |
| “ใช้บนมือถือ 50 ตัว” | Update target device and concurrently visible actor count; plan LOD/budget/runtime work while retaining other preferences. |
| “ใช้เดิม” | Retain the relevant existing selection/preferences. It is not a command to apply new-project defaults. |
| “เริ่มใหม่” | Create a new run without deleting old work. For the current character retain the accepted brief/reference unless the user changes that scope; state the reused inputs briefly. |

For a genuinely new character, use the newly selected source and new project scope. Do not carry a previous character's identity or equipment into it merely because files exist. If multiple projects are equally plausible, inspect available state and ask one focused selection question only if choosing incorrectly would change the work.

### Reference selection

1. Prefer an explicit file/image/subject selection in the current request, then its attached source, then the active project's registered reference.
2. Treat several attachments as a possible set; inspect whether they depict the same character and whether their views agree. Do not arbitrarily select the first or newest file.
3. Keep original source files, hashes, selected subject, view labels, reviewed crops and `reference_manifest.json`. Never substitute a generated model render for the source without an explicit design decision.
4. For a single observed image, use an explicit view route such as `--view front=...` only when that label is supported. Do not split it into four panels. For a sheet, inspect panel order, safe crop boxes and all extremities/equipment; do not assume the bottom 10% is disposable.
5. If “ภาพนี้” has no available source, recover the previously selected source where context supports it. If no source is available, ask for the image; do not pretend an unrelated or imagined image is the requested reference.

Distinguish routine inferred details from material design choices. Prepare a coherent proposed interpretation and concrete evidence when the source is contradictory. Do useful diagnostic work first, then obtain the necessary acceptance under the existing fidelity contract; never manufacture user approval to avoid a question.

## Persistent project records

Keep private project state outside the installed skill. Store artifacts in the user's project and persist them through the applicable storage workflow. Use these records:

- **`studio_brief.json`:** intended result, selected source paths, preferences and per-field provenance. Preserve whether a value came from the user, existing project or an assumption.
- **`studio_state.json`:** artifact registry, current/previous snapshots, paths, hashes and execution cache. This is not an approval record or substitute for gate evidence.
- **`studio_history.jsonl`:** chronological raw requests, resolved changes, assumptions and restart/invalidation decisions. Append decisions; keep previous attempts reviewable.

เมื่อเริ่มใหม่ ให้เก็บที่มาของค่าที่รับต่อมาจริง ๆ: ค่า `ASSUMED` ต้องยังเป็นสมมติฐาน ไม่เปลี่ยนเป็นค่าที่ผู้ใช้ยืนยันเพียงเพราะย้ายโครงการ เก็บ `inherited_from` แยกจาก source เดิม และเคารพ provenance ที่ระบุชัดในคำขอใหม่

Adopt an existing part-stage project with `--stage-project`. Read its real `project.json`, reference manifest, assessments and gates. Do not call stage initialization over it or silently manufacture missing approvals. Import known preferences from conversation/files explicitly; do not use the procedural demo `character_spec.json` as an accepted design brief.

## Structured request contract

Write a JSON request after interpreting the sentence. Use `raw_text`, `intent` and `changes`, plus optional `provenance`; `intent` is one of `create`, `continue`, `refine`, `update`, `restart`. Keep `changes` flat. Supported keys are:

`title`, `language`, `style`, `detail`, `character_type`, `height_m`, `rig`, `clips`, `device`, `actor_count`, `runtime_tier`, `constraints`, `must_match`, `source_files`.

Example resolved request:

```json
{
  "raw_text": "ใช้บนมือถือ ๕๐ ตัว ไม่ต้องมี animation",
  "intent": "update",
  "changes": {
    "device": "MOBILE",
    "actor_count": 50,
    "clips": []
  }
}
```

Use `language: th|en`, `detail: LOW|BALANCED|HIGH`, `rig: STATIC|DEFORMABLE_SKINNED|SEGMENTED_RIGID`, `device: UNSPECIFIED|MOBILE|DESKTOP|MIXED` and `runtime_tier: HERO|NPC|CROWD`. Supply a positive integer for `actor_count` and a positive finite number or `null` for `height_m`. Use arrays of unique nonempty strings for `clips`, `constraints`, `must_match`, `source_files`; an empty array is allowed. Other fields are nonempty strings. Resolve source paths relative to the request JSON, or use absolute paths. Do not invent additional request keys.

Omitted fields mean **preserve existing**. An explicit empty list means empty, not unknown. Keep rig separate from clip selection; the example does not request removing an existing skeleton. An empty `changes` object is valid for continuing work. When adding clips to a new static brief, explicitly choose the appropriate rig in the same request; the helper rejects clips with `STATIC` instead of guessing. A rejected structured request is a schema problem to fix, not evidence that the user's Thai is invalid.

Optional `provenance` maps only changed field names to `USER`, `PROJECT` or `ASSUMED`. Mark agent-selected defaults/estimates `ASSUMED` and recovered preferences `PROJECT` rather than recording them as direct user instructions. For example, `"provenance": {"height_m": "ASSUMED"}` documents an agent-selected staging height.

The helper may validate numbers or normalize known identifiers. Such validation is not semantic understanding. Natural-language negation, “เดิม”, implied references and design ambiguity remain the agent's responsibility. Retain `raw_text` so a later turn can audit the interpretation.

## Resume and invalidate correctly

Run `plan` after recovering context and applying explicit changes. Recompute real part gates through `stage_pipeline.py`; never trust a cached `current_stage`, `PASS` string or old approval digest. The first unresolved prerequisite limits work. Complete G0 before gated authoring, follow the six shape stages in order, then keep topology/material, rig/pose, LOD/budget, target runtime and preview obligations visible. A planner may identify missing evidence without being able to validate it automatically.

| Change | Evidence to revisit |
|---|---|
| Device, actor count, runtime tier | Scene assumptions, budget/LOD plan and target-device performance. Unchanged geometry does not lose its fidelity evidence solely because the device changed. |
| Requested clips | Clip completeness, sampled motion/deformation and any workload-dependent runtime measurement. Do not restart unchanged reference intake or shape modeling. |
| Rig/weights/topology | Relevant skin, pose and geometry regression checks; preserve shape acceptance only where unchanged geometry and its evidence still justify it. |
| Reference selection or accepted design | Intake/calibration, affected fidelity and dependent artifacts. Preserve originals and previous decisions. |
| Geometry/exported shape | Affected part evidence, integration regressions and dependent technical/runtime evidence tied to the old snapshot. |
| Render, mask, camera, landmarks, rubric | Fresh review of the changed evidence context. Never copy a new digest onto an old approval. |
| Title/language | Presentation/state metadata; do not rerun unrelated modeling. |

If a device update later causes mesh optimization, the mesh change creates its own fidelity/deformation revalidation obligation. Changing a clip list may leave static shape acceptance valid while invalidating measured animation workload. Dependency-specific invalidation must not become a way to reuse a benchmark of a different workload.

Use `NOT_APPLICABLE` with a scope reason for work explicitly excluded by the brief, such as clip checks on a static asset. Do not label skipped tests PASS. A rig without clips still needs relevant deformation checks. No short instruction, including “ทำต่อ” or “ใช้เดิม”, authorizes advancing past a failed gate.

## Tool orchestration and checkpoints

Use `python scripts/studio_project.py --help` for exact arguments. Keep the orchestration helper responsible for reusable paths and bookkeeping, while the agent supplies real inputs and decisions.

| Command | Intended use |
|---|---|
| `init` | Create orchestration records from a resolved request; use `--stage-project` when adopting existing stage work. |
| `update` | Apply a resolved request patch while preserving unspecified fields and recording provenance. |
| `plan` | Recover the next permissible action from project state and current gate evidence. |
| `preflight` | Check available tool/filesystem capabilities; treat success as tool availability only. |
| `intake` | Register an agent-authored source-reading manifest bound to the brief's exact source hashes; it does not crop images or approve calibration. |
| `checkpoint` | Register an isolated static stage GLB with its supplied reference/render/QA paths and create the stage preview. It does not play skinned animation. |
| `restart` | Create a new run, retaining the chosen brief/source context and preserving old artifacts; start fresh evidence. |

Example invocation pattern for a new orchestration record over existing stage work:

```bash
python scripts/studio_project.py init --project character_project --request initial_request.json --stage-project existing_stage_project
python scripts/studio_project.py intake --project character_project --manifest source_reading.json
python scripts/studio_project.py update --project character_project --request request.json
python scripts/studio_project.py plan --project character_project
```

Prepare the source pack with `reference_intake.py`, inspect the crops and write the separate `source_reading.json`. Supply `source_sha256` as the complete list of actual current source hashes from the brief; `layout_notes`, `proportion_notes`, `camera_notes` as meaningful strings; and `views` as a nonempty list of objects with unique `name`, `basis: OBSERVED|INFERRED|UNKNOWN`, and `notes`. Optional `crop_px` is a reviewed integer rectangle `[x0, y0, x1, y1]`. The helper checks this record against current source bytes; the agent still verifies that notes, labels and crops are true. The crop generator's `reference_manifest.json` is not automatically this intake schema.

For each substantive **static stage** export, checkpoint the actual model and reference/render/QA paths. Include current and previous attempts, matched reference views, the comparison board and its real gate report where present. Build the preview even for a failed HEAD attempt. Keep missing or stale evidence labeled honestly instead of generating placeholders that imply review.

```bash
python scripts/studio_project.py checkpoint --project character_project --model attempts/head_02.glb --stage HEAD --renders-dir attempts/head_02_renders --reference-dir review/reference/head --qa attempts/head_02_gate.json --out export/head_preview
python scripts/studio_project.py restart --project character_project --out character_project_new --request restart_request.json
```

`checkpoint` requires a real `--model` and `--renders-dir`; `--stage` identifies the isolated part. `--out` defaults to the project's `preview` folder. A supplied `--qa` must bind that model with `model_sha256`; omitting it produces structural inspection only, never a fidelity approval. Forward optional source-sheet, comparison, review-content and camera-view inputs using the helper's supported arguments. Keep prior model snapshots immutable so before/after comparison remains meaningful.

For final skinned/animated exports use `build_preview_site.py`, or a verified Three.js/R3F path when required features exceed that viewer's support. Do not feed skinned animation into the static stage checkpoint and imply it was played. If a viewer cannot load the asset, fix its route or report that limitation. Do not replace geometry with a picture and call it interactive 3D. A software 3D fallback remains labeled separately from GPU rendering.

Tie current preview status to the exact artifact and fresh evidence, not an arbitrary `status` field in an imported JSON. Keep Thai explanations beside machine codes. Record preview-building success separately from actual browser interaction, rendering correctness and target-device performance. Preserve the complete site and assets, not just its `index.html`. Local preview generation does not imply public deployment.

Do not stop after printing a plan when authoring/review work is available and authorized. Continue the actual work, checkpoint and iterate. When a real capability or material design question blocks progress, deliver the best current artifact and a specific next action; do not make the user reconstruct the workflow.

## Structural correction and stagnation

When asked “แก้ให้เหมือน”, inspect the original, current model, multiple registered views and the last independent critique before editing. Select a small ranked set of concrete defects in the current permissible part. Preserve world scale, approved global anchors and supported camera framing.

1. **Diagnose mass and proportion first.** Compare head width/height, cranium depth, forehead slope, cheek/jaw planes, chin projection, ear location/depth and hair volume in front/profile/back views. For later parts inspect torso depth, shoulder/hip ratios, limb lengths, hands/feet and large outfit volumes. Use observed proportions rather than generic anatomy presets.
2. **Edit the shape that causes the defect.** Move/reshape the skull, jaw, cheek, ear or hair surfaces; fit a suitable base, sculpt or rebuild meaningful topology when needed. Decorative eyes, nose markers, eyebrow strips, facet colors and lighting cannot fix an incorrect head mass. Do not add detached primitive decorations and present them as repaired facial anatomy.
3. **Check the actual change.** Export real GLB geometry, render the same supported views in clay/material modes and compare with the preceding attempt. A changed file hash proves changed bytes, not an improved silhouette or even a meaningful vertex change. Inspect the corrected surfaces and measure only properly registered evidence.
4. **Re-review independently.** Give the exact source/current/previous artifacts and brief to a distinct reviewer. Ask for concrete findings, not the desired verdict. Preserve failed attempts and do not carry ratings or approval pins forward.
5. **Break a stagnant approach.** If consecutive attempts retain the same critical defect, inspect why: wrong source interpretation, camera assumptions, coarse topology, an unsuitable base, or an authoring method unable to reshape the region. Change the method or base and make a substantive correction. Repeating color/facet/feature-marker edits is not progress on a structural failure.
6. **Respect the limit.** If the available toolchain cannot create the required geometry, keep the stage `REVIEW_REQUIRED` and provide the prototype, observed defect list, usable source/preview and the concrete modeling work still needed. Do not lower thresholds, modify source masks, move cameras, invent review or assemble later parts to conceal the failure.

This loop is an authoring discipline, not an automatic face-recognition or sculpting system. An unclear reference may require a documented accepted interpretation; improving an unjustified IoU is not a substitute.

## Profile mapping and honest status

`inspect_character_glb.py` and `scene_budget.py` use **different profile names**. The first checks structural/file thresholds; the second estimates character/scene costs. Use both where applicable.

| Planned scene tier | `scene_budget.py --profile` | Initial triangles / primitive submissions | Corresponding `inspect_character_glb.py --profile` triangle cap |
|---|---|---|---|
| HERO | `hero` | 12,000 / 8 | `balanced`: 12,000 |
| NPC | `npc` | 5,000 / 4 | `mobile`: 5,000 |
| CROWD | `crowd` | 1,500 / 2 | `icon`: 1,500 |
| Deliberately heavier asset | Explicitly justified custom budget | Measure the actual use case | `hero`: 25,000; this is not the scene HERO cap |

Use an explicit `--max-triangles` override only when the brief/measurement justifies it; record why. `npc` and `crowd` are not valid inspector profile names. Inspector `mobile` does not prove mobile performance, and `icon` does not make an animated crowd efficient.

```bash
python scripts/inspect_character_glb.py export/character.glb --profile mobile --json reports/structure.json
python scripts/scene_budget.py export/character.glb --profile npc --instances 1 10 30 50 --json reports/scene_budget.json
```

Add skin/animation flags and requested clips from the actual brief. Select LODs by projected size as well as population: “mobile 50 ตัว แต่ตอนซูมต้องเห็นหน้า” may need a detailed near LOD and cheaper far LODs. A smaller file or fewer triangles alone is not an observed performance improvement.

| Code/evidence | Thai explanation to use |
|---|---|
| `PASS` for one gate | ผ่านเฉพาะการตรวจนี้ พร้อมหลักฐานของไฟล์รุ่นนี้ |
| `REVIEW_REQUIRED` | ยังต้องแก้/ตรวจ พร้อมชื่อข้อบกพร่องหรือข้อจำกัดที่แท้จริง |
| `NOT_TESTED` | ยังไม่ได้ทดสอบ หรือหลักฐานปัจจุบันยังไม่ครบ/ไม่สด |
| `BLOCKED` | ขั้นก่อนหน้ายังไม่ผ่าน หรือข้อมูล/หลักฐานใช้ไม่ได้ พร้อมสาเหตุ |
| `UNVERIFIED` | เป็นสมมติฐานหรือยังยืนยันไม่ได้ |
| `NOT_APPLICABLE` | ไม่อยู่ในขอบเขตที่ขอ พร้อมเหตุผล; ไม่ใช่ PASS |
| `WEB_PREVIEW_ONLY` | มีไฟล์เว็บพรีวิว แต่ยังไม่ได้ยืนยันการทำงานจริงในเบราว์เซอร์ |
| `PERFORMANCE_NOT_TESTED` | ยังไม่มีผลวัดบนอุปกรณ์/ภาระงานเป้าหมาย |

Never translate silhouette IoU or a rubric rating into “เปอร์เซ็นต์ความเหมือน”. Uncalibrated views remain diagnostic; hashes do not authenticate a reviewer; estimated submissions are not measured renderer calls/FPS. Only the complete requested acceptance evidence can justify `PRODUCTION_READY`.

## Short Thai examples

| Request and context | Required handling |
|---|---|
| “สร้างจากภาพนี้” + one image | Select the attached source, inspect its view and preserve full anatomy; mark unseen geometry inferred. |
| “สร้างจากภาพนี้” + four-view sheet | Inspect panel order/crops; retain all hair, shoes and equipment. |
| “ทำต่อ” after failed HEAD | Recover preferences, recompute gates and correct HEAD; do not begin TORSO. |
| “แก้ให้เหมือน” after a preview | Diagnose concrete shape differences and change geometry before re-render/review. |
| “ใช้บนมือถือ ๕๐ ตัว” | Resolve 50 simultaneous actors and mobile target; preserve other preferences. |
| “mobile 50 ตัว แต่ตอนซูมต้องเห็นหน้า” | Plan near/far LOD needs and runtime validation without discarding close-up fidelity. |
| “ไม่เอา animation เอาโมเดลนิ่ง” | Do not invent clips; retain applicable reference/shape/web checks. |
| “ไม่ต้องทำ animation แต่เตรียม rig ไว้” | Keep rig intent, empty requested clips, and skin/deformation QA. |
| “ยังไม่ต้องใช้บนมือถือ เอา desktop ก่อน” | Resolve desktop scope despite the negated mobile word. |
| “ใช้เดิม” with mobile/30 actors/Walk-only saved | Preserve those values; no default actor-count or clip reset. |
| “ทำต่อ ใช้ภาพเดิม แต่เอา Walk อย่างเดียว” | Retain registered source/project, replace requested clips with Walk, resume the earliest unresolved prerequisite. |
| “เริ่มใหม่ ใช้ภาพเดิม ไม่ต้องมีกระเป๋า” | Create a new run, preserve old work, retain the source, record the changed design and start fresh evidence. |

Use these as workflow examples, not an NLP benchmark that a keyword parser can pass. For independent forward tests supply the task, necessary context and raw artifacts without supplying this table's expected outcome.
