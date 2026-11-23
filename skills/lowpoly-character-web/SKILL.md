---
name: lowpoly-character-web
description: Build, review, repair, rig, animate and optimize original low-poly characters from text, reference images, existing GLBs or Blender models for WebApp, WebGL, Three.js and React Three Fiber. Support short Thai requests such as สร้างจากภาพนี้, ทำต่อ, แก้ให้เหมือน and ใช้บนมือถือ 50 ตัว by preserving project context and orchestrating tools. Use for character likeness, retopology, skinning, animation, interactive previews, LODs, crowd budgets, performance QA or skill refinement. Treat visual fidelity and measured runtime performance as release requirements.
category: UIUX
tags: [3d, low-poly, glb, blender, webgl, three-js]
version: 5.0.0
agents:
  - antigravity
  - claude-code
  - codex
compatibility:
  antigravity: ">=1.0.0"
  claude-code: ">=1.0.0"
  codex: ">=1.0.0"
---

# Low-poly Character Web Studio v5.0 — คำสั่งสั้น ทำต่อจากบริบท ตรวจผลงานจริง

## เป้าหมายหลัก

ส่งมอบ **ตัวละคร 3D จริงที่เห็นความเหมือน ใช้งานได้อย่างมีประสิทธิภาพ และตรวจสอบได้** เริ่มสร้าง `HEAD` และผ่านหลักฐานเทียบมุมมองก่อนทำ `TORSO` แล้วดำเนินงานตามด่านที่กำหนด ผลงานจริงสำคัญกว่าการรันสคริปต์สำเร็จ: คำอธิบาย แผนงาน blockout ทั่วไป หรือ GLB ที่เปิดได้ยังไม่ใช่ผลสำเร็จ หากพรีวิวยังต่างจากต้นฉบับอย่างชัดเจน ให้ตรวจข้อบกพร่อง แก้สาเหตุในโมเดล และทดสอบซ้ำ หากเครื่องมือทำคุณภาพที่ต้องการไม่ได้ ให้ส่ง `PROTOTYPE` พร้อมเหตุผลเฉพาะเจาะจง ทุกโมเดลที่สร้างต้องมี GLB จริงและเว็บพรีวิวที่รันได้ ห้ามอ้างว่าทดสอบด้วย Blender/Chrome/Khronos หากยังไม่ได้รันจริง

**ลำดับงานที่ต้องทำ:** ตรวจและเทียบภาพอ้างอิง/ระบุจุดสำคัญ → กำหนดสัดส่วนรวม → ผ่านรูปทรง `HEAD` → ทำส่วนถัดไปตามลำดับ → รวม topology → ตรวจ deformation/animation ตามขอบเขต → วางงบฉากและ LOD → วัด runtime ที่มีหลายตัวละครจริง → ส่งมอบ สำหรับมนุษย์ที่ต้องเคลื่อนไหวให้ใช้ `DEFORMABLE_SKINNED` เป็นหลัก และใช้ `SEGMENTED_RIGID` เฉพาะงานที่ตั้งใจออกแบบเป็นชิ้นส่วนกลไก ผิวที่เชื่อมเป็นชิ้นเดียวจาก marching cubes **ยังไม่ใช่หลักฐานว่า topology พร้อมเปลี่ยนรูปหรือมีรูปทรงที่ออกแบบเหมาะสม**

## Thai-first orchestration — own the workflow

รับคำสั่งสั้น เช่น **“สร้างจากภาพนี้”, “ทำต่อ”, “แก้ให้เหมือน”, “ใช้บนมือถือ 50 ตัว”** แล้วทำงานที่อนุญาตต่อให้ครบ ผู้ใช้ระบุเป้าหมายและสิ่งที่ต้องการเปลี่ยน; agent รับผิดชอบการอ่านบริบท เลือกภาพ/เครื่องมือ บันทึก brief ทำพรีวิว ตรวจหลักฐาน และแก้ผลงาน ไม่ให้ผู้ใช้ป้อนลำดับ CLI หรือยืนยันงานประจำทุกขั้น อ่าน [references/thai-orchestration.md](references/thai-orchestration.md) ก่อนเริ่ม/ต่อโครงการหรือแปลคำสั่งสั้นเป็นการทำงาน

