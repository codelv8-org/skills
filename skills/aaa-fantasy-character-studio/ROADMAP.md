# Roadmap

## Current — v2.0.0 Beta
- Cloud-only default, explicit MeshIR, deterministic GLB compiler, bind-clay renderer, authored skin and clips, 26 tested cases. Evidence gates retained.

## Next release
- Test the same original full-character brief in verified Chat and Agent cloud sessions with identical cameras and metrics; archive baseline, versions and actual outputs.
- Add anatomy-aware surface patches, seam constraints and local-edit regression tests. Refresh overview concept and include actual matched renders separately.
- Add independent glTF validation and animated skinning/geometry diagnostics; compare engine import against compiler output.

## Planned
- Bounded adaptive implicit surfaces and topology refinement; UV island/overlap and texel-density diagnostics; validated high/low tangent and AO baker; garment/hair collision checks; procedural materials and physically based preview.
- Rig weight/deformation evaluation, performance and LOD measurements under explicit cloud budgets.

## Challenges / long-term vision
Specialized learned 3D systems have trained priors unavailable to an LLM code-only workflow. Seek reproducible agent-authored editable surfaces and measured fidelity without mandatory SaaS or local generation; maintain explicit fallback and avoid claiming parity without benchmarks. Stable requires actual character benchmarks in both modes, matched version evidence and independent production gate approval.
