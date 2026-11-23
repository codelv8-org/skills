"""Build and audit reference presets in isolated background Blender.

Requires Blender >=4.2; uses sibling skill scripts, never the working directory.
Output must be new/empty and outside the input directory. No inputs are saved.
"""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--presets-dir', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'assets')
    parser.add_argument('--pattern', default='ref-*.json', help='Filename glob, no directories')
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--save-blends', action='store_true', help='Save all audited editable assets')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    source, out = args.presets_dir.expanduser().resolve(), args.out_dir.expanduser().resolve()
    if not source.is_dir():
        parser.error('--presets-dir must be an existing directory')
    if not args.pattern or '/' in args.pattern or '\\' in args.pattern or '..' in args.pattern:
        parser.error('--pattern must be a filename glob without directories')
    paths = sorted(source.glob(args.pattern))
    if not paths or any(not p.is_file() or p.suffix.lower() != '.json' for p in paths):
        parser.error('Pattern must match one or more JSON files')
    if source.is_relative_to(out) or out.is_relative_to(source):
        parser.error('Input and output directories must not overlap')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error('--out-dir must be a new or empty directory')
    try:
        presets = [(p, json.loads(p.read_text(encoding='utf-8-sig'))) for p in paths]
        import bpy
    except (OSError, ValueError, ImportError) as exc:
        parser.error(f'Cannot load presets or Blender runtime: {exc}')
    if not bpy.app.background or bpy.app.version < (4, 2, 0):
        parser.error('Use isolated background Blender >=4.2')
    # Resolve dependencies relative to this installed script, independently of cwd.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_reference import Builder, FAMILIES
    from reference_finish import apply_materials
    from mesh_uv_qa import inspect
    if any(not isinstance(cfg, dict) or cfg.get('family') not in FAMILIES for _, cfg in presets):
        parser.error('Every preset must be an object with a supported family')
    if any(not p.resolve().is_relative_to(source) for p in paths):
        parser.error('Preset symlinks must not escape the input directory')
    out.mkdir(parents=True, exist_ok=True)
    summary = {'passed': True, 'blender_version': bpy.app.version_string, 'presets': []}
    for path, cfg in presets:
        try:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            collection = Builder(cfg).build()
            apply_materials(collection)
            result = inspect(collection.all_objects)
            if args.save_blends:
                bpy.ops.wm.save_as_mainfile(filepath=str(out / (path.stem + '.blend')),
                                           check_existing=False)
        except Exception as exc:
            result = {'passed': False, 'errors': [str(exc)]}
        report_name = path.stem + '-source-qa.json'
        (out / report_name).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        summary['presets'].append({'preset': path.name, 'passed': result['passed'], 'report': report_name})
        summary['passed'] = summary['passed'] and result['passed']
        print('PRESET', path.name, 'PASS' if result['passed'] else 'FAIL', flush=True)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
