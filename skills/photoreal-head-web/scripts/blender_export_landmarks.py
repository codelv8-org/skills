#!/usr/bin/env python3
"""Export 3D landmarks from Blender empty objects named LM_<code>.

Place the empties under HEAD_LANDMARKS. If a HEAD_ROOT exists, use its
local coordinate system to convert world-space empty positions. Align HEAD_ROOT
so that +X = subject-left, -Y = front, +Z = up. 1 Blender unit = 1 meter.

blender -b head.blend --python scripts/blender_export_landmarks.py -- \
  --collection HEAD_LANDMARKS --root HEAD_ROOT --output reports/landmarks_3d.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--collection', default='HEAD_LANDMARKS')
    p.add_argument('--root', default='HEAD_ROOT')
    p.add_argument('--output', type=Path, required=True)
    return p.parse_args(argv)


def main():
    import bpy
    args = parse_args()
    collection = bpy.data.collections.get(args.collection)
    if collection is None:
        raise RuntimeError(f'Landmark collection {args.collection!r} does not exist')
    root = bpy.data.objects.get(args.root)
    root_inv = root.matrix_world.inverted() if root else None
    points = {}
    if abs(float(bpy.context.scene.unit_settings.scale_length) - 1.0) > 1e-6:
        raise RuntimeError('Set Blender unit scale to 1.0 (1 BU = 1 meter) before exporting landmarks')
    for obj in collection.all_objects:
        if obj.type != 'EMPTY' or not obj.name.startswith('LM_'):
            continue
        name = obj.name[3:]
        if '.' in name:
            raise RuntimeError('Landmark name must be unique and not auto-suffixed: ' + obj.name)
        if name in points:
            raise RuntimeError('Duplicate landmark ' + name)
        pos = obj.matrix_world.translation.copy()
        if root_inv is not None:
            pos = root_inv @ pos
        points[name] = [round(float(v), 7) for v in pos]
    if not points:
        raise RuntimeError('No EMPTY objects named LM_<code> found')
    record = {
        'schema': 'photoreal-head-landmarks-3d/v1',
        'coordinate_system': 'blender_local_z_up_front_minus_y',
        'units': 'meters',
        'source_blend': bpy.data.filepath,
        'root': args.root if root else None,
        'landmarks': dict(sorted(points.items())),
    }
    path = args.output.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(points)} 3D landmarks to {path}')


if __name__ == '__main__':
    main()
