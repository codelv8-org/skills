# Research evidence and implementation provenance

## What was integrated

R3.1 integrates the completed **Thai Krathong 3D Builder — Deep Research Upgrade(1)** report, dated 2026-11-23, and direct visual inspection of the user's 14 supplied screenshots. [Read the research report](https://chatgpt.com/library?file_id=libfile_ffc2d867098c819189e7101fda501d9b&account_id=23279cbc-f151-4d12-a479-623f5ef46ac3).

The report described a 50-file Reference Match V3 archive, but the active skill still contained 15 original files. The report's archive was not recoverable from its saved metadata in this runtime. **R3.1 is a new implementation of the findings, not a recovered or verified copy of that archive.** Do not repeat the report's historical file/test counts as results of this implementation.

The new builder uses Blender directly and preserves the legacy generator. Actual implementation checks are recorded in `implementation-verification.json` beside this document. Tests establish technical execution, not exact likeness.

## Research-to-implementation map

| Finding | Practical consequence | Location |
|---|---|---|
| References have different structural families | Choose family before constructing perimeter/base | `SKILL.md`; `build_reference.py`; eight `ref-*.json` presets |
| Lotus depends on broad curvature and different whorl pitch | Closed spoon surfaces, independent whorls | Lotus/petal builder |
| Banana-leaf folds expose planar sections and overlaps | Creased sheets and layered flaps | Leaf builder |
| Diamond/terraces change whole-body topology | Change footprint and platform layout | Diamond and tiered builders |
| Bread and clay are volumetric families | Thick slices or a hollow vessel | Bread/clay builders |
| Surface and presentation matter | Original image textures; actual Blender rendering | `reference_finish.py` |
| Mesh validity is not likeness | GLB round trip plus separate image review | `check_reference_model.py`; mandatory visual gate |

## Source register and scope

1. **Fourteen user screenshots:** primary evidence for these particular digital designs. Consult `screenshot-study.md` and `assets/reference-catalog.json`. Screenshots establish visible shape and colour; rear topology, dimensions and original shader internals remain inferred.
2. **Completed research report**, linked above: evidence for research conclusions and that report's own claims. It is not proof that the files it described were installed.
3. **Ruangnarong, 2018, Silpakorn/Veridian:** [Thai traditional folding kra-tong, case study Hak-Kor-Ma](https://he02.tci-thaijo.org/index.php/Veridian-E-Journal/article/view/125560). The abstract identifies Hak-Kor-Ma as a basic banana-leaf folding form. This supports modelling distinct folded panels; it does not certify these presets as exact Hak-Kor-Ma constructions. Article page rechecked 2026-11-23.
4. **DLTV:** [natural-material krathong construction](https://dltv.ac.th/utils/files/download/110774), [materials list](https://dltv.ac.th/utils/files/download/204799), [four-corner leaf-container preparation](https://dltv.ac.th/utils/files/download/125978). Supports stem base, leaf preparation/cover/folds and decoration sequence. Food containers are related leaf craft, not automatically the same festival design.
5. **Lotus morphology study (2025):** [Comparative transcriptomics of two petal variants](https://pmc.ncbi.nlm.nih.gov/articles/PMC12279870/) / [PubMed](https://pubmed.ncbi.nlm.nih.gov/40697868/). Compares broad/narrow petals, supporting independent width and length controls. Screenshots, not a universal botanical count, determine the digital assembly. Rechecked via indexed primary paper and PubMed 2026-11-23.
6. **Blender official documentation:** [glTF 2.0 exporter](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html). Explains recognised Principled/image connections and roughness/metallic values. Check the installed Blender version; the online manual may describe a newer release.
7. **Khronos:** [glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html). Portable output uses supported image/material properties, not arbitrary Blender node graphs.
8. **Reference websites:** [Posy For You](https://www.posyforyou.com/krathong), [SeasonSnap](https://www.seasonsnap.store/). The report describes public category/thumbnail observations, not a full mesh inventory. SeasonSnap's landing page was readable on recheck; Posy returned an accessibility error through the text fetcher. No claim is made to have captured every page or downloaded their mesh assets.

## Design choices and remaining limits

Default scale, hidden-side counts, shell thickness, crease/cup parameters, roughness, bump amplitude and lighting are adjustable design decisions. Do not describe them as measurements from references.

Eight families cover broad strategies; the fourteen images include subtypes. A pale folded bowl with bead border, particular bread pedestals, a lotus central dome or specific leaf creases can require additional component edits. Record these gaps instead of silently changing the target reference.

The original procedural textures are interpretations; website UVs and material maps were not recovered. Embedded base colour is portable. Extra Blender bump/subsurface and stage effects need separate export review or actual baking. A successful build/round trip does not establish beauty or exact matching.
