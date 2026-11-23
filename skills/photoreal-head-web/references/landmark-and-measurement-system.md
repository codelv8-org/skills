# 3D anatomical landmark system: conventions, measurement, QA

Use FaceBase's 3D Facial Norms definitions as the main vocabulary; supplement with **artist-defined** points for ear extent and glabella. The FaceBase study defined 24 clinically useful soft-tissue landmarks; its subjects and access restrictions do not imply universal ranges for all humans.

## 3D landmark collection and axes

- In Blender create an empty named `HEAD_ROOT` aligned with the unposed head, local **+Z up**, **-Y toward the face/front**, **+X to subject's anatomical left** (viewer sees +X on viewer right in a correctly aligned frontal view). Ensure **1 Blender unit = 1 meter**. Avoid nonuniform root scale.
- Create a `HEAD_LANDMARKS` collection of empty objects named `LM_n`, `LM_prn`, `LM_en_l`, `LM_en_r`, etc. Position each precisely on the intended **surface** anatomical landmark, not on hidden skull or a guessed screenshot pixel.
- Use `scripts/blender_export_landmarks.py` to convert named empties to a JSON file. It removes `HEAD_ROOT` transform from world coordinates. Never rename `.001` duplicates as valid landmark names.
- FaceBase lateral suffix `_l` / `_r` always means **anatomical subject left/right**, not image left/right. Mirror image annotation only when source images are actually mirrored, and record that preprocessing.
- Do not guess an occluded landmark; omit it and explicitly document reduced QA coverage. In `--high-fidelity` mode the nose bridge and ear extent annotations are required, so missing views may prevent release and must be explained rather than invented.

## Landmark definitions

| Code | Location | Note |
|---|---|---|
| `n` | Nasion (soft-tissue nasofrontal landmark) | Do not confuse with deeper `sellion` |
| `prn` | Pronasale, most anterior nasal tip point | Confirm in profile |
| `sn` | Subnasale, columella to upper-lip junction | Confirm subnasal/profile |
| `ls`, `li` | Upper/lower lip vermilion border midline | Use relaxed mouth |
| `sto` | Stomion, meeting of lips at median | Closed/relaxed mouth |
| `sl` | Sublabiale, chin-lip sulcus | Optional |
| `gn` | Gnathion, lower chin contour point | Confirm profile and frontal |
| `en_l/r` | Endocanthion, **inner** eye corner | Do not mark just the visible sclera edge |
| `ex_l/r` | Exocanthion, **outer** eye corner | Caution closed eyes and occlusion |
| `al_l/r` | Alare, outermost side of nasal ala | Validate in both frontal and underside views |
| `ac_l/r` | Alar curvature/crease at cheek | Optional; expression-sensitive |
| `sbal_l/r` | Subalare under lower alar insertion | Optional; hard in some nose types |
| `cph_l/r` | Crista philtri, upper-lip philtral crest | Optional |
| `ch_l/r` | Chelion, mouth corners | Mouth must be neutral |
| `t_l/r` | Tragion, above tragus near ear attachment | Requires lateral view; hair can obscure |

**Additional artist-only landmarks** (NOT part of canonical FaceBase 24): `se` = sellion/root groove; `rh` = approximate surface point over rhinion on the nasal dorsum; `g` = glabella soft tissue point; `pg` = pogonion chin prominence; `sa_l/r` and `sba_l/r` = superior and inferior visible ear extent. Do not label these as FaceBase-defined or assume identical research measurement reliability.

## Core measurements

For strict portrait work, pass `--high-fidelity` to require the supplementary `se`, `rh`, `g`, `pg` and both visible ear-extents `sa/sba`; missing bridge/ear landmarks then block the gate. These are artist QA markers, not validated anatomical diagnoses. Run `scripts/analyze_anatomy.py` to compute **actual 3D Euclidean** distances: outercanthal span, intercanthal span, left/right palpebral fissure length, nasal width, nasal height, nasal-tip projection proxy, morphological face height (`n` to `gn`), mouth width, lip/face vertical spans, tragion span, optional ear height. Keep units and definitions consistent; don't compare Euclidean distance to a 2D photo pixel distance as if they were the same physical measure.

When independent 3D subject landmarks or a licensed scan are available, compare **ratios** normalized to outercanthal width to avoid arbitrary size differences. `--max-drift 0.08` is a **project QA tolerance** for normalized ratios, not a clinical confidence interval; tune to task and source uncertainty. If no independent 3D subject reference exists, don't invent one; mark structural gate as **REVIEW_REQUIRED** even if no gross violations were found.

Basic topological/anatomic checks include subject-left vs subject-right sign, canthus ordering, `n` higher than `sn`, `sn` higher than `sto`, `sto` higher than `gn`, nose tip forward of subnasale, and tragion behind/lateral to outer canthus. Warnings trigger manual review, not arbitrary alteration of genuine anatomical variation. The check only validates explicitly marked points, not the entire mesh; a sphere with well-placed empties must still fail the clay review.

## Example commands

```bash
blender -b source/head.blend --python scripts/blender_export_landmarks.py -- \
  --root HEAD_ROOT --collection HEAD_LANDMARKS --output reports/landmarks_3d.json

python scripts/analyze_anatomy.py reports/landmarks_3d.json \
  --high-fidelity --json reports/anatomy_qa.json

# Only with independent 3D coordinates for the SAME person:
python scripts/analyze_anatomy.py reports/landmarks_3d.json \
  --reference-3d inputs/subject_reference_3d.json --high-fidelity --max-drift 0.08 \
  --json reports/anatomy_qa.json
```

**Output states**: `BLOCKED` = incomplete or structurally contradictory; `REVIEW_REQUIRED` = no independent 3D reference or warnings; `PASS_METRICS_ONLY` = numbers pass but visual review still mandatory. None means proven realism. A report must be updated after modifying mesh/landmark positions; never reuse stale reports.
