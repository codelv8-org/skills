#!/usr/bin/env python3
"""Inspect a glTF 2.0 binary (.glb) for head-asset delivery prerequisites.

Pure standard-library structural QA; cannot detect visual likeness, UV overlaps,
physically incorrect color values, or runtime rendering differences.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

GLB_HEADER = struct.Struct('<4sII')
CHUNK_HEADER = struct.Struct('<I4s')


def parse_glb(path: Path) -> tuple[dict, int]:
    raw = path.read_bytes()
    if len(raw) < GLB_HEADER.size:
        raise ValueError('File shorter than GLB header')
    magic, version, declared_length = GLB_HEADER.unpack_from(raw)
    if magic != b'glTF':
        raise ValueError('Not a GLB (missing glTF magic)')
    if version != 2:
        raise ValueError(f'Unsupported GLB version: {version}')
    if declared_length != len(raw):
        raise ValueError(f'GLB length mismatch: header={declared_length}, actual={len(raw)}')
    offset = GLB_HEADER.size
    chunks = []
    while offset < len(raw):
        if offset + CHUNK_HEADER.size > len(raw):
            raise ValueError('Incomplete GLB chunk header')
        size, kind = CHUNK_HEADER.unpack_from(raw, offset)
        offset += CHUNK_HEADER.size
        if offset + size > len(raw):
            raise ValueError('Chunk extends beyond GLB length')
        chunks.append((kind, raw[offset:offset + size]))
        offset += size
    if not chunks or chunks[0][0] != b'JSON':
        raise ValueError('First GLB chunk must be JSON')
    gltf = json.loads(chunks[0][1].decode('utf-8').rstrip(' \t\r\n\0'))
    bin_bytes = next((len(payload) for kind, payload in chunks[1:] if kind == b'BIN\0'), 0)
    return gltf, bin_bytes


def inspect(path: Path, max_tris: int | None, max_mb: float | None, require_normal: bool) -> dict:
    gltf, bin_size = parse_glb(path)
    errors: list[str] = []
    warnings: list[str] = []
    size_mb = path.stat().st_size / (1024 * 1024)

    asset = gltf.get('asset', {})
    if asset.get('version') != '2.0':
        errors.append('glTF asset.version must be 2.0')
    buffers = gltf.get('buffers', [])
    if buffers and not buffers[0].get('uri') and int(buffers[0].get('byteLength', 0)) > bin_size:
        errors.append('Embedded BIN chunk shorter than declared buffer length')

    views = gltf.get('bufferViews', [])
    for i, view in enumerate(views):
        bi = view.get('buffer', 0)
        if not isinstance(bi, int) or bi < 0 or bi >= len(buffers):
            errors.append(f'bufferView[{i}] references nonexistent buffer')
            continue
        start = int(view.get('byteOffset', 0))
        length = int(view.get('byteLength', 0))
        if start < 0 or length < 0 or start + length > int(buffers[bi].get('byteLength', 0)):
            errors.append(f'bufferView[{i}] out of range')

    meshes = gltf.get('meshes', [])
    accessors = gltf.get('accessors', [])
    materials = gltf.get('materials', [])
    images = gltf.get('images', [])
    textures = gltf.get('textures', [])
    triangle_count = 0
    primitive_count = 0
    uv_primitive_count = 0

    def count_accessor(index: object, label: str) -> int:
        if not isinstance(index, int) or index < 0 or index >= len(accessors):
            errors.append(f'{label}: invalid accessor index {index!r}')
            return 0
        return int(accessors[index].get('count', 0))

    for mi, mesh in enumerate(meshes):
        for pi, primitive in enumerate(mesh.get('primitives', [])):
            primitive_count += 1
            tag = f'mesh[{mi}].primitive[{pi}]'
            attrs = primitive.get('attributes', {})
            if 'POSITION' not in attrs:
                errors.append(f'{tag}: missing POSITION')
                continue
            vertex_count = count_accessor(attrs['POSITION'], f'{tag}.POSITION')
            if vertex_count <= 0:
                errors.append(f'{tag}: empty POSITION accessor')
            if 'TEXCOORD_0' not in attrs:
                errors.append(f'{tag}: missing UV0/TEXCOORD_0')
            else:
                uv_primitive_count += 1
                uv_count = count_accessor(attrs['TEXCOORD_0'], f'{tag}.TEXCOORD_0')
                if uv_count != vertex_count:
                    errors.append(f'{tag}: UV0 count {uv_count} differs from POSITION count {vertex_count}')
            if 'NORMAL' not in attrs:
                warnings.append(f'{tag}: missing vertex NORMAL; appearance may be faceted')
            if primitive.get('mode', 4) != 4:
                warnings.append(f'{tag}: primitive is not TRIANGLES mode')
            else:
                count = count_accessor(primitive['indices'], f'{tag}.indices') if 'indices' in primitive else vertex_count
                if count % 3:
                    warnings.append(f'{tag}: triangle index/vertex count not divisible by 3')
                triangle_count += count // 3
            if 'material' in primitive:
                mat = primitive['material']
                if not isinstance(mat, int) or mat < 0 or mat >= len(materials):
                    errors.append(f'{tag}: invalid material index')
            else:
                warnings.append(f'{tag}: material not explicitly assigned')

    if not meshes or primitive_count == 0:
        errors.append('No mesh primitives found')
    if not materials:
        warnings.append('No PBR materials found')
    if not images:
        warnings.append('No texture images found')

    normal_maps = sum(1 for m in materials if isinstance(m.get('normalTexture'), dict))
    albedo_maps = sum(
        1 for m in materials
        if isinstance(m.get('pbrMetallicRoughness', {}).get('baseColorTexture'), dict)
    )
    if not albedo_maps:
        warnings.append('No image-backed BaseColor texture found')
    if not normal_maps:
        (errors if require_normal else warnings).append('No tangent-space normal texture found')

    for i, image in enumerate(images):
        uri = image.get('uri')
        if uri and not uri.startswith('data:'):
            errors.append(f'image[{i}]: GLB references external image URI {uri!r}')
        elif 'bufferView' in image and (not isinstance(image['bufferView'], int) or not 0 <= image['bufferView'] < len(views)):
            errors.append(f'image[{i}]: invalid bufferView')
        elif 'bufferView' not in image and not uri:
            warnings.append(f'image[{i}]: no embedded bytes or URI')

    if max_tris is not None and triangle_count > max_tris:
        errors.append(f'Triangle budget exceeded: {triangle_count} > {max_tris}')
    if max_mb is not None and size_mb > max_mb:
        errors.append(f'GLB size budget exceeded: {size_mb:.2f} MB > {max_mb:.2f} MB')

    return {
        'file': str(path), 'size_mb': round(size_mb, 3),
        'asset_version': asset.get('version'), 'mesh_count': len(meshes),
        'primitive_count': primitive_count, 'triangles': triangle_count,
        'uv0_primitives': uv_primitive_count, 'materials': len(materials),
        'textures': len(textures), 'images': len(images),
        'basecolor_maps': albedo_maps, 'normal_maps': normal_maps,
        'extensions_required': gltf.get('extensionsRequired', []),
        'status': 'PASS' if not errors else 'FAIL',
        'errors': errors, 'warnings': warnings,
        'scope': 'structural validation only; visual UV/texture/browser QA still required',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--max-triangles', type=int)
    parser.add_argument('--max-mb', type=float)
    parser.add_argument('--require-normal-map', action='store_true')
    parser.add_argument('--strict-warnings', action='store_true')
    parser.add_argument('--json', type=Path, help='Write JSON report here')
    args = parser.parse_args()
    try:
        result = inspect(args.glb, args.max_triangles, args.max_mb, args.require_normal_map)
    except (OSError, ValueError, json.JSONDecodeError, struct.error) as exc:
        result = {'file': str(args.glb), 'status': 'FAIL', 'errors': [str(exc)], 'warnings': []}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return 1 if result['status'] == 'FAIL' or (args.strict_warnings and result['warnings']) else 0


if __name__ == '__main__':
    sys.exit(main())
