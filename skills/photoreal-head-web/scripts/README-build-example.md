# Rebuild the licensed head demonstration

`build_example.py` is specific to the **Infinite, 3D Head Scan by Lee Perry-Smith**
demonstration. It reuses a licensed scan; it does not sculpt a new head or certify
anatomy/likeness. Existing skill release gates remain unchanged.

Requires Blender **>=4.2** and its bundled `bpy`, `bmesh`, `mathutils`; no pip
dependencies. Verified runtime: Blender 5.2.2 LTS. Run in an isolated background
process because building resets the scene. Do not run this inside a live session.

Provide the original licensed input directory with all four files:

- `LeePerrySmith.glb`
- `Map-COL.jpg`
- `Infinite-Level_02_Tangent_SmoothUV.jpg`
- `LeePerrySmith_License.txt`

Input assets are not downloaded or bundled by this script. Obtain them from the
licensed source described in the tracked example's `README.md` and
`reports/provenance.json` under `assets/examples/photoreal-head/`. Retain CC BY 3.0
attribution. The script copies the provided attribution; it cannot independently
verify its truth or authorize arbitrary third-party data.

From the repository root, with Blender on PATH (or substitute its full executable):

```text
blender --background --factory-startup --python-exit-code 1 --python skills/photoreal-head-web/scripts/build_example.py -- --source-dir work/photoreal-head-source --out-dir work/head-example-new
```

Use **new/empty, non-overlapping output**. Input and output paths resolve from the
caller's cwd; there is no workstation/root constant. Spaces are supported when
quoted. All inputs are checked before the scene reset. Nothing is written beside
inputs or into the shipped example by default. A failed build may leave partial
output; retain it for diagnosis and use a new directory on retry.

Outputs: `model/head.glb`, seven PNGs in `renders/`, `reports/build.json`,
`head-example.blend` and copied `LICENSE-head.txt`. Unlike the old local helper,
the report lists actual PNG paths instead of claiming WebP conversions. GLB is
exported with scan skin materials before clay renders; the saved project restores
the skin material. No viewer, WebP conversion or public deployment is performed.

`--resolution 800 --samples 24` are defaults (height is width * 9/8).
For a fast runtime smoke test use `--resolution 64 --samples 1`; this does not
establish production render quality. `--skip-renders` exports only model/project
and reports `NOT_RUN` for render review. Use `--help` after Blender's `--` for CLI
help, or `python scripts/build_example.py --help` from this skill directory.

Validate the generated GLB with the existing structural checker:

```text
python -B skills/photoreal-head-web/scripts/inspect_glb.py work/head-example-new/model/head.glb --require-normal-map
python -B -m unittest discover -s skills/photoreal-head-web/tests -p "test_build_example_cli.py" -v
```

CLI tests cover missing inputs, output preservation, import safety and portability
without Blender. Real generation/render verification requires the licensed inputs
and background Blender. Tests remove only their own temporary fixtures. Structural
checks do not replace clay/UV/browser inspection or human anatomy acceptance.