1. **Recover before asking.** Read the active project, conversation decisions and registered references. Prefer new explicit instructions, then saved project preferences, then declared defaults. Reply and label new previews in Thai unless the user/project specifies otherwise. Explain status in Thai alongside its code, such as `REVIEW_REQUIRED — ต้องแก้รูปทรง`.
2. **Resolve meaning as an agent.** Interpret the whole sentence, negation, Thai numerals and mixed Thai/English; create structured request JSON for `scripts/studio_project.py`. It validates and orchestrates explicit inputs; it is not a Thai semantic parser or automatic sculptor. Missing fields preserve existing values, `clips: []` explicitly requests no clips, and rig intent is independent. Never invent clips or erase an existing four-clip brief because the new prompt only says “ทำต่อ”.
3. **Keep durable context.** Use `studio_brief.json` for preferences/provenance, `studio_state.json` for artifact paths and work cache, and `studio_history.jsonl` for decisions. State is not approval. Adopt existing stage projects with `--stage-project`; keep their source/evidence and re-evaluate, without initializing over them. Use `init`, `update`, `plan`, `intake`, `checkpoint`, `restart` and `preflight` instead of rewriting path glue.
4. **Resume real work.** Recompute gate status and address the earliest unresolved prerequisite. “แก้ให้เหมือน” means inspect and fix specific geometry; “ใช้เดิม” preserves the relevant saved values. “เริ่มใหม่” creates a new run and keeps old artifacts; retain the accepted brief/reference unless the user changes the scope. A new device/count requires new runtime evidence; a source or geometry change requires affected fidelity checks. No command, cache or user shorthand bypasses a failed gate.
5. **Declare useful assumptions once and act.** Use the supplied image or existing selected source; inspect layout before cropping. Do not ask for every optional measurement. Mark uncertain scale/cameras/hidden surfaces explicitly. Ask only when a material ambiguity blocks useful progress, after preparing the available evidence and concrete choice. Never invent acceptance of an inferred design interpretation.
6. **Checkpoint every real export.** Register the actual GLB and create its current/previous preview with reference, renders and truthful QA. Continue authorized edits and independent review without routine permission prompts. If tools cannot resolve a critical failure, deliver the useful prototype, exact correction list and evidence; never call orchestration success production readiness.

## ข้อมูลที่ต้องใช้และการเลือกเส้นทาง

- อ่าน brief ภาพอ้างอิง/ภาพหน้า-หลัง-ข้างหรือไฟล์ 3D (`.glb`/`.blend`) ฉากเป้าหมาย ระยะกล้องใกล้สุด/ไกลสุด จำนวนตัวละครที่เห็นพร้อมกัน browser/GPU/มือถือ และคลิปที่ต้องการ ห้ามถามข้อมูลเดิมซ้ำ เมื่อข้อมูลเสริมขาดให้ประกาศสมมติฐานและใช้สถานะ `UNVERIFIED` ตามจริง
- ออกแบบตัวละครต้นฉบับที่เผยแพร่ได้เป็นหลัก เคารพสิทธิในภาพ/asset และข้อจำกัดของตราสัญลักษณ์ ห้ามอนุมานตัวบุคคลจากภาพถ่าย
- ใช้ 1 world unit = 1 เมตร, glTF +Y ขึ้น และพื้น y=0 **ห้ามอ้างความสูงจริงจากภาพที่ไม่มีหลักฐาน** กำหนดความสูงสำหรับงานให้ชัดเจนและบันทึกว่าเป็นสมมติฐานเมื่อผู้ใช้ไม่ได้ระบุ
- ระบุเส้นทาง `MULTIVIEW_REFERENCE`, `SINGLE_VIEW_CONCEPT` (ส่วนที่มองไม่เห็นเป็นการอนุมาน), `EXISTING_MODEL_REPAIR` หรือ `TEXT_CONCEPT` แยกชนิด `STATIC`, `DEFORMABLE_SKINNED` หรือ `SEGMENTED_RIGID` พร้อมระดับฉาก `HERO`, `NPC`, `CROWD` และจำนวนตัวละครที่คาดว่าจะเห็น
- สำหรับตัวละครมนุษย์จากภาพ ใช้ **Blender/เครื่องมือสร้างโมเดลจริง** เมื่อมี เลือก base topology/rig ที่มีสิทธิใช้งานและเหมาะกับตัวละคร แล้วปรับรูปทรง sculpt/retopo อย่างมีเจตนา การต่อ ellipsoid แยกชิ้นหรือ SDF ทั่วไปไม่ทดแทนงานนี้ หากไม่มีเครื่องมือที่ทำได้ให้ระบุข้อจำกัด และห้ามรับรอง procedural surface ว่าพร้อมใช้งานจริง

