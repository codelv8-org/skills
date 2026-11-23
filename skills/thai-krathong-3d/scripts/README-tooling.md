# Portable authoring checks

These optional tools are separate from the skill's Python-only generation tools.
They resolve their dependencies relative to their installed location. Input/output
CLI paths are resolved from the caller's current directory. Quoted paths with spaces
are supported. Existing input files and nonempty output directories are preserved.
Failures can leave a **new, partial output** for diagnosis; choose a new output path
for retries. No overwrite or cleanup operation is provided.

## Preset audit

Requires Blender **>=4.2**, including its bundled Python, `bpy`, `bmesh` and
`mathutils`; do not `pip install bpy`. Verified with Blender 5.2.2 LTS. Keep this
script with its sibling skill scripts (`build_reference.py`, `reference_finish.py`,
`mesh_uv_qa.py`) and the skill's `assets/` directory.

From the repository root, with `blender` on PATH (or substitute its full path):

```text
blender --background --factory-startup --python-exit-code 1 --python skills/thai-krathong-3d/scripts/audit_presets.py -- --out-dir work/preset-audit-new --save-blends
```

The default `--presets-dir` is the installed skill's `assets/`, independent of cwd.
Use `--presets-dir PATH --pattern "ref-*.json"` for other presets. The pattern must
be a filename glob, not a directory traversal. Every selected preset is built and
audited; `--save-blends` saves all generated editable scenes instead of a fixed
family list. The directory must be new/empty and must not overlap the preset source.
Run only in a separate background process: the script resets the scene per preset.
Reports and `summary.json` remain available on QA failure. Any failed preset causes
exit 1; preflight misuse causes exit 2. Geometry/UV checks do not certify visual
likeness, anatomy, buoyancy or target-device performance.

## Independent GLB validator

Requires Node.js **>=18** and npm. Install the exact locked optional dependency:

```text
npm ci --ignore-scripts --prefix skills/thai-krathong-3d
node skills/thai-krathong-3d/scripts/validate-glb.cjs --out-dir work/glb-validation-new skills/thai-krathong-3d/examples/web-pbr-showcase/results/banana/krathong.glb skills/thai-krathong-3d/examples/web-pbr-showcase/results/clay/krathong.glb
```

`gltf-validator` is pinned to **2.0.0-dev.3.10** with integrity in `package-lock.json`.
Install from the skill package even when invoking the script from a different cwd.
No global package or local fixture `node_modules` path is used. Inputs must be
self-contained GLBs; external resource dependencies fail validation.

Errors **and warnings fail by default**. `--allow-warnings` is explicit opt-in and
retains all warnings in reports; it never permits errors. Indexed report filenames
avoid collisions when GLBs have the same basename. Reports go only into a new/empty
directory; there is no automatic overwrite of reports beside source assets.
`summary.json` includes the validator version and per-file result.

Exit 0: all files pass. Exit 1: any invalid asset (including malformed container).
Exit 2: usage, filesystem or dependency failure. Use `--help` for usage and `--`
before filenames beginning with a dash.

## Regression checks

```text
python -B -m unittest discover -s skills/thai-krathong-3d/tests -p "test_audit_presets_cli.py" -v
npm test --prefix skills/thai-krathong-3d
```

The CLI suite checks preflight and preservation without Blender. The Node suite
runs the actual locked validator against generated valid/invalid GLB fixtures,
including strict warnings and external resources. Run a real preset audit separately
with Blender to check generation and geometry. Only test-owned temporary fixtures
are cleaned by the automated suites; user authoring data is never removed.
