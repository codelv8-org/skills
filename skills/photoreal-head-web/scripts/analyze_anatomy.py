#!/usr/bin/env python3
"""Check manually annotated 3D facial landmarks for gross structure and fit.

This cannot certify anatomic correctness, photorealism, identity, or face similarity.
Coordinates must be Blender-local: +X subject-left, -Y forward, +Z up.
Run without Blender: python scripts/analyze_anatomy.py landmarks.json ...
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

MANDATORY = (
    'n', 'prn', 'sn', 'sto', 'gn',
    'en_l', 'en_r', 'ex_l', 'ex_r',
    'al_l', 'al_r', 'ch_l', 'ch_r',
    't_l', 't_r',
)
EXTRA_FOR_HIFI = ('se', 'rh', 'g', 'pg', 'sa_l', 'sa_r', 'sba_l', 'sba_r')
MIDLINE = ('n', 'se', 'rh', 'prn', 'sn', 'sto', 'gn', 'g', 'pg', 'ls', 'li')
BILATERAL = ('en', 'ex', 'al', 'ch', 't', 'sa', 'sba', 'ac', 'sbal', 'cph')

MEASURES = {
    'outercanthal_width': ('ex_l', 'ex_r'),
    'intercanthal_width': ('en_l', 'en_r'),
    'left_eye_fissure': ('en_l', 'ex_l'),
    'right_eye_fissure': ('en_r', 'ex_r'),
    'nasal_width': ('al_l', 'al_r'),
    'nose_height': ('n', 'sn'),
    'upper_face_height': ('n', 'sto'),
    'facial_height': ('n', 'gn'),
    'lower_face_height': ('sn', 'gn'),
    'upper_lip_height': ('sn', 'sto'),
    'mouth_width': ('ch_l', 'ch_r'),
    'tragion_width': ('t_l', 't_r'),
    'nasal_tip_to_root': ('prn', 'n'),
    'nasal_bridge_segment': ('se', 'rh'),
    'nasal_bridge_to_tip': ('rh', 'prn'),
    'nasal_root_to_tip': ('se', 'prn'),
    'nasal_tip_to_subnasale': ('prn', 'sn'),
    'left_ear_height': ('sa_l', 'sba_l'),
    'right_ear_height': ('sa_r', 'sba_r'),
}


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def load_landmarks(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('coordinate_system') != 'blender_local_z_up_front_minus_y':
        raise ValueError('Expected coordinate_system=blender_local_z_up_front_minus_y')
    if data.get('units') != 'meters':
        raise ValueError('Expected units=meters; convert all landmarks first')
    points = data.get('landmarks', {})
    if not isinstance(points, dict):
        raise ValueError('landmarks must be an object keyed by landmark name')
    validated = {}
    for key, coords in points.items():
        if (not isinstance(coords, list) or len(coords) != 3 or
                any(not isinstance(c, (int, float)) or not math.isfinite(c) for c in coords)):
            raise ValueError(f'Invalid 3D coordinate for {key!r}')
        validated[key] = [float(c) for c in coords]
    return validated


def measures(points):
    return {
        label: distance(points[a], points[b])
        for label, (a, b) in MEASURES.items()
        if a in points and b in points
    }


def check(points, reference=None, tolerance=0.08, high_fidelity=False):
    errors, warnings = [], []
    missing = [k for k in MANDATORY if k not in points]
    if missing:
        errors.append('Missing mandatory landmarks: ' + ', '.join(missing))
    hifi_missing = [k for k in EXTRA_FOR_HIFI if k not in points] if high_fidelity else []
    if hifi_missing:
        errors.append('High-fidelity mode requires nose bridge, ears and chin markers: ' + ', '.join(hifi_missing))
    values = measures(points)
    ref_vals = measures(reference) if reference else {}
    width = values.get('outercanthal_width', 0.0)
    if width <= 0:
        errors.append('Missing or zero outercanthal width; cannot normalize facial metrics')
        width = None
    if width is not None:
        for label in MIDLINE:
            if label in points and abs(points[label][0]) > 0.12 * width:
                warnings.append(f'{label}: midline offset exceeds 12% of outercanthal width; inspect anatomy or orientation')
    for name in BILATERAL:
        left, right = points.get(name + '_l'), points.get(name + '_r')
        if left is not None and right is not None:
            if left[0] <= right[0]:
                errors.append(f'{name}: subject-left X must exceed subject-right X')
            if left[0] <= 0 or right[0] >= 0:
                warnings.append(f'{name}: pair does not straddle the +X/-X midline; inspect orientation')
    for side in ('l', 'r'):
        en = points.get('en_' + side)
        ex = points.get('ex_' + side)
        if en and ex and abs(en[0]) >= abs(ex[0]):
            errors.append(f'{side}: inner canthus is not medial to outer canthus')
    for above, below in [('n', 'sn'), ('sn', 'sto'), ('sto', 'gn'), ('se', 'rh'), ('rh', 'prn')]:
        if above in points and below in points and points[above][2] <= points[below][2]:
            errors.append(f'Incorrect vertical order: {above} should be above {below}')
    if 'prn' in points and 'sn' in points and points['prn'][1] >= points['sn'][1]:
        warnings.append('Nose tip not anterior to subnasale (-Y forward); verify side silhouette')
    if 'se' in points and 'rh' in points and points['rh'][1] >= points['se'][1]:
        warnings.append('Rhinion is not anterior to sellion; inspect nasal bridge profile and marking')
    if 'rh' in points and 'prn' in points and points['prn'][1] >= points['rh'][1]:
        warnings.append('Nasal tip not anterior to rhinion; inspect nasal profile (dorsal hump can vary)')
    if 'n' in points and 'se' in points and points['n'][2] <= points['se'][2]:
        warnings.append('Nasion not superior to sellion; verify difference in landmark definition')
    for side in ('l', 'r'):
        ear = points.get('t_' + side)
        outer_eye = points.get('ex_' + side)
        if ear and outer_eye:
            if abs(ear[0]) <= abs(outer_eye[0]):
                warnings.append(f'{side}: tragion not farther lateral than outer canthus')
            if ear[1] <= outer_eye[1]:
                warnings.append(f'{side}: tragion not posterior to eye; inspect profile')
    for side in ('l', 'r'):
        top, bottom = points.get('sa_' + side), points.get('sba_' + side)
        if top and bottom and top[2] <= bottom[2]:
            errors.append(f'{side}: superior ear point not above inferior ear point')
    le, re = values.get('left_eye_fissure'), values.get('right_eye_fissure')
    if le and re and abs(le - re) / ((le + re) / 2) > 0.20:
        warnings.append('Eye fissure length asymmetry >20%; check annotations before sculpt')
    drift = {}
    if reference is not None:
        ref_width = ref_vals.get('outercanthal_width', 0)
        if ref_width <= 0 or width is None:
            errors.append('Reference and model both require valid outercanthal width')
        else:
            for name in sorted(values.keys() & ref_vals.keys()):
                if name == 'outercanthal_width':
                    continue
                a = values[name] / width
                b = ref_vals[name] / ref_width
                if b <= 1e-6:
                    continue
                delta = abs(a - b) / b
                drift[name] = {'model_ratio': round(a, 5), 'reference_ratio': round(b, 5),
                               'relative_drift': round(delta, 5)}
                if delta > tolerance:
                    errors.append(f'{name}: normalized reference drift {delta:.1%} > {tolerance:.1%}')
            if len(drift) < 5:
                warnings.append('Fewer than five comparable measurements; subject-fit validation is limited')
    if errors:
        status = 'BLOCKED'
    elif warnings or reference is None:
        status = 'REVIEW_REQUIRED'
    else:
        status = 'PASS_METRICS_ONLY'
    return {
        'status': status,
        'scope': '3D facial landmark layout and reference ratios only; NOT proof of photorealism',
        'required_landmarks_present': len(MANDATORY) - len(missing),
        'required_landmarks_total': len(MANDATORY),
        'landmark_count': len(points),
        'high_fidelity_requested': high_fidelity,
        'high_fidelity_extra_landmarks_present': len(EXTRA_FOR_HIFI) - len(hifi_missing),
        'measurements_m': {k: round(v, 6) for k, v in values.items()},
        'ratios_to_outercanthal_width': (
            {k: round(v / width, 5) for k, v in values.items()}
            if width else {}
        ),
        'reference_comparison': drift,
        'reference_available': reference is not None,
        'errors': errors,
        'warnings': warnings,
        'must_still_pass': ['human clay-sculpt review', 'front/profile/three-quarter silhouette',
                            'photo-fit comparison when photos available', 'UV+PBR', 'browser review'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('landmarks', type=Path)
    parser.add_argument('--reference-3d', type=Path,
                        help='Independent 3D landmark reference for the SAME subject, same axis convention')
    parser.add_argument('--high-fidelity', action='store_true',
                        help='Require nose-root/bridge, ear extents, glabella and chin projection markers')
    parser.add_argument('--max-drift', type=float, default=0.08,
                        help='Max relative ratio deviation (default .08 = 8%%)')
    parser.add_argument('--json', type=Path, help='Write report JSON')
    args = parser.parse_args()
    if not (0.0 < args.max_drift < 1.0):
        parser.error('--max-drift must lie between 0 and 1')
    try:
        model = load_landmarks(args.landmarks)
        reference = load_landmarks(args.reference_3d) if args.reference_3d else None
        result = check(model, reference, args.max_drift, args.high_fidelity)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {'status': 'BLOCKED', 'errors': [str(exc)], 'warnings': []}
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    print(text, end='')
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text, encoding='utf-8')
    return 2 if result['status'] == 'BLOCKED' else 0


if __name__ == '__main__':
    sys.exit(main())
