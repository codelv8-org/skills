#!/usr/bin/env python3
"""Prepare a separately labelled, unlit B1 atlas from the licensed public scan.

Authoring dependency: xatlas==0.0.11 plus requirements-projection.txt. The baseline
GLB is read-only. All source triangles, positions and normals are retained; only
UV seams change. This is not an anatomy, photographic accuracy or release gate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import io
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA256 = '9dd65d33d43987479e0f66775282803c56941cb7ea93dfe1cf0ef84250a17ed6'
sys.path.insert(0, str(ROOT / 'skills/photoreal-head-web/scripts'))
from render_uv_layout_glb import read_asset, accessor_data
from validate_head_surface import measure, validate
from project_face_texture import raster, sample, srgb_to_linear, linear_to_srgb
from benchmark_head_projection import look_at, render_uv, render_map, texture, stats


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signed_area(tri):
    a, b = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    return (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]) / 2


def triangle_chart(tri, density):
    a, b = tri[1] - tri[0], tri[2] - tri[0]
    length = np.linalg.norm(a)
    return np.array([[0., 0.], [length, 0.],
                     [np.dot(a, b) / length, np.linalg.norm(np.cross(a, b)) / length]]) * density


def pack_rectangles(extents, scale, size, padding):
    """Deterministic MaxRects packing. Rectangles include real texture gutters."""
    dims = [(int(math.ceil(w * scale)) + 2 * padding,
             int(math.ceil(h * scale)) + 2 * padding) for w, h in extents]
    order = sorted(range(len(dims)), key=lambda i: (-max(dims[i]), -dims[i][0] * dims[i][1], i))
    free, result = [(0, 0, size, size)], {}
    for i in order:
        w, h = dims[i]
        candidates = [(min(fw - w, fh - h), max(fw - w, fh - h), y, x, k)
                      for k, (x, y, fw, fh) in enumerate(free) if fw >= w and fh >= h]
        if not candidates:
            return None
        _, _, y, x, _ = min(candidates)
        result[i] = (x, y)
        split = []
        for fx, fy, fw, fh in free:
            if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                split.append((fx, fy, fw, fh))
                continue
            if x > fx: split.append((fx, fy, x - fx, fh))
            if x + w < fx + fw: split.append((x + w, fy, fx + fw - x - w, fh))
            if y > fy: split.append((fx, fy, fw, y - fy))
            if y + h < fy + fh: split.append((fx, y + h, fw, fy + fh - y - h))
        free = []
        for k, rect in enumerate(split):
            rx, ry, rw, rh = rect
            if any(k != j and sx <= rx and sy <= ry and sx + sw >= rx + rw and sy + sh >= ry + rh
                   and (rect != other or j < k)
                   for j, other in enumerate(split) for sx, sy, sw, sh in [other]):
                continue
            free.append(rect)
    return result


def packed_uv(charts, xy, size, padding):
    origins = [xy[faces].min(axis=(0, 1)) for faces in charts]
    extents = [xy[faces].max(axis=(0, 1)) - origin for faces, origin in zip(charts, origins)]
    lo, hi = 0., size / max(float(max(e)) for e in extents)
    best = None
    for _ in range(24):
        scale = (lo + hi) / 2
        placement = pack_rectangles(extents, scale, size, padding)
        if placement is None:
            hi = scale
        else:
            lo, best = scale, placement
    if best is None:
        raise ValueError('Chart gutters do not fit the requested texture size')
    uv = np.empty_like(xy, dtype=np.float64)
    for i, (faces, origin) in enumerate(zip(charts, origins)):
        uv[faces] = (xy[faces] - origin) * lo + np.array(best[i]) + padding
    return (uv / size).astype(np.float32), lo


def clean_atlas(positions, normals, indices, size, padding):
    import xatlas
    if importlib.metadata.version('xatlas') != '0.0.11':
        raise ValueError('Reproducible authoring requires xatlas==0.0.11')
    atlas = xatlas.Atlas()
    # xatlas' geometric epsilon is unsuitable for sub-millimetre facial triangles
    # in meter units. Scale its input only; exported positions remain unchanged.
    parameterization_scale = 1000.
    atlas.add_mesh(positions * parameterization_scale, indices, normals)
    chart_options = xatlas.ChartOptions()
    chart_options.fix_winding = True
    pack_options = xatlas.PackOptions()
    pack_options.resolution, pack_options.padding = size, padding
    atlas.generate(chart_options=chart_options, pack_options=pack_options)
    remap, new_indices, raw_uv = atlas[0]
    if not np.array_equal(positions[indices], positions[remap[new_indices]]):
        raise ValueError('Parameterizer changed source triangle order or positions')
    xy = raw_uv[new_indices].astype(np.float64) * [atlas.width, atlas.height]
    charts = [atlas.get_mesh_chart(0, i).faces.astype(int) for i in range(atlas.chart_count)]
    if sorted(np.concatenate(charts).tolist()) != list(range(len(indices))):
        raise ValueError('Parameterizer omitted or repeated source triangles')
    reflected = 0
    for faces in charts:
        area = signed_area(xy[faces])
        if np.all(area < 0):
            xy[faces, :, 0] *= -1
            reflected += 1
        elif not np.all(area > 0):
            raise ValueError('Parameterizer produced a degenerate or folded chart')
    world_tri = positions[indices].astype(np.float64)
    world_area = np.linalg.norm(np.cross(world_tri[:, 1] - world_tri[:, 0], world_tri[:, 2] - world_tri[:, 0]), axis=1) / 2
    density = float(np.median(np.sqrt(signed_area(xy) / world_area)))
    detached = []
    for _ in range(8):
        uv, scale = packed_uv(charts, xy, size, padding)
        metrics, errors, _, _ = measure(world_tri, uv, 'ccw')
        if not errors:
            return uv, {'parameterizer': 'xatlas==0.0.11', 'parameterization_input_scale': parameterization_scale,
                        'chart_options': {'fix_winding': True}, 'initial_charts': atlas.chart_count,
                        'final_charts': len(charts), 'reflected_charts': reflected,
                        'detached_overlap_triangles': detached, 'packing': 'deterministic MaxRects, no rotation',
                        'padding_texels_per_chart': padding, 'uv_winding': 'ccw', 'uv_metrics': metrics}
        if errors != ['overlap_pairs_found']:
            raise ValueError(f'New atlas fails exact UV checks: {errors}')
        # An exact positive-area overlap is a real chart defect. Give its most
        # involved triangle a new, isometric island. No geometry is removed.
        counts = Counter(face for pair in metrics['overlap_examples'] for face in pair)
        face = min(counts, key=lambda f: (-counts[f], f))
        if face in detached:
            raise ValueError('Detached triangle still overlaps after rectangle packing')
        charts = [faces[faces != face] for faces in charts]
        charts = [faces for faces in charts if len(faces)]
        charts.append(np.array([face]))
        xy[face] = triangle_chart(world_tri[face], density)
        detached.append(face)
    raise ValueError('Exact UV repair did not converge')


def bake_color(old_uv, new_uv, source, size, padding):
    ids, _, weights, hits = raster(new_uv.astype(np.float64) * size - .5, np.ones((len(new_uv), 3)), size, size, False)
    if np.any(hits > 1):
        raise ValueError('Exact-passing atlas still has raster collisions')
    occupied = ids >= 0
    w = weights[occupied].astype(np.float64)
    w = np.c_[w, 1 - w.sum(axis=1)]
    coords = np.einsum('ni,nij->nj', w, old_uv[ids[occupied]])
    linear = np.zeros((size, size, 3), np.float32)
    linear[occupied] = sample(source, coords * [source.shape[1], source.shape[0]] - .5)
    dist, nearest = distance_transform_edt(~occupied, return_indices=True)
    gutter = (~occupied) & (dist <= padding + 1)
    linear[gutter] = linear[nearest[0][gutter], nearest[1][gutter]]
    rgb = np.uint8(np.rint(linear_to_srgb(linear) * 255))
    return rgb, {'method': 'per-triangle barycentric UV transfer, bilinear source sampling in linear RGB',
                 'source_coordinate_correction': 'Sample source image at (u, 1-v). The legacy baseline GLB stores bottom-origin V against an upright image; nose/scalp/eyes are vertically misplaced with glTF top-origin sampling. The original GLB remains unchanged.',
                 'texture_size': [size, size], 'occupied_texels': int(occupied.sum()),
                 'sampled_overlap_pixels': int(np.count_nonzero(hits > 1)),
                 'gutter': 'nearest observed edge dilation only; no inferred skin filling'}


def write_glb(path, source_json, positions, normals, old_indices, uv, rgb):
    # Expand seams explicitly; triangle order, positions and source normals are
    # identical. This unlit benchmark model intentionally has no tangent normal.
    p = positions[old_indices].reshape(-1, 3).astype('<f4')
    n = normals[old_indices].reshape(-1, 3).astype('<f4')
    u = uv.reshape(-1, 2).astype('<f4')
    # Deduplicate only byte-identical position/normal/UV tuples, preserving seams.
    combo = np.concatenate([p, n, u], axis=1)
    unique, remap = np.unique(combo, axis=0, return_inverse=True)
    p, n, u = unique[:, :3].copy(), unique[:, 3:6].copy(), unique[:, 6:].copy()
    indices = remap.astype('<u2' if len(unique) < 65536 else '<u4')
    stream, views, accessors = bytearray(), [], []
    def append(data, target=None):
        while len(stream) % 4: stream.append(0)
        view = {'buffer': 0, 'byteOffset': len(stream), 'byteLength': len(data)}
        if target is not None: view['target'] = target
        views.append(view); stream.extend(data)
        return len(views) - 1
    for arr, typ, comp, target in [(p, 'VEC3', 5126, 34962), (n, 'VEC3', 5126, 34962),
                                   (u, 'VEC2', 5126, 34962), (indices, 'SCALAR', 5123 if indices.dtype.itemsize == 2 else 5125, 34963)]:
        acc = {'bufferView': append(arr.tobytes(), target), 'componentType': comp, 'count': len(arr), 'type': typ}
        if typ == 'VEC3' and not accessors:
            acc['min'], acc['max'] = p.min(axis=0).tolist(), p.max(axis=0).tolist()
        accessors.append(acc)
    image_data = io.BytesIO(); Image.fromarray(rgb).save(image_data, format='PNG', optimize=True)
    image_view = append(image_data.getvalue())
    j = {'asset': {'version': '2.0', 'generator': 'prepare-photoreal-atlas.py; unlit B1 derived atlas'},
         'scene': source_json.get('scene', 0), 'scenes': copy.deepcopy(source_json['scenes']),
         'nodes': copy.deepcopy(source_json['nodes']), 'meshes': [{'name': 'Head_Scan_B1_Projection_Atlas', 'primitives': [
             {'attributes': {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2}, 'indices': 3, 'material': 0}]}],
         'materials': [{'name': 'B1 scan color - repaired UV atlas', 'doubleSided': True,
                        'extensions': {'KHR_materials_unlit': {}},
                        'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicFactor': 0, 'roughnessFactor': 1}}],
         'extensionsUsed': ['KHR_materials_unlit'], 'extensionsRequired': ['KHR_materials_unlit'],
         'textures': [{'sampler': 0, 'source': 0}],
         'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071}],
         'images': [{'bufferView': image_view, 'mimeType': 'image/png', 'name': 'Transferred licensed scan color'}],
         'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(stream)}]}
    payload = json.dumps(j, separators=(',', ':')).encode('utf-8')
    payload += b' ' * (-len(payload) % 4); stream.extend(b'\0' * (-len(stream) % 4))
    data = b'glTF' + struct.pack('<II', 2, 12 + 8 + len(payload) + 8 + len(stream))
    data += struct.pack('<I4s', len(payload), b'JSON') + payload
    data += struct.pack('<I4s', len(stream), b'BIN\0') + stream
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    if not np.array_equal(p[indices].reshape(-1, 3, 3), positions[old_indices]):
        raise ValueError('Export changed source triangle geometry')
    if not np.array_equal(n[indices].reshape(-1, 3, 3), normals[old_indices]):
        raise ValueError('Export changed source triangle normals')
    return len(unique)


def transfer_quality(tri, old_uv, new_uv, source, rgb):
    target = np.ones(len(tri), bool)
    center = (tri.min(axis=(0, 1)) + tri.max(axis=(0, 1))) / 2
    extent = float(np.ptp(tri.reshape(-1, 3), axis=0).max())
    after = srgb_to_linear(rgb / 255.)
    result, total, count = {}, 0., 0
    for angle in [-140, -90, -65, -45, -25, 0, 25, 45, 65, 90, 115, 140, 180]:
        theta = math.radians(angle)
        eye = center + extent * 3.2 * np.array([math.sin(theta), 0, math.cos(theta)])
        K, R, t = look_at(center, eye, 512, 512 * 2.1)
        fg, source_coords = render_uv(tri, target, old_uv, K, R, t, 512)
        fg2, new_coords = render_uv(tri, target, new_uv, K, R, t, 512)
        if not np.array_equal(fg, fg2): raise ValueError('Transfer changed rendered silhouette')
        original, _ = render_map(source, fg, source_coords)
        transferred, _ = render_map(after, fg2, new_coords)
        row = stats(transferred, original, fg, int(fg.sum()))
        result[str(angle)] = row
        total += row['mae_srgb_255'] * row['pixels']; count += row['pixels']
    return {'scope': 'Corrected-source-orientation versus transferred unlit rendered color only. Source reference uses (u, 1-v); this is not a claim that the original baseline displayed correct colors, and is not independent photographic holdout.',
            'view_size': 512, 'views': result, 'weighted_mae_srgb_255': total / count,
            'silhouettes_identical': True, 'pixels': count}


def prepare(source_path, output_path, report_path, size=2048, padding=4):
    if source_path == output_path or source_path == report_path:
        raise ValueError('The source baseline must remain read-only')
    if sha(source_path) != SOURCE_SHA256:
        raise ValueError('This preparation script is pinned to the licensed public scan baseline')
    j, b = read_asset(source_path)
    if len(j['meshes']) != 1 or len(j['meshes'][0]['primitives']) != 1:
        raise ValueError('This public example preparation expects one static scan primitive')
    prim = j['meshes'][0]['primitives'][0]; attrs = prim['attributes']
    positions = np.asarray(accessor_data(j, b, attrs['POSITION']), np.float32)
    normals = np.asarray(accessor_data(j, b, attrs['NORMAL']), np.float32)
    old_uv = np.asarray(accessor_data(j, b, attrs['TEXCOORD_0']), np.float64)
    # Visual registration, not a numerical error score, revealed that the legacy
    # baseline's upright color image and bottom-origin V coordinates disagree.
    # Correct sampling in this derived diagnostic only; never mutate baseline UV.
    old_uv[:, 1] = 1 - old_uv[:, 1]
    indices = np.asarray(accessor_data(j, b, prim['indices']), np.uint32).reshape(-1, 3)
    source = texture(j, b, prim['material'])
    uv, atlas_report = clean_atlas(positions, normals, indices, size, padding)
    rgb, bake_report = bake_color(old_uv[indices], uv, source, size, padding)
    quality = transfer_quality(positions[indices], old_uv[indices], uv, source, rgb)
    if quality['weighted_mae_srgb_255'] > 3:
        raise ValueError('Color transfer mean error exceeds the explicit 3/255 engineering bound')
    vertices = write_glb(output_path, j, positions, normals, indices, uv, rgb)
    qa = validate(output_path, 'B1 scan color - repaired UV atlas', 'ccw', uv_only=True)
    if qa['status'] != 'PASS_UV_ONLY' or qa['errors']:
        raise ValueError(f'Exported GLB fails exact UV validation: {qa["errors"]}')
    report = {'schema_version': 1, 'status': 'PASS_UV_ONLY',
              'source_sha256': sha(source_path), 'output_sha256': sha(output_path),
              'source_asset': 'model/head.glb', 'output_asset': 'model/projection-head.glb',
              'source_license': 'Lee Perry-Smith / Infinite Realities, CC BY 3.0; LICENSE-head.txt',
              'scope': 'Separate unlit B1 diagnostic model with corrected source-image V registration and a new non-overlapping atlas. Source anatomy is unchanged; not a production head release. Baseline head.glb remains unchanged, including its legacy texture-registration defect.',
              'geometry': {'triangles': len(indices), 'vertices': vertices, 'positions_identical_per_triangle': True,
                           'normals_identical_per_triangle': True, 'triangle_order_identical': True,
                           'removed_triangles': 0, 'normal_map': 'Omitted intentionally from unlit diagnostic; retained on original baseline.'},
              'atlas': atlas_report, 'color_transfer': bake_report, 'transfer_quality': quality, 'uv_report': qa}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(output_path), 'sha256': report['output_sha256'], 'uv_status': qa['status'],
                      'triangles': len(indices), 'transfer_mae': quality['weighted_mae_srgb_255']}, indent=2))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    base = ROOT / 'assets/examples/photoreal-head'
    p.add_argument('--source', type=Path, default=base / 'model/head.glb')
    p.add_argument('--output', type=Path, default=base / 'model/projection-head.glb')
    p.add_argument('--report', type=Path, default=base / 'reports/atlas_preparation.json')
    p.add_argument('--size', type=int, default=2048)
    p.add_argument('--padding', type=int, default=4)
    a = p.parse_args()
    prepare(a.source.resolve(), a.output.resolve(), a.report.resolve(), a.size, a.padding)