## Mandatory gated workflow — never skip a failed earlier gate

### G0: Intake / Reference Evidence

1. Open original reference(s) at full resolution; read silhouette, face, hair front/back/side, garments, seams, badge/bag strap, and accessories. Distinguish observed vs inferred. Labels of camera's LEFT/RIGHT are not anatomical left/right. Record perspective/orthographic uncertainty and inconsistent features across views.
2. Run `scripts/reference_intake.py` with the inspected source layout; use an explicit view for one image, never assume every image is a four-column sheet. Preserve full anatomy/equipment, visually inspect crops and edit `reference_manifest.json`. Annotate normalized landmarks (hair top/chin/eyes/ears, shoulder/hip/knee/ankle/shoes and equipment) with confidence. Establish per-view prioritized feature checklist and geometry ratios **from the supplied images**, not canonical body proportions. Register the agent's source-reading notes and exact source hashes through `studio_project.py intake --manifest`; registration does not approve camera calibration or likeness.
3. Set 3D stage height, camera mapping, +Z forward, and accepted design interpretation. If essential views are absent or contradict, document uncertainty and use the observed-reference or approved-interpretation branch in [references/fidelity-measurement.md](references/fidelity-measurement.md). Preserve the original; label hidden features as inferred. Approximate concept matching remains diagnostic until an interpretation is accepted. Ask about a material unresolved design choice only when necessary; do not request routine approval at every part. Read [references/image-reference-pipeline.md](references/image-reference-pipeline.md).
4. STOP if reference cropping loses character anatomy/equipment, any view is mislabeled, or high-priority design features have not been inventoried. **No generic body mesh yet.**

### G1: Mandatory PART-BY-PART likeness-first building with a hard stop

**DO NOT build the complete humanoid then look at reference resemblance.** Lock only global height/shoulder/hip landmarks from G0, then model in this strict order: `HEAD` (skull/face/hair/ears) → `TORSO` (neck/shoulders/chest/waist) → `ARMS_HANDS` → `LEGS_FEET` → `OUTFIT_GEAR` → `INTEGRATION`. Maintain a consistent world scale and four registered cameras. See [references/part-by-part-studio.md](references/part-by-part-studio.md).

For **each** stage:
1. Extract annotated reference crops/masks for that anatomical region from ALL views where visible (use `scripts/part_region_crop.py` with the SAME region for source and model after global alignment), mark landmark points and unverifiable features. Use a fitted base/head sculpt or high-quality editable meshes, not generic cubes/ellipsoids presented as final facial topology.
2. Build only the requested region (plus translucent global scale guides) in editable Blender collections, with planned seam/attachment anchors. Render **actual exported GLB geometry** from front/back/left/right cameras, with material and clay views, matching source camera framing and world scale where supported. Use `scripts/render_stage_blender.py` for render provenance; its `APPROXIMATE_CONCEPT` label does not establish calibrated correspondence. Do not zoom, crop, mirror, or rescale render to fake shape matching.
3. Require `scripts/part_fidelity.py` evidence: independent nonblank source and render PNGs, calibrated binary part masks, matching image canvas, distinct annotated landmark pairs, comparison board, silhouette IoU, size/center errors, and independent reviewer ratings. Identify the model author and reviewer separately; label the reviewer `HUMAN` or `AI` truthfully. Use another agent for AI review when available; never claim the author reviewed their own work independently or that an AI review is human approval. **IoU is mask overlap, NOT a percentage of character likeness.** Reviewer must inspect eye/nose/ear positions, hair volume/facet shape and stylization even if IoU passes. Read [references/fidelity-measurement.md](references/fidelity-measurement.md) and [references/quality-failure-playbook.md](references/quality-failure-playbook.md).
4. If the image, masked metrics OR any critical visual review fail, **EDIT THAT PART'S REAL GEOMETRY**, export/preview, re-render and re-measure. Keep attempts as evidence. Do not advance and do not improve the numerical score by modifying source reference masks or camera calibration. If no modeling tool can fix the issue, stop at `REVIEW_REQUIRED` rather than promoting to finished.
5. Record a standalone passing gate tied to the precise source model SHA-256 and the independent reviewer's pinned `review.context_sha256`. Changed geometry, images, camera/landmarks or rubric require fresh review; never automatically refresh an approval digest. `stage_pipeline.py` recomputes saved PASS evidence and refuses advancement until all preceding stages pass. It cannot physically prevent manual modeling, so respect this order in the authoring tool as well. The final `INTEGRATION` stage must re-test **all previously approved anatomical parts from the assembled final GLB** to detect seam/scale/shape regressions. Hashes detect changed files; they do not prove authorship, camera accuracy or artistic quality.

