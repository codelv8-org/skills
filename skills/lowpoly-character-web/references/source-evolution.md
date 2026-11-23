# Derivation from user's photoreal-head-web v2.0

The user-provided source ZIP (`photoreal-head-web/SKILL.md` plus supporting references, tools and web starter) was actually opened and reviewed during this skill's creation. Key inherited ideas:

1. Anatomy and silhouette must pass a gray-clay/multiview check before materials.
2. Measured geometry and landmark conventions are useful but cannot prove subjective artistic quality; do not invent occluded reference evidence.
3. UV/texture and glTF checks are distinct from web rendering checks.
4. GLB is an actual editable pipeline deliverable, not a 2D image or promise; report missing operations.
5. Track privacy/authorization/license of real-person references.

Changed specifically for low-poly characters:

- Replaces head-only craniofacial scope with full-body, creature, robot, mascot, avatar and NPC modes.
- Replaces strict photoreal anatomy and measured facial landmarks with art-directed proportional landmarks and motion-aware topology. Proportions are stylistic variables rather than universal ideals.
- Replaces mandatory high-res PBR skin and UV0 requirement with optional UV, palette/vertex-color mode and polygon/draw-call budgets.
- Adds skinning, rigid segmented animation, deformation tests, clips, and original-IP checks.
- Reuses the concept and GLB parsing pattern of the source `inspect_glb.py`, adapted so absence of image textures/normal maps/UVs is valid for flat-color characters, and to check skins/animations only when requested.
- Includes a working procedural static blockout starter, six-view preview and web viewer example. Static blockout is intentionally **not** advertised as a finished weighted/rigged mesh.

No copy of the original photoreal skill is required to install this new skill. This is a standalone package.
