"""Inspect GLB 2.0 declared geometry/rig/material metadata; not full glTF validation."""
import argparse
import json
import struct
from pathlib import Path


def inspect(path, require_rig=False, max_triangles=None):
    path = Path(path)
    with path.open('rb') as f:
        head = f.read(12)
        if len(head) != 12:
            raise ValueError('truncated GLB header')
        magic, version, size = struct.unpack('<4sII', head)
        if magic != b'glTF' or version != 2 or size != path.stat().st_size:
            raise ValueError('invalid GLB 2.0 header/length')
        raw = f.read(8)
        if len(raw) != 8:
            raise ValueError('missing JSON chunk')
        length, typ = struct.unpack('<II', raw)
        if typ != 0x4E4F534A or length % 4 or length > min(size-20, 32*1024*1024):
            raise ValueError('invalid GLB JSON chunk')
        doc = json.loads(f.read(length).decode('utf-8'))
        while f.tell() < size:
            raw = f.read(8)
            if len(raw) != 8:
                raise ValueError('truncated chunk header')
            length, typ = struct.unpack('<II', raw)
            if length % 4 or length > size-f.tell():
                raise ValueError('invalid chunk size')
            f.seek(length, 1)
    if doc.get('asset', {}).get('version') != '2.0':
        raise ValueError('asset version not 2.0')
    accessors, meshes, nodes, skins = (doc.get(k, []) for k in ('accessors', 'meshes', 'nodes', 'skins'))
    def get(xs, i):
        if type(i) is not int or not 0 <= i < len(xs):
            raise ValueError('bad metadata index')
        return xs[i]
    def count(i):
        n = get(accessors, i)['count']
        if type(n) is not int or n <= 0:
            raise ValueError('invalid accessor count')
        return n
    totals, warnings = [], []
    skin_meshes = set()
    for i, mesh in enumerate(meshes):
        triangles = 0
        for primitive in mesh.get('primitives', []):
            attr = primitive.get('attributes', {})
            n = count(primitive['indices'] if 'indices' in primitive else attr['POSITION'])
            vertices = count(attr['POSITION'])
            mode = primitive.get('mode', 4)
            if mode == 4:
                if n % 3:
                    raise ValueError('TRIANGLES count not divisible by three')
                triangles += n//3
            elif mode in (5, 6):
                triangles += max(0, n-2)
            else:
                warnings.append(f'mesh {i}: non-triangle primitive mode {mode}')
            if 'NORMAL' not in attr or 'TEXCOORD_0' not in attr:
                warnings.append(f'mesh {i}: missing normal or UV0')
            if 'JOINTS_0' in attr and 'WEIGHTS_0' in attr:
                if count(attr['JOINTS_0']) != vertices or count(attr['WEIGHTS_0']) != vertices:
                    raise ValueError('skin accessor count mismatch')
                skin_meshes.add(i)
        totals.append(triangles)
    instanced, rigged_nodes = 0, 0
    for node in nodes:
        if 'mesh' in node:
            i = node['mesh']
            instanced += get(totals, i)
            if 'skin' in node:
                skin = get(skins, node['skin'])
                if i not in skin_meshes or not skin.get('joints'):
                    raise ValueError('skinned node lacks weights/joints')
                for j in skin['joints']:
                    get(nodes, j)
                for primitive in get(meshes, i).get('primitives', []):
                    if not {'JOINTS_0', 'WEIGHTS_0'}.issubset(primitive.get('attributes', {})):
                        raise ValueError('skinned primitive lacks weights/joints')
                rigged_nodes += 1
    total = sum(totals)
    if total <= 0:
        raise ValueError('no declared triangle geometry')
    if require_rig and not rigged_nodes:
        raise ValueError('no declared skinned mesh node')
    if max_triangles is not None and max(total, instanced) > max_triangles:
        raise ValueError('declared triangle budget exceeded')
    return {'status':'METADATA_DIAGNOSTIC_ONLY','bytes':size,'unique_mesh_triangles':total,'all_node_triangles':instanced,'meshes':len(meshes),'materials':len(doc.get('materials', [])),'images':len(doc.get('images', [])),'skins':len(skins),'rigged_nodes':rigged_nodes,'animations':[a.get('name',f'animation_{i}') for i,a in enumerate(doc.get('animations', []))],'warnings':warnings,'limitations':'Does not decode geometry, verify weights, validate buffers, measure draw calls/FPS, or test engine appearance.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path)
    parser.add_argument('--require-rig',action='store_true')
    parser.add_argument('--max-triangles',type=int)
    a=parser.parse_args()
    try:
        print(json.dumps(inspect(a.glb,a.require_rig,a.max_triangles),indent=2))
    except (ValueError, OSError, TypeError, KeyError, AttributeError, struct.error) as e:
        print(f'BLOCKED: {e}')
        return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
