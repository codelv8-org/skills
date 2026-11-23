#!/usr/bin/env python3
"""Evidence-based, calibrated, per-part multi-view silhouette & landmark gate.

Input is an explicit assessment JSON with independently prepared source/render
views and verified binary masks. IoU is NOT a percent likeness score.
Only a reviewer can set the qualitative checks and camera-verification flags.

Usage: python scripts/part_fidelity.py assessment.json --out gate.json --board board.png
Requirements: Pillow, NumPy. Does NOT perform segmentation, camera matching,
3D reconstruction, artistic review or browser testing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw
from inspect_character_glb import inspect as inspect_glb
from inspect_skinning import parse as parse_geometry_glb, accessor as decode_accessor

VIEWS = ("front", "back", "left", "right")
# Keep the non-optional review contract here so standalone regression assessments
# cannot obtain PASS by deleting criteria from a stage template.
PART_CHECKS = {
    'HEAD': ('cranium_and_jaw_shape', 'hair_volume_front_back_profiles', 'eyebrows_eyes_nose_ears', 'head_to_body_proportion'),
    'TORSO': ('shoulder_width_depth', 'neck_chest_waist_ratios', 'uniform_hem_collar', 'side_and_back_torso'),
    'ARMS_HANDS': ('upper_arm_forearm_lengths', 'shoulder_elbow_wrist_position', 'hand_palm_thumb_fingers', 'sleeve_cuffs'),
    'LEGS_FEET': ('thigh_shin_proportions', 'hip_knee_ankle_alignment', 'shoe_silhouette_profiles', 'foot_ground_contact'),
    'OUTFIT_GEAR': ('badge_belt_positions', 'shoulder_bag_side_and_depth', 'strap_path_front_back', 'faceted_garment_language'),
    'INTEGRATION': ('total_character_silhouette', 'neck_shoulder_hip_seams', 'ref_landmark_consistency', 'visible_face_and_gear'),
}
MIN_LANDMARKS = dict(zip(PART_CHECKS, (5, 3, 4, 4, 2, 5)))


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _resolve(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    if not isinstance(value, str):
        raise ValueError('Evidence paths must be strings')
    p = Path(value)
    return p if p.is_absolute() else base / p


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _input_paths(config_path: Path) -> set[Path]:
    """Include declared paths, even missing evidence, before any CLI output write."""
    protected = {config_path.resolve()}
    data = json.loads(config_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return protected
    base = config_path.resolve().parent
    values = [data.get('model_asset')]
    views = data.get('views', {})
    for view in views.values() if isinstance(views, dict) else []:
        if isinstance(view, dict):
            values.extend(view.get(key) for key in ('reference_image', 'render_image', 'reference_mask', 'render_mask'))
    for key in ('review', 'human_review'):
        review = data.get(key, {})
        checks = review.get('checks', []) if isinstance(review, dict) else []
        if isinstance(checks, list):
            values.extend(check.get('evidence') for check in checks if isinstance(check, dict))
    calibration = data.get('camera_calibration', {})
    if isinstance(calibration, dict):
        values.append(calibration.get('interpretation_evidence'))
    for value in values:
        if isinstance(value, str) and value:
            protected.add(_resolve(base, value).resolve())
    return protected


def _collides(path: Path, protected: set[Path]) -> bool:
    return path.resolve() in protected or (path.exists() and any(p.exists() and path.samefile(p) for p in protected))


def _validate_mesh_snapshot(path: Path) -> None:
    if path.suffix.lower() != '.glb':
        raise ValueError('Stage requires exported .glb snapshot, not a screenshot or uninspected .blend')
    # Structural validation is deliberately separate from the artistic gate.
    result = inspect_glb(path, max_triangles=float('inf'), max_mb=float('inf'))
    if result['errors']:
        raise ValueError('GLB structural errors: ' + '; '.join(result['errors']))
    if result['triangles_instantiated'] <= 0:
        raise ValueError('Stage gate requires TRIANGLES geometry; convert triangle strips/fans to mode 4 before assessment')
    doc, binary = parse_geometry_glb(path)

    def decoded(index, kind):
        if type(index) is not int or not 0 <= index < len(doc.get('accessors', [])):
            raise ValueError('Invalid geometry accessor index')
        acc = doc['accessors'][index]
        allowed = (5126,) if kind == 'VEC3' else (5121, 5123, 5125)
        if acc.get('type') != kind or acc.get('componentType') not in allowed or acc.get('sparse'):
            raise ValueError('Stage gate requires decoded, nonsparse POSITION/triangle-index accessors')
        if 'bufferView' not in acc:
            raise ValueError('Geometry accessor has no embedded payload')
        view = doc['bufferViews'][acc['bufferView']]
        count, offset = acc.get('count'), acc.get('byteOffset', 0)
        element = 12 if kind == 'VEC3' else {5121: 1, 5123: 2, 5125: 4}[acc['componentType']]
        stride = view.get('byteStride', element)
        if (type(count) is not int or count < 3 or type(offset) is not int or offset < 0 or
                type(stride) is not int or stride < element or
                offset + (count - 1) * stride + element > view['byteLength']):
            raise ValueError('Geometry accessor payload exceeds its bufferView or has invalid stride/count')
        values = decode_accessor(doc, binary, index)
        if not np.isfinite(values).all():
            raise ValueError('Geometry contains nonfinite vertex/index data')
        return values

    scenes = doc.get('scenes', [])
    scene = doc.get('scene', 0)
    if type(scene) is not int or not 0 <= scene < len(scenes):
        raise ValueError('GLB has no valid active scene')
    pending, visited, reachable_meshes = list(scenes[scene].get('nodes', [])), set(), set()
    nodes = doc.get('nodes', [])
    while pending:
        index = pending.pop()
        if type(index) is not int or not 0 <= index < len(nodes):
            raise ValueError('Scene references an invalid node')
        if index in visited:
            continue
        visited.add(index)
        node = nodes[index]
        pending.extend(node.get('children', []))
        if 'mesh' in node:
            reachable_meshes.add(node['mesh'])
    usable = False
    for mesh_index in reachable_meshes:
        for primitive in doc['meshes'][mesh_index].get('primitives', []):
            if primitive.get('mode', 4) != 4:
                continue
            positions = decoded(primitive['attributes']['POSITION'], 'VEC3').astype('float64')
            indices = (decoded(primitive['indices'], 'SCALAR').reshape(-1).astype('int64')
                       if 'indices' in primitive else np.arange(len(positions)))
            if len(indices) % 3 or (indices < 0).any() or (indices >= len(positions)).any():
                raise ValueError('Triangle indices are invalid or outside the vertex range')
            triangles = positions[indices.reshape(-1, 3)]
            areas = np.linalg.norm(np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]), axis=1)
            usable |= bool(np.any(areas > 0))
    if not usable:
        raise ValueError('No nondegenerate triangle geometry is reachable in the active scene')


def _load_image(path: Path):
    with Image.open(path) as im:
        if im.format != 'PNG':
            raise ValueError(f'Expected PNG evidence: {path}')
        rgba = ImageOps.exif_transpose(im).convert('RGBA')
        if min(rgba.size) < 32:
            raise ValueError(f'Evidence image is too small to review: {path}')
        # Inspect visible pixels, not hidden RGB data under transparent pixels.
        rgb = np.asarray(Image.alpha_composite(Image.new('RGBA', rgba.size, 'white'), rgba).convert('RGB'))
    if not np.any(np.ptp(rgb, axis=(0, 1)) > 1):
        raise ValueError(f'Blank or uniform evidence image: {path}')
    return rgb


def _load_mask(path: Path):
    with Image.open(path) as im:
        if im.format != 'PNG':
            raise ValueError(f'Expected PNG binary mask: {path}')
        grey = ImageOps.exif_transpose(im).convert('L')
        arr = np.asarray(grey, dtype=np.uint8)
    # Require truly annotated binary silhouettes: arbitrary photos cannot be masks.
    if not np.all((arr <= 5) | (arr >= 250)):
        raise ValueError(f'Expected binary (black/white) mask: {path}')
    return arr >= 250


def _bbox(mask):
    if mask.ndim != 2 or min(mask.shape) < 32:
        raise ValueError('Mask canvas must be at least 32 pixels in each dimension')
    yy, xx = np.where(mask)
    if xx.size < 20:
        raise ValueError('Binary silhouette has fewer than 20 foreground pixels')
    if xx.size >= mask.size * .98:
        raise ValueError('Mask lacks meaningful background; review part segmentation/crop')
    bounds = (int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1))
    if min(bounds[2]-bounds[0], bounds[3]-bounds[1]) < 16:
        raise ValueError('Part silhouette is too small to evaluate; render a larger calibrated canvas')
    return bounds


def compute_metrics(ref_mask, render_mask, landmarks: dict | None = None) -> dict:
    if ref_mask.shape != render_mask.shape:
        raise ValueError('Reference/render masks have different dimensions; register cameras/canvas first')
    rb = _bbox(ref_mask)
    mb = _bbox(render_mask)
    intersection = int(np.logical_and(ref_mask, render_mask).sum())
    union = int(np.logical_or(ref_mask, render_mask).sum())
    iou = intersection / union if union else 0
    rw, rh = rb[2]-rb[0],rb[3]-rb[1]
    mw, mh = mb[2]-mb[0],mb[3]-mb[1]
    bbox_err = max(abs(rw-mw)/rw, abs(rh-mh)/rh)
    # width/height differences and positional center must not be hidden by an automatically rescaled alignment.
    ref_center = ((rb[0]+rb[2])*.5, (rb[1]+rb[3])*.5)
    mod_center = ((mb[0]+mb[2])*.5, (mb[1]+mb[3])*.5)
    centroid_err = float(np.linalg.norm(np.subtract(ref_center,mod_center)) / rh)
    errors = {}
    if landmarks is not None and not isinstance(landmarks, dict):
        raise ValueError('Landmarks must be named paired observations')
    seen_reference = set()
    seen_render = set()
    for name, datum in (landmarks or {}).items():
        if not _text(name) or not isinstance(datum, dict):
            raise ValueError('Landmarks require a nonempty name and paired observations')
        a,b = datum.get('reference'), datum.get('render')
        if (not isinstance(a, (list, tuple)) or not isinstance(b, (list, tuple)) or
                len(a)!=2 or len(b)!=2 or not all(_number(v) and 0<=v<=1 for v in [*a,*b])):
            raise ValueError(f'Landmark {name}: expected normalized x,y pairs in [0,1]')
        if tuple(a) in seen_reference or tuple(b) in seen_render:
            raise ValueError(f'Landmark {name}: duplicate coordinates cannot count as independent visible features')
        seen_reference.add(tuple(a)); seen_render.add(tuple(b))
        px = np.array(ref_mask.shape[::-1],dtype=float)
        errors[name] = float(np.linalg.norm((np.asarray(a)-np.asarray(b))*px)/rh)
    return {
        'silhouette_iou': round(iou,5),
        'silhouette_overlap_percent_NOT_likeness': round(100*iou,2),
        'bbox_size_error_ratio': round(float(bbox_err),5),
        'bbox_center_error_ref_height': round(centroid_err,5),
        'landmark_errors_ref_height': {k:round(v,5) for k,v in errors.items()},
        'mean_landmark_error_ref_height': round(sum(errors.values())/len(errors),5) if errors else None,
        'reference_bounds_px': list(rb),
        'model_bounds_px': list(mb),
        'canvas_width_height_px': list(ref_mask.shape[::-1]),
    }


def _board(data: dict, source_dir: Path, target: Path, metrics: dict) -> None:
    views = data.get('required_views',list(VIEWS))
    w,h = 330,290
    outer=Image.new('RGB',(w*len(views), h*3+30),(238,241,247))
    draw=ImageDraw.Draw(outer)
    calibrated = data.get('camera_calibration', {}).get('verified') is True
    labels=('REFERENCE','MODEL','CALIBRATED MASK OVERLAP' if calibrated else 'DIAGNOSTIC MASK / NO CALIBRATION')
    for col, view in enumerate(views):
        files = data.get('views',{}).get(view,{})
        for row, typ in enumerate(('reference_image','render_image','_overlay')):
            x,y=col*w,row*h+30
            pad=Image.new('RGB',(w-12,h-30),(246,247,250))
            try:
                if typ == '_overlay':
                    if not files.get('reference_mask') or not files.get('render_mask'):
                        raise ValueError('Missing mask; keep diagnostic placeholder')
                    rm=_load_mask(_resolve(source_dir,files['reference_mask']))
                    mm=_load_mask(_resolve(source_dir,files['render_mask']))
                    if rm.shape!=mm.shape: raise ValueError('mask shapes mismatch')
                    array=np.zeros((*rm.shape,3),dtype=np.uint8);array[:]=(247,248,251)
                    array[rm & ~mm]=[240,87,99]  # reference-only red
                    array[~rm & mm]=[84,130,242]  # render-only blue
                    array[rm & mm]=[56,173,135]  # overlap green
                    src=Image.fromarray(array,'RGB')
                else:
                    if not files.get(typ):
                        raise ValueError('Missing evidence image')
                    src=ImageOps.exif_transpose(Image.open(_resolve(source_dir,files[typ]))).convert('RGB')
                src.thumbnail((w-24,h-40),Image.Resampling.LANCZOS)
                pad.paste(src,((pad.width-src.width)//2,(pad.height-src.height)//2))
            except (KeyError,FileNotFoundError,OSError,ValueError):
                ImageDraw.Draw(pad).text((12,20),'MISSING / NOT REVIEWED', fill=(176,48,48))
            outer.paste(pad,(x+6,y+6))
            draw.text((x+10,y+8),labels[row],fill=(30,40,58))
        title=metrics.get(view,{}).get('silhouette_iou')
        draw.text((col*w+12,10),f'{view.upper()}  '+(f'IoU {title:.3f}' if title is not None else 'NO METRIC'),fill=(15,25,41))
    target.parent.mkdir(parents=True,exist_ok=True)
    outer.save(target)


def _evaluate(config_path: Path, board_path: Path | None = None) -> dict:
    data = json.loads(config_path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Assessment must be a JSON object')
    source_dir = config_path.resolve().parent
    name = str(data.get('part', '')).upper()
    required = data.get('required_views', list(VIEWS))
    if (name not in PART_CHECKS or not isinstance(required, list) or not required or
            not all(isinstance(v, str) and v in VIEWS for v in required) or len(set(required)) != len(required)):
        raise ValueError('Invalid part or required_views (nonempty unique named views required)')
    missing, failures, bad = [], [], []
    if set(required) != set(VIEWS):
        missing.append('Four-view evidence is incomplete; absent/inferred views cannot silently pass')
    views = data.get('views', {})
    if not isinstance(views, dict):
        raise ValueError('views must be an object')
    asset = _resolve(source_dir, data.get('model_asset'))
    asset_sha = _sha(asset) if asset and asset.is_file() else None
    if asset_sha:
        try:
            _validate_mesh_snapshot(asset)
        except (ValueError, OSError, UnicodeError, struct.error, TypeError, KeyError, IndexError, AttributeError) as exc:
            bad.append(f'model_asset: {exc}')
    else:
        missing.append('model_asset (real .glb)')
    thresholds = data.get('thresholds', {})
    if not isinstance(thresholds, dict):
        raise ValueError('thresholds must be an object')
    min_iou = thresholds.get('min_silhouette_iou', .82)
    max_size = thresholds.get('max_bbox_size_error_ratio', .10)
    max_ctr = thresholds.get('max_bbox_center_error_ref_height', .06)
    max_lm = thresholds.get('max_mean_landmark_error_ref_height', .055)
    min_landmarks = thresholds.get('min_landmarks_total', MIN_LANDMARKS[name])
    if (not all(_number(v) for v in (min_iou, max_size, max_ctr, max_lm)) or
            not (0 < min_iou <= 1 and 0 <= max_size <= 1 and 0 <= max_ctr <= 1 and 0 <= max_lm <= 1) or
            type(min_landmarks) is not int or min_landmarks < MIN_LANDMARKS[name]):
        raise ValueError('Invalid threshold range or reduced mandatory landmark count')
    by_view = {}
    n_landmarks = 0
    evidence_paths = set()
    view_files_seen = set()
    for view in required:
        item = views.get(view, {})
        if not isinstance(item, dict):
            raise ValueError(f'{view}: view evidence must be an object')
        needed = ('reference_image', 'render_image', 'reference_mask', 'render_mask')
        files = {k: _resolve(source_dir, item.get(k)) for k in needed}
        for key, path in files.items():
            if path is None or not path.is_file():
                missing.append(f'{view}.{key}')
            else:
                evidence_paths.add(path.resolve())
        if any(path is None or not path.is_file() for path in files.values()):
            continue
        try:
            if len({path.resolve() for path in files.values()}) != len(files):
                raise ValueError('Reference/render images and masks must be independently saved files')
            resolved_files = {path.resolve() for path in files.values()}
            if resolved_files & view_files_seen:
                raise ValueError('Different view labels must not reuse the same evidence files')
            view_files_seen.update(resolved_files)
            rm = _load_mask(files['reference_mask'])
            mm = _load_mask(files['render_mask'])
            ref_image = _load_image(files['reference_image'])
            mod_image = _load_image(files['render_image'])
            if ref_image.shape != mod_image.shape or ref_image.shape[:2] != rm.shape:
                raise ValueError('Images and masks must use same calibrated canvas dimensions')
            if np.array_equal(ref_image, mod_image):
                raise ValueError('Reference and render pixels are identical; copied evidence is not a model render')
            metrics = compute_metrics(rm, mm, item.get('landmarks'))
            n_landmarks += len(metrics['landmark_errors_ref_height'])
            by_view[view] = metrics
            if metrics['silhouette_iou'] < min_iou:
                failures.append(f'{view}: IoU {metrics["silhouette_iou"]:.3f} < {min_iou:.3f}')
            if metrics['bbox_size_error_ratio'] > max_size:
                failures.append(f'{view}: bbox size mismatch')
            if metrics['bbox_center_error_ref_height'] > max_ctr:
                failures.append(f'{view}: center/camera mismatch')
            if metrics['mean_landmark_error_ref_height'] is not None and metrics['mean_landmark_error_ref_height'] > max_lm:
                failures.append(f'{view}: landmarks out of tolerance')
        except (ValueError, OSError) as exc:
            bad.append(f'{view}: {exc}')
    if n_landmarks < min_landmarks:
        missing.append(f'landmarks: annotated {n_landmarks}/{min_landmarks}')

    # Read legacy input keys, but never infer that the reviewer is human.
    if 'review' in data and 'human_review' in data:
        raise ValueError('Use one review object; review and legacy human_review cannot coexist')
    review = data.get('review', data.get('human_review', {}))
    if not isinstance(review, dict):
        raise ValueError('review must be an object')
    reviewer_type = review.get('reviewer_type')
    if (not _text(review.get('reviewer')) or review.get('approved') is not True or
            not _text(review.get('notes')) or reviewer_type not in ('HUMAN', 'AI') or
            review.get('independent_from_author') is not True):
        missing.append('review: identified HUMAN/AI independent reviewer, explicit approval and notes required')
    author = data.get('model_author')
    if not _text(author):
        missing.append('model_author: identify the geometry author separately from the reviewer')
    elif _text(review.get('reviewer')) and author.strip().casefold() == review['reviewer'].strip().casefold():
        bad.append('The geometry author cannot be their own independent reviewer')
    if not asset_sha or review.get('render_model_sha256') != asset_sha:
        missing.append('review.render_model_sha256 matching actual GLB: render provenance not verified')
    checks = review.get('checks', [])
    if not isinstance(checks, list) or not all(isinstance(c, dict) for c in checks):
        raise ValueError('review.checks must be a list of named criteria')
    ids = [c.get('id') for c in checks]
    if not all(_text(value) for value in ids) or len(set(ids)) != len(ids):
        raise ValueError('Review check IDs must be nonempty and unique')
    absent = set(PART_CHECKS[name]) - set(ids)
    if absent:
        missing.append('mandatory review checks: ' + ', '.join(sorted(absent)))
    all_checks = []
    reviewed_images = set()
    for check in checks:
        ident, rating, weight = check['id'], check.get('rating'), check.get('weight', 1)
        # Evidence belongs to review context even before a reviewer supplies a
        # rating, so obtaining the required digest never requires pre-approval.
        evidence = _resolve(source_dir, check.get('evidence'))
        if evidence is not None and evidence.is_file():
            evidence_paths.add(evidence.resolve())
        if ident in PART_CHECKS[name] and check.get('critical') is not True:
            bad.append(f'review {ident}: mandatory criteria must remain critical')
        if not _number(weight) or weight <= 0:
            bad.append(f'review {ident}: weight must be finite and positive')
            continue
        if not _number(rating) or not 0 <= rating <= 5:
            missing.append(f'review_rating:{ident}')
            continue
        if evidence is None or not evidence.is_file():
            missing.append(f'review_evidence:{ident}')
        else:
            evidence = evidence.resolve()
            evidence_paths.add(evidence)
            if evidence not in reviewed_images:
                try:
                    _load_image(evidence)
                except (ValueError, OSError) as exc:
                    bad.append(f'review_evidence:{ident}: {exc}')
                reviewed_images.add(evidence)
        if not _text(check.get('notes')):
            missing.append(f'review_notes:{ident}')
        all_checks.append((rating, weight))
        if check.get('critical') is True and rating < 4:
            failures.append(f'reviewer critical {ident}: {rating}/5')
    weighted_min = review.get('weighted_min', 4.3)
    if not _number(weighted_min) or not 4.3 <= weighted_min <= 5:
        raise ValueError('Review weighted_min must be a finite number from 4.3 to 5')
    # Normalize positive weights before summing so very large weights cannot
    # overflow into NaN and bypass the minimum rating comparison.
    weighted = None
    if all_checks:
        largest = max(weight for _, weight in all_checks)
        weighted = sum(rating * (weight / largest) for rating, weight in all_checks) / sum(weight / largest for _, weight in all_checks)
        if weighted < weighted_min:
            failures.append(f'reviewer weighted rating {weighted:.3f}/5 below target')

    calibration = data.get('camera_calibration', {})
    if not isinstance(calibration, dict):
        raise ValueError('camera_calibration must be an object')
    if (calibration.get('verified') is not True or calibration.get('projection') not in ('ORTHOGRAPHIC', 'PERSPECTIVE') or
            not _text(calibration.get('method'))):
        missing.append('camera_calibration: verified boolean, known projection and documented method required')
    basis = calibration.get('reference_basis', 'OBSERVED_REFERENCE')
    if basis not in ('OBSERVED_REFERENCE', 'APPROVED_DESIGN_INTERPRETATION'):
        bad.append('Unknown camera_calibration.reference_basis')
    if calibration.get('diagnostic_only', False) is not False:
        failures.append('Camera/reference correspondence is diagnostic only; resolve the design interpretation before PASS')
    if basis == 'APPROVED_DESIGN_INTERPRETATION':
        interpretation = _resolve(source_dir, calibration.get('interpretation_evidence'))
        if interpretation is None or not interpretation.is_file() or not _text(calibration.get('limitations')):
            missing.append('Approved interpretation requires documented source conflicts/inferred features and approval evidence')
        elif not interpretation.read_text(encoding='utf-8').strip():
            missing.append('Design interpretation approval evidence is empty')
        else:
            evidence_paths.add(interpretation.resolve())
    if board_path:
        protected = _input_paths(config_path)
        if _collides(board_path, protected):
            bad.append('Comparison board output would overwrite assessment/model/input evidence')
        else:
            _board(data, source_dir, board_path, by_view)
    evidence_hashes = {str(path): _sha(path) for path in sorted(evidence_paths)}
    context = {
        'assessment_inputs': {key: value for key, value in data.items() if key not in ('review', 'human_review')},
        'review_rubric': {'weighted_min': weighted_min, 'checks': [
            {key: check.get(key) for key in ('id', 'critical', 'weight', 'evidence')} for check in checks]},
        'model_sha256': asset_sha,
        'evidence_sha256': evidence_hashes,
    }
    required_context = hashlib.sha256(json.dumps(context, sort_keys=True, separators=(',', ':'),
                                                 ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()
    if review.get('context_sha256') != required_context:
        missing.append('review.context_sha256 is missing/stale; current inputs require independent review')
    return {
        'schema_version': '4.1',
        'part': name,
        'assessment_path': str(config_path.resolve()),
        'assessment_sha256': _sha(config_path),
        'evidence_sha256': evidence_hashes,
        'status': 'BLOCKED' if bad else ('NOT_TESTED' if missing else ('REVIEW_REQUIRED' if failures else 'PASS')),
        'model_asset': str(asset.resolve()) if asset else None,
        'model_sha256': asset_sha,
        'camera_calibration': calibration,
        'fidelity_scope': basis,
        'metric_labels': {'iou': 'mask intersection/union only; not human likeness or image similarity percentage',
                          'landmark_error': '2D landmark distance divided by reference-mask height'},
        'view_metrics': by_view,
        'reviewer_type': reviewer_type,
        'reviewer': review.get('reviewer'),
        'reviewer_weighted_rating_0to5': round(weighted, 3) if weighted is not None else None,
        'reviewer_approved': review.get('approved') is True,
        'review_context_sha256': review.get('context_sha256'),
        'required_review_context_sha256': required_context,
        # Compatibility fields retain their literal meaning; AI review is never human approval.
        'human_weighted_rating_0to5': round(weighted, 3) if weighted is not None and reviewer_type == 'HUMAN' else None,
        'human_approved': review.get('approved') is True and reviewer_type == 'HUMAN',
        'thresholds': thresholds,
        'missing_evidence': missing,
        'failures': failures,
        'invalid_evidence': bad,
        'board_file': str(board_path) if board_path else None,
        'verification_limits': 'Hashes detect changed files, not who created them or whether a render came from this mesh. Independent visual/provenance review is still required.',
    }


def evaluate(config_path: Path, board_path: Path | None = None) -> dict:
    """Return an explicit failed gate for malformed evidence instead of crashing."""
    try:
        return _evaluate(config_path, board_path)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError) as exc:
        return {'status': 'BLOCKED', 'error': str(exc), 'assessment_path': str(config_path.resolve())}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('assessment',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--board',type=Path)
    args=p.parse_args()
    try:
        protected = _input_paths(args.assessment)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        protected = {args.assessment.resolve()}
    if (_collides(args.out, protected) or
            (args.board is not None and _collides(args.out, {args.board.resolve()}))):
        print(json.dumps({'status': 'BLOCKED', 'error': 'Output path collides with assessment, model, input evidence or comparison board; nothing written'}))
        raise SystemExit(2)
    res=evaluate(args.assessment,args.board)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'part':res.get('part'),'status':res['status'],'failures':res.get('failures'),'missing':res.get('missing_evidence')},ensure_ascii=False))
    if res['status']=='BLOCKED':raise SystemExit(2)


if __name__=='__main__':main()