**Repair structure before decoration.** Rank defects by silhouette, head/profile mass, facial planes, hair/ear volume, attachment and then small details. Adding eye dots, eyebrows or color facets cannot repair a wrong skull or jaw. If consecutive attempts leave the same critical shape defect, compare actual mesh changes, re-open the relevant proportions/base topology and change the authoring method instead of repeating cosmetic edits. See the structural correction and stagnation loop in [references/thai-orchestration.md](references/thai-orchestration.md). Keep camera/reference evidence stable and request a fresh independent review after substantive corrections.

**Authoring parts separately is not exporting a pile of detached limbs.** Use semantic Blender collections while modeling; weld/retopo appropriate continuous body portions with loop flow at neck, shoulders, hip, elbows and knees. Attach costume, hair and bags as skinned accessories where appropriate. Never simply Boolean Union to create animation-quality topology. Read [references/part-by-part-studio.md](references/part-by-part-studio.md). A model that looks unlike the reference is NOT ACCEPTED even if all six skill scripts pass.

```bash
python scripts/stage_pipeline.py init --out character_project --reference-dir review/reference
python scripts/stage_pipeline.py next --project character_project
# After authoring real 01_head/model.glb plus verified reference/render masks + scorecard:
python scripts/stage_pipeline.py evaluate --project character_project --stage HEAD
# This command is hard-blocked until HEAD is really PASS:
python scripts/stage_pipeline.py evaluate --project character_project --stage TORSO
# After the final merge, re-score all five earlier parts on the same integrated GLB SHA.
```

### G2: Deliberate integrated topology and geometry (only after G1 parts pass)

1. Model facial masses and hair using intentional polygon planes; ears with depth, anatomically located eyebrows above eyes, nose bridge/chin/cheeks, hands/fingers, shoes, equipment placements. **Do not build final faces from generic cylinders/boxes if design clearly needs richer geometry**.
2. For skinned organics, build quad-oriented loops at shoulders/armpits, elbows, knees, groin and wrist; attach/fit clothing to same armature; avoid hidden faces and duplicated intersections. Use Blender retopology from sculpt or licensed base whenever available. Separate accessories okay; 1 Blender object or 1 glTF Mesh is NOT evidence of correct deformation loops.
3. Generic voxel/Marching Cubes/SDF is allowed as **silhouette prototype only**. It requires retopology/artistic approval before final animated character. Keep original faceted look by face normals/materials **after** solving topology; don't collapse the silhouette solely to save triangles.
4. Preserve semantic parts/names for eye materials, badges, gear and bones as needed; avoid 50 separately rendered accessory objects. Read [references/continuous-mesh-rigging.md](references/continuous-mesh-rigging.md) and [references/anatomy-topology.md](references/anatomy-topology.md).

### G3: Materials, UV, styling (after isolated shape gates)

Use flat PBR palette/vertex colors, or controlled texture atlas when warranted; image textures need UV0. Compare material-lit and clay reference side by side. Count **visible render primitives and materials**, not just model object count. Minimize materials and small accessories according to chosen web tier while preserving the visually important reference details. No false claims of accurate skin texture/lettering from source if not actually modeled. See [references/materials-and-uv.md](references/materials-and-uv.md).

### G4: Actual rig/animation validation (if applicable)

1. Use skeleton and normalized skin weights, not rigid parenting masquerading as deformable skin. Fix automatic weights manually. Check shoulder 45°/90°, elbow 45°/90°, knee 45°/90°, knee twist, body bends, fingers, bag strap and face intersections; render the worst poses from front and side.
2. Verify exactly the requested animation clips by **actual sampled poses**, heel/toe ground contact, center of mass, hand-to-temple for a requested salute, loop transition and intended in-place/root motion. Named clips only prove metadata. Preserve previously requested clips when continuing a project; do not create a default list for a new static request.
3. Run both structural inspectors:

```bash
# Example only: a project that explicitly requests these four clips.
python scripts/inspect_character_glb.py export/character.glb --profile balanced --require-skin --require-animations --json reports/structure.json
python scripts/inspect_skinning.py export/character.glb --required-clips Idle Walk Run Salute --json reports/skin.json
```

