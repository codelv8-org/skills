#!/usr/bin/env python3
"""Validate and export a Blender HEAD_WEB collection as glTF 2.0 binary.

Run with Blender, e.g. blender -b scene.blend --python blender_export_head.py --
    --collection HEAD_WEB --output export/head.glb --report reports/qa.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def cli_args():
    extra = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', default='HEAD_WEB')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, help='Optional JSON report')
    parser.add_argument('--max-triangles', type=int, default=90000)
    parser.add_argument('--release', action='store_true', help='Enforce anatomy evidence before candidate GLB export; final promotion requires surface QA')
    parser.add_argument('--anatomy-report', type=Path, help='JSON from analyze_anatomy.py')
    parser.add_argument('--photo-fit-report', type=Path, action='append', default=[], help='JSON from compare_photo_landmarks.py, repeat for views')
    parser.add_argument('--manual-anatomy-reviewed', action='store_true', help='Operator attests to actual clay-view anatomy review, not an automated claim')
    parser.add_argument('--likeness-requested', action='store_true', help='A specific authorized likeness needs photo-fit evidence')
    return parser.parse_args(extra)


def run():
    import bpy

    args = cli_args()
    coll = bpy.data.collections.get(args.collection)
    if coll is None:
        raise RuntimeError(f'Missing export collection {args.collection!r}')
    objs = [o for o in coll.all_objects if o.type == 'MESH' and not o.hide_render]
    if not objs:
        raise RuntimeError('No visible mesh objects in export collection')

    errors, warnings = [], []
    tris = 0
    sources = []
    dg = bpy.context.evaluated_depsgraph_get()
    for obj in objs:
        if not obj.data.uv_layers:
            errors.append(f'{obj.name}: missing UV layer')
        else:
            uv_data = obj.data.uv_layers.active.data
            coords = [v for loop in uv_data for v in tuple(loop.uv)]
            if coords and (min(coords) < -0.0001 or max(coords) > 1.0001):
                errors.append(f'{obj.name}: UV0 out of [0,1] range')
        if not obj.material_slots or all(slot.material is None for slot in obj.material_slots):
            errors.append(f'{obj.name}: no assigned material')
        if any(abs(float(v)) < 0.00001 for v in obj.scale):
            errors.append(f'{obj.name}: zero object scale')
        if any(float(v) < 0 for v in obj.scale):
            warnings.append(f'{obj.name}: negative scale, inspect normals')
        obj_eval = obj.evaluated_get(dg)
        mesh_eval = obj_eval.to_mesh()
        try:
            mesh_eval.calc_loop_triangles()
            tri_count = len(mesh_eval.loop_triangles)
        finally:
            obj_eval.to_mesh_clear()
        tris += tri_count
        sources.append({'name': obj.name, 'triangles': tri_count})

    materials = {slot.material for obj in objs for slot in obj.material_slots if slot.material}
    texture_count = 0
    material_maps = {}
    for material in materials:
        names = []
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.type != 'TEX_IMAGE':
                    continue
                if node.image is None:
                    warnings.append(f'{material.name}: image texture node without image')
                    continue
                image = node.image
                names.append(image.name)
                texture_count += 1
                if image.source == 'FILE' and not image.packed_file:
                    image_path = Path(bpy.path.abspath(image.filepath))
                    if not image_path.is_file():
                        errors.append(f'{material.name}: missing texture file {image_path}')
                if image.source not in ('FILE', 'GENERATED', 'TILED'):
                    warnings.append(f'{material.name}: image source {image.source} might need baking')
        if not names:
            warnings.append(f'{material.name}: no image texture nodes; verify GLB material appearance')
        material_maps[material.name] = names

    # Release gates deliberately remain separate from generic structural export.
    # These reports are evidence, not mathematical proof of a believable human face.
    anatomy_evidence = {}
    photo_fit_evidence = []
    if args.release:
        if not args.output.name.endswith('.candidate.glb'):
            errors.append('Release export must use *.candidate.glb; final promotion requires validate_head_surface.py')
        if not args.manual_anatomy_reviewed:
            errors.append('Release requires an actual clay-view anatomy review (--manual-anatomy-reviewed)')
        if not args.anatomy_report:
            errors.append('Release requires --anatomy-report from landmark inspection')
        elif not args.anatomy_report.is_file():
            errors.append('Anatomy QA report does not exist: ' + str(args.anatomy_report))
        else:
            try:
                anatomy_evidence = json.loads(args.anatomy_report.read_text(encoding='utf-8'))
                if anatomy_evidence.get('status') == 'BLOCKED':
                    errors.append('Anatomy QA report is BLOCKED')
                elif anatomy_evidence.get('status') not in ('PASS_METRICS_ONLY', 'REVIEW_REQUIRED'):
                    errors.append('Anatomy QA report status is invalid/unrecognized')
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append('Anatomy QA report unreadable: ' + str(exc))
        if args.likeness_requested and not args.photo_fit_report:
            errors.append('Requested specific likeness requires at least one comparable photo-fit report')
        for path in args.photo_fit_report:
            try:
                doc = json.loads(path.read_text(encoding='utf-8'))
                photo_fit_evidence.append({'file': str(path), 'status': doc.get('status'), 'view': doc.get('view')})
                if doc.get('status') != 'PASS_PHOTO_FIT_ONLY':
                    errors.append('Photo-fit report did not pass: ' + str(path))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append('Photo-fit report unreadable: ' + str(exc))
    if tris > args.max_triangles:
        errors.append(f'Triangle target exceeded: {tris} > {args.max_triangles}')
    if not bpy.data.filepath:
        warnings.append('Current scene has never been saved; source .blend may not be deliverable')

    output = args.output.expanduser().resolve()
    report_path = (args.report or output.with_name(output.stem + '_qa.json')).expanduser().resolve()
    report = {
        'collection': args.collection, 'objects': sources, 'triangles': tris,
        'materials': material_maps, 'texture_nodes': texture_count,
        'errors': errors, 'warnings': warnings, 'export_path': str(output),
        'status': 'FAIL' if errors else 'PASS_STRUCTURAL_PRE_EXPORT',
        'note': 'Landmark checks do NOT prove realism; UV overlap/stretch, anatomical appearance, and browser runtime still require human QA',
        'release_mode': args.release, 'manual_anatomy_review_declared': args.manual_anatomy_reviewed,
        'anatomy_evidence_status': anatomy_evidence.get('status'), 'photo_fit_evidence': photo_fit_evidence,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if errors:
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        raise RuntimeError('Pre-export validation failed: ' + '; '.join(errors))

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    output.parent.mkdir(parents=True, exist_ok=True)
    if not hasattr(bpy.ops.export_scene, 'gltf'):
        raise RuntimeError('Blender glTF exporter unavailable in current installation')
    result = bpy.ops.export_scene.gltf(filepath=str(output), export_format='GLB', use_selection=True)
    if 'FINISHED' not in result or not output.is_file():
        raise RuntimeError('Blender glTF exporter did not create GLB')
    report['status'] = 'CANDIDATE_NEEDS_SURFACE_QA' if args.release else 'EXPORTED_NEEDS_GLB_AND_BROWSER_QA'
    report['glb_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    report['glb_size_mb'] = round(output.stat().st_size / (1024 * 1024), 3)
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    run()
