# Evidence and release contract

Each project has evidence/G0.json through evidence/G7.json. Copy the following shape and fill actual paths relative to the project. Do not use placeholders as evidence. All paths must stay under the project root; retain immutable candidate snapshots. Candidate and evidence files must be nonempty. A reviewer must be distinct from the author and actually inspect the stated evidence; the script cannot authenticate people, image contents or artistic judgment. A seal computes hashes only, not approval. Missing or failed reviews block advancement.

```json
{"stage":"G0","candidate":"candidates/g0/brief.json","author":"actual author ID","reviewer":"actual separate reviewer ID","reviewer_type":"HUMAN","decision":"PASS","findings":"Specific observed results and limitations","evidence":{"reference":"refs/sheet.png","inventory":"evidence/inventory.json","capabilities":"evidence/preflight.txt"}}
```

For G1, record each anatomy region separately in the anatomy report, including actual per-region reviewer findings and model revision, before sealing the aggregate gate. For later stages retain earlier snapshots. The required evidence roles are enforced by gate.py:
- G0 reference, inventory, capabilities
- G1 clay, anatomy, comparison (all four directions and 3/4; per-region checks)
- G2 garment_clay, garment_review, bent_pose
- G3 gear_clay, inventory_match, integration_review
- G4 wireframe, uv_checker, bake_review
- G5 material_views, albedo, normal_review, lighting_review
- G6 export_review, deformation_review, runtime_review (for scoped static/offline cases, document why a check is not applicable; never fake it)
- G7 final_views, final_comparison, release_review

Each role may point to a report/contact sheet, not a fake placeholder. Findings must explicitly state any inferred feature, material defect or measured runtime limitation. For G7 candidate use exact final delivery artifact; release_review must enumerate and hash any companion files, and verify their relationship to the candidate. A new upstream revision or evidence edit invalidates its seal and all downstream seals. Re-review the actual changed candidate before resealing; never use sealing as a way to bypass artistic rejection. Run check after G7. Exit 0 verifies the evidence chain only. Exit 1 means incomplete, invalid or stale.

Suggested comparison: fixed orthographic camera and shared scale, matched full-frame masks and independently annotated landmarks; use mask IoU and normalized landmark distances only as diagnostics. Inspect reference/actual renders side-by-side and identify critical silhouette/feature differences. In uncalibrated concept routes disclose that measurements are approximate. Never transform reference or camera just to inflate a score. Do not claim a numerical photorealism percentage. If repeated corrections fail, change the modeling route or mark PROTOTYPE.

Deliver source/character.blend, export/character.fbx or .glb as scoped, texture maps, rig/LOD if applicable, previews and evidence. Keep private sources out of public releases. Clearly separate concept, prototype, reviewed candidate and released asset. A still render is not an editable model.