Use the brief's requested clips in the second command; a missing requested clip is a failure, not a reason to remove it from the check. For static art omit animation requirements and omit skin requirements only when a rig is not requested. A rig with no clips still needs weight/deformation QA. For explicitly mechanical segmented characters use `--allow-rigid` only with documented scope. If artistic pose QA fails, mark `REVIEW_REQUIRED` despite numeric PASS. See [references/skinning-qa.md](references/skinning-qa.md).

### G5: WebApp target, proportions, LOD & scene budget — **mandatory**

1. Choose `HERO`, `NPC`, `CROWD` based on **on-screen pixel height, viewing distance and visible population**, not only total polygons. Preserve plausible world height/metre scale, foot placement, stable pivot/collider and consistent LOD silhouette. See [references/webgl-scene-budgets.md](references/webgl-scene-budgets.md).
2. Initial planning caps (adjust after measuring target hardware): `HERO ≤12k triangles, ≤8 primitives/draw submissions`; `NPC ≤5k, ≤4`; `CROWD ≤1.5k, ≤2`. A 9k model with 17 primitives is NOT automatically accepted for 50-person scene even if file bytes are tiny.
   **CLI profiles differ:** scene tiers use `scene_budget.py --profile hero|npc|crowd`; corresponding triangle caps in `inspect_character_glb.py` use `balanced|mobile|icon`. Its `hero` profile allows 25k triangles and does not mean the 12k scene `HERO` tier. See the mapping in [references/thai-orchestration.md](references/thai-orchestration.md); always run scene budgeting as well.
3. Prefer at least LOD0/LOD1/LOD2 when camera has large distance variation; simplify face/fingers/gear progressively, not distinctive hairstyle silhouette. For many actors use material sharing/vertex colors/atlas, visibility culling and animation LOD. For independently animated skinned clones use correct `SkeletonUtils.clone`, not plain `InstancedMesh` pretending per-instance bones exist.
4. Use `scripts/projected_lod.py --height-m 1.7 --distances-m 2 5 10 20 40 --fov-vertical-deg 50 --viewport-css-height 900` with explicit height **assumption** to inspect approximate CSS screen size/LOD trigger; confirm in engine. Run `scripts/scene_budget.py export/character.glb --profile npc --instances 1 10 30 50 100 --json reports/scene_budget.json`. **Counts are analytical estimates, not FPS**. If over target revise geometry/materials or change deployment count. Export optimized versions only after preserving skin and motion; do not blindly flatten animated glTF. Repeat mesh/rig/visual QA after optimize.
5. Run `assets/crowd-benchmark/` in WebGL on actual target desktop/mobile, with 1/10/30/50/100 visible. Log actual renderer calls, triangles, frame pacing/FPS, viewport/DPR, shadows and clips. Without a browser/hardware test, `PERFORMANCE_NOT_TESTED`; no promise that 30/60 FPS will hold.

### G6: Preview site + visual acceptance (mandatory)

Generate runnable website **after each stage export as well as every final GLB**. Use `studio_project.py checkpoint` to register an **isolated static stage export** and wire `scripts/build_stage_preview.py`; the stage viewer does not animate a skin. Use `scripts/build_preview_site.py` or a verified compatible viewer for final skinned/animated GLBs. Include actual GLB bytes, reference/current/previous comparisons, render evidence, orbit/view presets, material/clay/wire modes where supported, and animation controls where applicable. Display Thai explanations and current evidence-backed status; an old report or stored status cannot approve a changed model. Provide the complete site folder with its dependent assets. Actual WebGL test is needed before `BROWSER_PASS`; static fallback images are not interactive 3D, and software 3D is not WebGL/performance verification. See [references/live-preview.md](references/live-preview.md).

### G7: Artifact and report release gate

For image-guided deliverables, output reference manifest/crops, **completed stage assessment JSON, multi-view mask comparison boards, render provenance and gate history** plus the actual source `.blend` when created, `.glb`/LOD files, skin/structural QA, budget measurements and estimates, preview website and visual QA scorecard with reviewer type. When stopping at HEAD, deliver that useful prototype and its correction list; never fabricate later-stage PASS reports. Provide a complete ZIP when requested. Track statuses separately: `G0_REFERENCE`, `G1_FIDELITY`, `G2_GEOMETRY/TOPOLOGY`, `G3_MATERIAL`, `G4_POSES`, `G5_SCENE_BUDGET`, `G5_BROWSER_PERF`, `G6_PREVIEW`, `G7_PRODUCTION_READY`. If any essential artistic, deformation or WebGL gate is untested, **mark PROTOTYPE/REVIEW_REQUIRED, not 'finished'**. Read [references/acceptance-iteration.md](references/acceptance-iteration.md).

