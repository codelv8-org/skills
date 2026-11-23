#!/usr/bin/env python3
"""Render UV0 triangle wireframe from an uncompressed glTF 2.0 GLB to a PNG.

Requires Pillow. This is a layout preview, NOT a UV overlap/stretch validator.
Draco/Meshopt-compressed geometry must first be decoded using compatible tools.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

from PIL import Image, ImageDraw

SIZES = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_asset(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if len(raw) < 12 or raw[:4] != b'glTF' or struct.unpack_from('<I', raw, 4)[0] != 2:
        raise ValueError('Expected glTF 2.0 binary GLB')
    if struct.unpack_from('<I', raw, 8)[0] != len(raw):
        raise ValueError('Corrupt GLB header length')
    offset = 12
    chunks = []
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError('Malformed chunk header')
        size, kind = struct.unpack_from('<I4s', raw, offset)
        offset += 8
        if offset + size > len(raw):
            raise ValueError('Malformed chunk payload')
        chunks.append((kind, raw[offset:offset + size]))
        offset += size
    if not chunks or chunks[0][0] != b'JSON':
        raise ValueError('Missing JSON chunk')
    gltf = json.loads(chunks[0][1].decode('utf-8').rstrip(' \r\n\t\0'))
    buffer = next((payload for kind, payload in chunks if kind == b'BIN\0'), None)
    if buffer is None:
        raise ValueError('No embedded buffer; GLB geometry is inaccessible')
    return gltf, buffer


def accessor_data(gltf: dict, binary: bytes, index: int) -> list[tuple]:
    acc = gltf['accessors'][index]
    if 'sparse' in acc or 'bufferView' not in acc:
        raise ValueError('Sparse/accessor without bufferView is unsupported; decode or expand it first')
    bv = gltf['bufferViews'][acc['bufferView']]
    if 'EXT_meshopt_compression' in bv.get('extensions', {}):
        raise ValueError('Meshopt-compressed bufferView; decode before UV render')
    if bv.get('buffer', 0) != 0:
        raise ValueError('Only embedded GLB binary buffer 0 is supported')
    comp_format, width = SIZES[acc['componentType']]
    count = int(acc['count'])
    dim = COMPONENTS[acc['type']]
    stride = int(bv.get('byteStride', width * dim))
    start = int(bv.get('byteOffset', 0)) + int(acc.get('byteOffset', 0))
    fmt = '<' + comp_format * dim
    items = []
    for i in range(count):
        v = struct.unpack_from(fmt, binary, start + i * stride)
        if acc.get('normalized', False) and acc['componentType'] in (5120, 5121, 5122, 5123):
            signed = acc['componentType'] in (5120, 5122)
            denom = (2 ** (8 * width - 1) - 1) if signed else (2 ** (8 * width) - 1)
            v = tuple(max(-1.0, x / denom) if signed else x / denom for x in v)
        items.append(v)
    return items


def render(path: Path, output: Path, size: int, transparent: bool) -> dict:
    gltf, binary = read_asset(path)
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0) if transparent else (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)
    if not transparent:
        for i in range(1, 16):
            x = round(i * (size - 1) / 16)
            draw.line([(x, 0), (x, size - 1)], fill=(233, 235, 240, 255))
            draw.line([(0, x), (size - 1, x)], fill=(233, 235, 240, 255))
    tris = 0
    skipped = 0
    for mesh in gltf.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            if primitive.get('mode', 4) != 4 or 'TEXCOORD_0' not in primitive.get('attributes', {}):
                skipped += 1
                continue
            if primitive.get('extensions', {}).get('KHR_draco_mesh_compression'):
                raise ValueError('KHR_draco_mesh_compression detected; decode geometry before UV render')
            uv = accessor_data(gltf, binary, primitive['attributes']['TEXCOORD_0'])
            indices = (accessor_data(gltf, binary, primitive['indices']) if 'indices' in primitive
                       else [(i,) for i in range(len(uv))])
            flat_indices = [int(value[0]) for value in indices]
            if len(flat_indices) % 3:
                raise ValueError('Primitive index count is not a triangle multiple')
            for start in range(0, len(flat_indices), 3):
                tri = []
                for idx in flat_indices[start:start + 3]:
                    if idx < 0 or idx >= len(uv):
                        raise ValueError('UV index out of range')
                    u, v = uv[idx][:2]
                    tri.append((round(float(u) * (size - 1)), round((1 - float(v)) * (size - 1))))
                draw.line([*tri, tri[0]], fill=(25, 56, 83, 220), width=1)
                tris += 1
    if not tris:
        raise ValueError('No uncompressed UV0 triangles to draw')
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output)
    return {'source': str(path), 'output': str(output), 'image_size': size,
            'triangles_drawn': tris, 'primitives_skipped': skipped,
            'warning': 'UV line preview only; overlap, stretching, and texel density need manual review'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--size', type=int, choices=(512, 1024, 2048, 4096), default=2048)
    parser.add_argument('--transparent', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(render(args.glb, args.out, args.size, args.transparent), indent=2))
        return 0
    except (OSError, ValueError, KeyError, IndexError, struct.error) as exc:
        print(f'UV layout failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
