#!/usr/bin/env python3
"""Create an evidence-first multi-view character reference pack.

Does not infer camera calibration, absolute measurements, landmarks, depth,
identity or artistic fidelity. All inferred/unknown fields remain unverified.

Examples:
  python scripts/reference_intake.py sheet.png --out review/reference --layout four-columns
  python scripts/reference_intake.py --out review/reference --view front=front.png --view back=back.png
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps

VIEWS = ('front', 'back', 'left', 'right')
FEATURES = [
    ('head_hair_silhouette', True, 5),
    ('facial_proportions_and_landmarks', True, 5),
    ('whole_body_silhouette', True, 5),
    ('shoulder_hip_leg_ratios', True, 5),
    ('hands_ears_shoes', True, 4),
    ('uniform_color_panels', False, 3),
    ('strap_bag_badge_location', False, 4),
    ('faceted_design_language', True, 5),
]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_pack(out: Path, sheet: Path | None = None, views: dict[str, Path] | None = None,
                order: tuple[str, ...] = VIEWS, content_y: float = .90,
                boxes: dict[str, list[float]] | None = None) -> dict:
    if not 0 < content_y <= 1:
        raise ValueError('content_y must be >0 and <=1')
    if sheet is None and not views:
        raise ValueError('Supply a sheet or individual --view paths')
    if sheet is not None and views:
        raise ValueError('Use either --layout or --view input, not both')
    if sheet is not None and (set(order) != set(VIEWS) or len(order) != 4):
        raise ValueError('order must contain each of front, back, left, right exactly once')
    images: dict[str, Image.Image] = {}
    sources = {}
    if sheet is not None:
        if not sheet.is_file():
            raise FileNotFoundError(sheet)
        im = ImageOps.exif_transpose(Image.open(sheet)).convert('RGB')
        if im.width < 80 or im.height < 80:
            raise ValueError('Reference sheet too small for a four-view study')
        for i, view in enumerate(order):
            if boxes and view in boxes:
                b = boxes[view]
                if len(b) != 4 or not(0 <= b[0] < b[2] <= 1 and 0 <= b[1] < b[3] <= 1):
                    raise ValueError(f'Invalid normalized crop for {view}: {b}')
                x0,y0,x1,y1 = [int(q * (im.width if j%2==0 else im.height)) for j,q in enumerate(b)]
            else:
                x0 = round(im.width*i/4)
                x1 = round(im.width*(i+1)/4)
                y0,y1 = 0,round(im.height*content_y)
            images[view] = im.crop((x0,y0,x1,y1))
            sources[view] = {'original': str(sheet), 'crop_px': [x0,y0,x1,y1]}
        inputs = [sheet]
    else:
        if not set(views or {}).issubset(set(VIEWS)):
            raise ValueError('Unknown view name; use front/back/left/right')
        for view, src in (views or {}).items():
            if not src.is_file():
                raise FileNotFoundError(src)
            images[view] = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
            sources[view] = {'original': str(src)}
        inputs = list((views or {}).values())
    out.mkdir(parents=True, exist_ok=True)
    for view, im in images.items():
        im.save(out / f'{view}.png')
    spec = {
        'schema_version': '3.0',
        'origin_files': [{'name': p.name, 'sha256': sha256(p)} for p in inputs],
        'source_type': 'four_view_sheet' if sheet is not None else 'separate_view_images',
        'view_order': list(order) if sheet is not None else list(images),
        'view_camera_type': 'UNVERIFIED',
        'projection': 'UNVERIFIED: orthographic/perspective unknown; never assert exact scale from source',
        'character_height_m': None,
        'scale_assumption': 'Not supplied; choose only after scene brief (1 Blender unit = 1 m in authoring)',
        'facing_axis_gltf': '+Z (assumed; verify in exported GLB)',
        'source_views': {},
        'feature_requirements': [
            {'feature': name, 'critical': critical, 'weight': weight, 'observed_details': None,
             'confidence': 'UNREVIEWED', 'evidence': None}
            for name, critical, weight in FEATURES
        ],
        'open_questions': [
            'Verify camera projection and align head/feet/reference scale across views',
            'Mark head, shoulders, hips, knees, ankles and accessory landmarks per view',
            'Resolve any front/back/side contradictions before sculpting',
            'Confirm target WebGL character height and closest camera viewing distance'
        ],
        'gate': 'REVIEW_REQUIRED',
        'notice': 'Cropping is mechanical; no pose extraction, landmark detection, silhouette validation or 3D reconstruction is claimed.'
    }
    for v, im in images.items():
        spec['source_views'][v] = {
            **sources[v], 'view_path': f'{v}.png', 'size_px': [im.width, im.height],
            'coverage': 'UNREVIEWED',
            'key_landmarks_normalized': {
                'head_top': None, 'chin': None, 'left_shoulder': None, 'right_shoulder': None,
                'left_hip': None, 'right_hip': None, 'left_knee': None, 'right_knee': None,
                'left_ankle': None, 'right_ankle': None, 'left_foot_tip': None, 'right_foot_tip': None
            },
            'uncertainties': []
        }
    (out / 'reference_manifest.json').write_text(json.dumps(spec, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return spec


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sheet', nargs='?', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--layout', choices=['four-columns'])
    ap.add_argument('--order', default='front,back,left,right')
    ap.add_argument('--content-y', type=float, default=.90)
    ap.add_argument('--boxes-json', type=Path, help='JSON mapping view to normalized x0,y0,x1,y1 crops')
    ap.add_argument('--view', action='append', default=[], help='name=path; repeat for individual images')
    args=ap.parse_args()
    parsed={}
    for pair in args.view:
        if '=' not in pair:
            ap.error('--view needs name=path')
        name, path=pair.split('=',1)
        if name in parsed:
            ap.error(f'duplicate --view {name}')
        parsed[name]=Path(path)
    if args.sheet and not args.layout:
        ap.error('Supply --layout four-columns for a sheet (explicit assumption)')
    boxes=json.loads(args.boxes_json.read_text()) if args.boxes_json else None
    result=create_pack(args.out, args.sheet, parsed or None, tuple(args.order.split(',')), args.content_y, boxes)
    print(json.dumps({'out': str(args.out), 'views': list(result['source_views']), 'gate': result['gate']}))

if __name__=='__main__':
    main()
