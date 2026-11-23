#!/usr/bin/env python3
"""Run *within Blender* after seams are marked on a named mesh.

Example: blender -b source.blend --python blender_unwrap_head.py --
    --object Head_LOD0 --output-blend output_uv.blend
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def parse_args():
    cli = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--object', default='Head_LOD0', help='Exact mesh object name')
    parser.add_argument('--uv-name', default='UVMap')
    parser.add_argument('--margin', type=float, default=0.015)
    parser.add_argument('--output-blend', type=Path, required=True)
    return parser.parse_args(cli)


def main():
    import bpy

    args = parse_args()
    if not 0.001 <= args.margin <= 0.1:
        raise ValueError('margin must be between 0.001 and 0.1 UV units')
    obj = bpy.data.objects.get(args.object)
    if obj is None or obj.type != 'MESH':
        raise RuntimeError(f'Expected MESH object named {args.object!r}')
    if obj.data.library is not None:
        raise RuntimeError('Target mesh is externally linked; make it local before editing')
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    seam_count = sum(1 for edge in obj.data.edges if edge.use_seam)
    if not seam_count:
        raise RuntimeError(
            f'{obj.name} has no seam edges. Mark anatomical seams manually '
            '(behind scalp, behind ears, under jaw) before unwrapping.'
        )
    if not obj.data.uv_layers.get(args.uv_name):
        obj.data.uv_layers.new(name=args.uv_name)
    obj.data.uv_layers.active = obj.data.uv_layers[args.uv_name]
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=args.margin)
    bpy.ops.object.mode_set(mode='OBJECT')

    uv_layer = obj.data.uv_layers[args.uv_name]
    values = [coord for loop in uv_layer.data for coord in tuple(loop.uv)]
    if not values:
        raise RuntimeError('Unwrap produced no UV coordinates')
    low, high = min(values), max(values)
    if low < -0.0001 or high > 1.0001:
        raise RuntimeError(f'UV coordinates outside [0,1]: low={low:.5f}, high={high:.5f}')

    dest = args.output_blend.expanduser().resolve()
    if bpy.data.filepath and Path(bpy.data.filepath).resolve() == dest:
        raise RuntimeError('Refusing to overwrite source .blend; use a different --output-blend path')
    dest.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    print(json.dumps({
        'result': 'UV0 created, visual stretch/overlap review still required',
        'object': obj.name, 'seam_edges': seam_count,
        'uv_range': [round(low, 6), round(high, 6)],
        'output': str(dest),
    }, indent=2))


if __name__ == '__main__':
    main()
