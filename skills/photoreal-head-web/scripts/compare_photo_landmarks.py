#!/usr/bin/env python3
"""Compare 2D landmark annotations on a reference photo and a rendered head.

A similarity fit removes only translation, rotation, and uniform scale.
It does NOT correct perspective, expression, focal length, lens distortion,
head pose, or occlusion. Those must be matched before interpreting results.
Coordinates use image pixels: +X right, +Y down (not Blender 3D axes).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

FRONTAL_ANCHORS = ('en_l', 'en_r', 'ex_l', 'ex_r')
PROFILE_ANCHORS = ('n', 'prn', 'sn', 'gn')
REGIONS = {
    'eye': ('en_', 'ex_', 'pupil_', 'supraorbital_'),
    'nose': ('n', 'prn', 'sn', 'al_', 'ac_', 'sbal_', 'rh'),
    'mouth_chin': ('ls', 'li', 'sto', 'ch_', 'gn', 'pg'),
    'ear': ('t_', 'sa_', 'sba_', 'obi_', 'obs_'),
}


def load_points(path):
    obj = json.loads(Path(path).read_text(encoding='utf-8'))
    if obj.get('coordinate_space') != 'image_pixels_xy_down':
        raise ValueError(f'{path}: coordinate_space must be image_pixels_xy_down')
    view = obj.get('view')
    if view not in ('front', 'left_profile', 'right_profile', 'left_threequarter', 'right_threequarter'):
        raise ValueError(f'{path}: set a supported view')
    size = obj.get('image_size')
    if (not isinstance(size, list) or len(size) != 2 or
            any(not isinstance(v, int) or v <= 0 for v in size)):
        raise ValueError(f'{path}: image_size should be [width,height] in pixels')
    raw = obj.get('points', {})
    if not isinstance(raw, dict):
        raise ValueError(f'{path}: points must be an object')
    points = {}
    for name, xy in raw.items():
        if (not isinstance(xy, list) or len(xy) != 2 or
                any(not isinstance(x, (float, int)) or not math.isfinite(x) for x in xy)):
            raise ValueError(f'{path}: invalid point {name}')
        if not (0 <= xy[0] <= size[0] and 0 <= xy[1] <= size[1]):
            raise ValueError(f'{path}: point {name} lies outside the image bounds')
        points[name] = (float(xy[0]), float(xy[1]))
    return view, size, points


def similarity_transform(src, dest, anchors):
    n = len(anchors)
    sx = sum(src[k][0] for k in anchors) / n
    sy = sum(src[k][1] for k in anchors) / n
    dx = sum(dest[k][0] for k in anchors) / n
    dy = sum(dest[k][1] for k in anchors) / n
    xx, xy, ss = 0., 0., 0.
    for k in anchors:
        x, y = src[k][0] - sx, src[k][1] - sy
        u, v = dest[k][0] - dx, dest[k][1] - dy
        xx += x * u + y * v
        xy += x * v - y * u
        ss += x * x + y * y
    if ss <= 1e-9:
        raise ValueError('Degenerate landmark set: all render anchor points coincide')
    a, b = xx / ss, xy / ss
    if a * a + b * b <= 1e-9:
        raise ValueError('Degenerate alignment: source and target anchors cannot be registered')
    def f(xy):
        x, y = xy[0] - sx, xy[1] - sy
        return a * x - b * y + dx, b * x + a * y + dy
    return f, (a, b)


def compare(reference_path, render_path, threshold=0.04):
    ref_view, ref_size, ref = load_points(reference_path)
    rend_view, rend_size, rend = load_points(render_path)
    if ref_view != rend_view:
        raise ValueError(f'View mismatch: reference={ref_view} model={rend_view}')
    common = sorted(ref.keys() & rend.keys())
    if len(common) < 5:
        raise ValueError('At least 5 matching points are required')
    preferred = FRONTAL_ANCHORS if ref_view == 'front' else PROFILE_ANCHORS
    anchors = [k for k in preferred if k in ref and k in rend]
    if len(anchors) < 3:
        raise ValueError('Need at least 3 view-specific anchor landmarks: ' + ', '.join(preferred))
    align, (a, b) = similarity_transform(rend, ref, anchors)
    if all(k in ref for k in ('ex_l', 'ex_r')):
        p, q = ref['ex_l'], ref['ex_r']
        unit = math.dist(p, q)
        basis = 'outercanthal_width_px'
    elif all(k in ref for k in ('n', 'gn')):
        unit = math.dist(ref['n'], ref['gn'])
        basis = 'nasion_to_gnathion_px'
    else:
        unit = max(max(x for x, y in ref.values()) - min(x for x, y in ref.values()),
                   max(y for x, y in ref.values()) - min(y for x, y in ref.values()))
        basis = 'reference_landmark_bbox_extent_px'
    if unit < 1:
        raise ValueError('Reference landmarks are degenerate: normalization length too short')
    errors = {}
    aligned = {}
    for k in common:
        xy = align(rend[k]); aligned[k] = [round(xy[0], 2), round(xy[1], 2)]
        errors[k] = math.dist(xy, ref[k]) / unit
    rms = math.sqrt(sum(e * e for e in errors.values()) / len(errors))
    max_key = max(errors, key=errors.get)
    per_region = {}
    for region, prefixes in REGIONS.items():
        included = [e for k, e in errors.items() if any(k == p or k.startswith(p) for p in prefixes)]
        if included:
            per_region[region] = round(math.sqrt(sum(e * e for e in included) / len(included)), 5)
    notes = [
        'Threshold is a project fit gate, not a scientific facial-realism score.',
        'Only interpret after matching view, expression, camera projection and landmarks.',
        'A 2D landmark match cannot establish hidden head geometry or photorealism.',
        'Source image stays local unless user explicitly authorizes upload or sharing.',
    ]
    if ref_view != 'front':
        notes.append('Profile and oblique landmark alignment is more sensitive to camera and occlusion.')
    return {
        'status': 'PASS_PHOTO_FIT_ONLY' if rms <= threshold else 'REVIEW_REQUIRED',
        'view': ref_view, 'matched_points': len(common), 'anchor_points': anchors,
        'reference_size': ref_size, 'render_size': rend_size,
        'rms_normalized': round(rms, 5), 'threshold_normalized': threshold,
        'normalization_basis': basis, 'largest_error_landmark': max_key,
        'largest_error_normalized': round(errors[max_key], 5),
        'per_region_rms': per_region,
        'individual_error_normalized': {k: round(v, 5) for k, v in errors.items()},
        'registered_render_points': aligned,
        'reference_points': {k: list(ref[k]) for k in common},
        'notes': notes,
    }


def save_overlay(path, result, photo_path=None):
    from PIL import Image, ImageDraw
    w, h = result['reference_size']
    if photo_path:
        canvas = Image.open(photo_path).convert('RGB')
        if canvas.size != (w, h):
            raise ValueError('Background photo size differs from reference image_size')
    else:
        canvas = Image.new('RGB', (w, h), (35, 37, 41))
    draw = ImageDraw.Draw(canvas)
    for name, ref in result['reference_points'].items():
        render = result['registered_render_points'][name]
        draw.line([tuple(ref), tuple(render)], fill=(255, 187, 60), width=2)
        x, y = ref
        rx, ry = render
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(78, 207, 140))
        draw.ellipse((rx - 3, ry - 3, rx + 3, ry + 3), fill=(255, 99, 109))
        draw.text((x + 5, y - 12), name, fill=(245, 245, 245))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference_2d', type=Path)
    p.add_argument('render_2d', type=Path)
    p.add_argument('--threshold', type=float, default=0.04)
    p.add_argument('--json', type=Path)
    p.add_argument('--overlay', type=Path, help='Optional local PNG of aligned landmarks')
    p.add_argument('--photo', type=Path, help='Optional consented background photo for overlay')
    args = p.parse_args()
    if not 0 < args.threshold < 1:
        p.error('--threshold must lie between 0 and 1')
    try:
        result = compare(args.reference_2d, args.render_2d, args.threshold)
        if args.overlay:
            save_overlay(args.overlay, result, args.photo)
            result['overlay_path'] = str(args.overlay)
    except (OSError, ValueError, json.JSONDecodeError, ImportError) as exc:
        result = {'status': 'BLOCKED', 'errors': [str(exc)]}
    text = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    print(text, end='')
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding='utf-8')
    return 2 if result['status'] == 'BLOCKED' else 1 if result['status'] == 'REVIEW_REQUIRED' else 0


if __name__ == '__main__':
    sys.exit(main())
