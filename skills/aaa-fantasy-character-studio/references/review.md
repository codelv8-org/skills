# Evidence and release contract

Each stage has evidence/G0.json through evidence/G11.json. Start with the example shape; use actual paths and actual independent findings. Candidates are immutable snapshots (G11 exact delivery ZIP, which must exclude the G11 record/seal to avoid a circular hash). Retain all files under the project root; paths must be nonempty, relative, non-symlink escapes. Do not use fake placeholder files as evidence. Reviewer must be a genuinely separate human or independent review agent who inspected the evidence; self-review with a different label is not independent. The script only validates declared fields and SHA-256 integrity, not artistic quality, reviewer identity, content or engine success.

Example record for G0:
```json
{"stage":"G0","candidate":"candidates/g0/brief.json","author":"actual author ID","reviewer":"actual independent reviewer ID","reviewer_type":"HUMAN","decision":"PASS","findings":"Actual observations, assumptions and defects resolved","evidence":{"reference":"refs/turnaround.png","inventory":"evidence/inventory.json","capabilities":"evidence/preflight.txt"}}
```

Required distinct evidence roles (one file/report/contact sheet per role):
- G0 reference, inventory, capabilities
- G1 design_brief, blockout_views, silhouette_review
- G2 clay_views, anatomy_review, part_comparison
- G3 garment_clay, layer_review, bent_pose
- G4 hair_review, armor_review, assembly_views
- G5 wireframe, topology_report, deformation_trial
- G6 uv_layout, uv_checker, density_report
- G7 bake_settings, map_review, seam_review
- G8 material_views, albedo, lighting_review
- G9 rig_review, deformation_review, clip_review
- G10 export_review, engine_review, runtime_report
- G11 final_views, final_comparison, release_review

For G2 and G3/G4 report actual per-region reviews and revision IDs before aggregate PASS. For every comparison record the view/camera, reference status, specific defect, severity, remedy and independent decision. Use silhouette IoU/normalized landmark offsets only if appropriate; they cannot establish photorealism or artistic identity. Record intentionally open edges, UV overlap exceptions and inferred hidden shapes explicitly. Where static/offline scope makes a later role inapplicable, record reason in that role's report; a game profile must not waive engine and deformation evidence.

Run seal sequentially after each genuine PASS, then check. Modifying a candidate, review or evidence invalidates the gate and descendants; redo dependent work and obtain fresh review before resealing. Final exact ZIP hash covers companion artifacts; record contents and verify unpack/reimport. Keep G11 evidence records/seal outside ZIP; deliver them alongside it. Never seal merely to bypass a FAIL. If missing tools or repeated correction fails, return BLOCKED or PROTOTYPE; absent independent review is REVIEW_REQUIRED. Provide limitations and NOT RUN metrics explicitly. Exit zero is evidence integrity only, never a claim of AAA quality or engine certification.