## Practical commands

```bash
# Four equally spaced front/back/left/right panels; review crops manually.
python scripts/reference_intake.py reference.png --layout four-columns --content-y 1.0 --out review/reference
# When subjects overlap panel boundaries, supply manually reviewed normalized crops:
# python scripts/reference_intake.py reference.png --layout four-columns --boxes-json crops.json --content-y 1.0 --out review/reference
# For one observed front image (hidden views remain inferred/unverified):
# python scripts/reference_intake.py --out review/reference --view front=front.png
# Or input independent images:
python scripts/reference_intake.py --out review/reference --view front=front.png --view back=back.png --view left=left.png --view right=right.png

# Requires *actual* model render images named front.png, back.png, left.png, right.png.
python scripts/reference_review.py --ref review/reference --renders previews/matched --board review/side_by_side.png --new-scorecard review/reference_scorecard.json
python scripts/reference_review.py --score review/reference_scorecard.json --json reports/reference_gate.json

# Inspect expected scene cost, then benchmark in browser before claiming FPS.
python scripts/projected_lod.py --height-m 1.7 --distances-m 2 5 10 20 40 --fov-vertical-deg 50 --viewport-css-height 900
python scripts/scene_budget.py export/character.glb --profile npc --instances 1 10 30 50 100 --json reports/scene_budget.json

# Preview actual GLB. If browser unavailable, still package website but label untested.
python scripts/build_preview_site.py export/character.glb --out export/preview
python -m http.server 8765 --bind 127.0.0.1 --directory export/preview
```

## Reusable tools & cautions

- `scripts/studio_project.py` maintains explicit briefs, provenance, plans and checkpoints. It does not interpret arbitrary Thai, model geometry, approve design, authenticate a reviewer or measure target-device FPS. Read [references/thai-orchestration.md](references/thai-orchestration.md) for the request schema, responsibility split and resume rules.
- `scripts/generate_blockout.py` and `scripts/generate_skin_demo.py` are **demonstration-only**; never promote their procedural meshes to reference-faithful production character without geometry redevelopment and visual review.
- `scripts/blender_skin_export.py` assumes suitable pre-authored fitted meshes; it is not a magical converter of disjoint objects to good deformation topology.
- `assets/crowd-benchmark/` provides actual test harness using Three.js/Vite and native `SkeletonUtils.clone`. Requires installation and in-browser measurements. Do not report benchmark as tested just because source file exists.
- `references/part-by-part-studio.md`, `references/fidelity-measurement.md`, `references/quality-failure-playbook.md`, `references/image-reference-pipeline.md`, `references/acceptance-iteration.md`, `references/webgl-scene-budgets.md` contain the decisive checklists; older reference guides remain relevant.

## การรายงานและส่งมอบ

สรุปเป็นภาษาไทยว่า **ขณะนี้ทำถึงส่วนใด เปลี่ยนรูปทรงอะไร ตรวจอะไรแล้ว และอะไรยังต้องทำ** แนบ GLB/พรีวิวของรุ่นที่รายงาน พร้อมสถานะ เช่น `REVIEW_REQUIRED — ต้องแก้ความลึกกรามด้านข้าง` หรือ `PERFORMANCE_NOT_TESTED — ยังไม่ได้วัดบนมือถือเป้าหมาย` อธิบายขั้นถัดไปให้เป็นงานที่ทำได้จริงและทำต่อเองเมื่อได้รับอนุญาตอยู่แล้ว ไม่ผลักภาระให้ผู้ใช้เขียนคำสั่งยาวใหม่

**น้ำหนักของหลักฐาน:** ผลตรวจภาพหลายมุมที่ทำซ้ำได้ > deformation pose และ runtime ที่ทดสอบจริง > โครงสร้าง/น้ำหนัก/metadata คลิป > การรันสคริปต์สำเร็จ > คำอ้าง ห้ามเปลี่ยน `REVIEW_REQUIRED` เป็น `PASS` โดยไม่มีหลักฐานใหม่ ความพอใจของผู้ใช้เป็นข้อมูลด้านรูปลักษณ์ที่สำคัญ แต่ยังต้องระบุและแก้ข้อบกพร่องของ mesh/design ที่เห็นได้จริง
