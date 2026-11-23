# Human-head sculpture: anatomy evidence checklist

> Fill after reviewing ACTUAL model and rendered clay screenshots, not inferred expectations.

- Project / Blender file:
- Head origin, unit and camera conventions:
- Reference type: generic / authorized photographs / authorized scan / original mesh
- Reference views, camera / lens limits and missing information:
- Base mesh source, license and attribution:
- Review date and reviewer (or describe independent inspection method):

## G1 - Cranial masses, grey-clay (do not texture until PASS)

| View | Evidence screenshot | Result PASS/REVIEW/BLOCK | Concrete fault / corrective change |
|---|---|---|---|
| Front | | | |
| Left profile | | | |
| Right profile | | | |
| Left 3/4 | | | |
| Right 3/4 | | | |
| Top/back silhouette | | | |

**Check explicitly:** cranial/posterior vault, forehead curvature, zygomatic/maxillary volume, mandibular ramus/angle/chin, orbital socket depth, ear attachment.

## G2 - Facial features, grey-clay

| Region | Evidence | Result | Observation and change |
|---|---|---|---|
| Left/right orbit, eyeball seat and lid thickness | | | |
| Nasion and sellion / nasal bridge curvature | | | |
| Nasal tip, ala, columella and subnasal openings | | | |
| Left/right ear helix/antihelix/concha/tragus/lobule | | | |
| Philtrum/lip vermilion/mouth corners/mentalis | | | |
| Brow bone and proposed eyebrow decal footprint | | | |

## G3 - Numeric evidence (not photorealism proof)

- 3D landmark JSON:
- Required landmarks placed (count), high-fidelity extra markers placed:
- `analyze_anatomy.py` report / status:
- If applicable, source 3D reference provenance and normalized ratio drift:
- Photo-fit front report / RMS / threshold / worst landmark:
- Photo-fit profile report / RMS / threshold / worst landmark:
- Camera/perspective caveats and remaining inferred geometry:

## G4 - Materials and UV

- Retopology quality and eyelid/lip loops:
- Face UV0 checker and eyebrow texel-density screenshot:
- Normal bake and PBR color-space verification:
- Eyebrow variant A and B independently switched without z-fighting:

## G5 - Real browser acceptance

- GLB path and `inspect_glb.py` result:
- Browser/device and renderer:
- Eye / nose / ear appearance at front, 3/4 and profile:
- Runtime triangle count, file size, FPS / loading where tested:
- Unfinished tests or known aesthetic defects:

## Release decision

- Status: **PASS / REVIEW / BLOCKED**
- Corrective actions completed and re-rendered:
- What is actually delivered (exact paths):
- What was NOT executed (missing 3D authoring / no browser / missing photos):
