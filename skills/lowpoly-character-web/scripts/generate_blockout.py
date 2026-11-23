#!/usr/bin/env python3
"""Create a real, static, original faceted humanoid blockout in GLB format.

This script makes editable geometric STARTER mesh parts for later Blender refinement.
It does not create a skeleton, skin weights, UV atlas, or animation clips.

Usage:
  python -m pip install trimesh numpy
  python scripts/generate_blockout.py --spec assets/templates/character_spec.json \
      --out export/character_blockout.glb --manifest reports/blockout.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    import numpy as np
    import trimesh
except ImportError as exc:
    raise SystemExit("Install required packages: python -m pip install trimesh numpy") from exc


def rgb(hex_code: str) -> tuple[int, int, int, int]:
    value = hex_code.strip().lstrip('#')
    if len(value) != 6 or any(ch not in '0123456789abcdefABCDEF' for ch in value):
        raise ValueError(f"Invalid RGB hex color: {hex_code!r}")
    return tuple(int(value[n:n+2], 16) for n in (0, 2, 4)) + (255,)


def make_material(name: str, color: str):
    return trimesh.visual.material.PBRMaterial(
        name=name, baseColorFactor=rgb(color), metallicFactor=0.0, roughnessFactor=0.86
    )


def faceted(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Duplicate vertices per face so glTF export preserves hard/faceted normals."""
    verts = np.asarray(mesh.vertices)[np.asarray(mesh.faces)].reshape(-1, 3)
    faces = np.arange(len(verts), dtype=np.int64).reshape(-1, 3)
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def ellipsoid(center, extents, subdivisions=1):
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=1.0)
    mesh.apply_scale(extents)
    mesh.apply_translation(center)
    return faceted(mesh)


def box(center, extents):
    mesh = trimesh.creation.box(extents=extents)
    mesh.apply_translation(center)
    return faceted(mesh)


def tube(a, b, radius_a: float, radius_b: float, segments=8):
    """Closed tapered polygonal tube between points; not weight-painted."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    direction = b - a
    distance = np.linalg.norm(direction)
    if distance <= 1e-9:
        raise ValueError("Tube has zero length")
    axis = direction / distance
    guide = np.array([0.0, 1.0, 0.0]) if abs(axis[1]) < 0.95 else np.array([1.0, 0.0, 0.0])
    u = np.cross(axis, guide)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    circle = [math.cos(2 * math.pi * i / segments) * u + math.sin(2 * math.pi * i / segments) * v
              for i in range(segments)]
    verts = [a + radius_a * q for q in circle] + [b + radius_b * q for q in circle]
    verts += [a, b]
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.extend([(i, j, segments + i), (j, segments + j, segments + i)])
        faces.append((2 * segments, j, i))
        faces.append((2 * segments + 1, segments + i, segments + j))
    mesh = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=False)
    return faceted(mesh)


def torso(z0=0.89, z1=1.39, shoulder_scale=1.0):
    """Eight-corner rings for a waist / chest / neck block, faceted and symmetric."""
    def ring(z, width, depth):
        w, d = width / 2, depth / 2
        return [(-w, -d*.6, z), (-w*.72, -d, z), (w*.72, -d, z), (w, -d*.6, z),
                (w, d*.6, z), (w*.72, d, z), (-w*.72, d, z), (-w, d*.6, z)]
    rings = [ring(z0, .33, .22), ring(1.18, .42 * shoulder_scale, .24),
             ring(z1, .48 * shoulder_scale, .22)]
    verts = np.array(sum(rings, []), dtype=float)
    verts = np.concatenate([verts, np.array([[0, 0, z0], [0, 0, z1]], dtype=float)])
    faces = []
    for r in (0, 1):
        for i in range(8):
            j = (i + 1) % 8
            k = r * 8
            faces.extend([(k+i, k+j, k+8+i), (k+j, k+8+j, k+8+i)])
    for i in range(8):
        j = (i + 1) % 8
        faces.extend([(24, j, i), (25, 16+i, 16+j)])
    return faceted(trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False))


def hair_dome():
    """Dome ending above eyebrows; open base is an intentional hair shell over head."""
    slices, rings = 12, 3
    verts = []
    center_z, radius_z = 1.665, .116
    for k in range(rings):
        phi = (0.5 * math.pi) * (k / (rings - 1))
        for i in range(slices):
            ang = 2 * math.pi * i / slices
            verts.append((.184 * math.sin(phi) * math.cos(ang),
                          -.006 + .150 * math.sin(phi) * math.sin(ang),
                          center_z + radius_z * math.cos(phi)))
    faces = []
    for k in range(rings - 1):
        for i in range(slices):
            j = (i+1) % slices
            b = k * slices
            faces.extend([(b+i, b+slices+i, b+j), (b+j, b+slices+i, b+slices+j)])
    return faceted(trimesh.Trimesh(vertices=verts, faces=faces, process=False))


def build(spec: dict) -> tuple[trimesh.Scene, dict]:
    if spec.get('kind', 'human') != 'human':
        raise ValueError("This static generator supports kind='human' only; the skill's manual pipeline supports other species")
    if spec.get('rig', 'none') != 'none':
        raise ValueError("Blockout generator is static only. Set rig='none'; build a real rig in Blender separately")
    if spec.get('style', 'faceted-hero') != 'faceted-hero':
        raise ValueError("Starter currently implements only style='faceted-hero'; use Blender for other style profiles")
    if spec.get('pose', 'A-pose') != 'A-pose':
        raise ValueError("Starter currently implements only pose='A-pose'; change pose using a real rig/modeling tool")
    name = str(spec.get('name', 'original-lowpoly-character'))
    height = float(spec.get('height_meters', 1.70))
    head_scale = float(spec.get('head_scale', 1.0))
    shoulder_scale = float(spec.get('shoulder_scale', 1.0))
    if not (0.5 <= height <= 3.0 and 0.70 <= head_scale <= 1.55 and 0.7 <= shoulder_scale <= 1.5):
        raise ValueError('height_meters/head_scale/shoulder_scale out of starter supported ranges')
    colors = dict(spec.get('palette', {}))
    defaults = dict(skin='#D8AA83', hair='#35282E', shirt='#397C83', pants='#344858',
                    boots='#2B2F36', eyes='#262128', accent='#E0A346')
    defaults.update(colors)
    mats = {key: make_material(key, col) for key, col in defaults.items()}
    scene = trimesh.Scene()
    components = []

    def add(part: str, mesh: trimesh.Trimesh, color: str):
        if color not in mats:
            raise ValueError(f'Unknown palette key: {color}')
        mesh.visual = trimesh.visual.TextureVisuals(material=mats[color])
        scene.add_geometry(mesh, geom_name=part, node_name=part)
        components.append({'part': part, 'material': color, 'triangles': int(len(mesh.faces))})

    add('BODY_Torso', torso(shoulder_scale=shoulder_scale), 'shirt')
    add('BODY_Pelvis', box((0, 0, .893), (.32, .235, .16)), 'pants')
    add('BODY_Neck', tube((0,0,1.35),(0,0,1.46),.066,.064,8), 'skin')

    for side, s in [('L', 1), ('R', -1)]:
        hip=(s*.105,0,.88); knee=(s*.119,-.016,.48); ankle=(s*.116,0,.122)
        add(f'LEG_{side}_Thigh',tube(hip,knee,.103,.081,8),'pants')
        add(f'LEG_{side}_Calf',tube(knee,ankle,.078,.056,8),'pants')
        add(f'LEG_{side}_Shoe',box((s*.116,-.063,.072),(.154,.277,.14)),'boots')
        shoulder=(s*.245*shoulder_scale,0,1.325)
        elbow=(s*.316*shoulder_scale,0,1.065)
        cuff=(s*.335*shoulder_scale,0,1.015)
        wrist=(s*.401*shoulder_scale,-.018,.780)
        add(f'ARM_{side}_Upper',tube(shoulder,cuff,.085,.074,8),'shirt')
        add(f'ARM_{side}_Forearm',tube(cuff,wrist,.060,.044,7),'skin')
        add(f'ARM_{side}_Hand',ellipsoid((s*.413*shoulder_scale,-.024,.713),(.055,.040,.087),1),'skin')

    # For head_scale > 1, shift head upward to maintain neck-to-chin clearance.
    head_center=np.array([0, 0, 1.590 + (head_scale-1)*.09])
    def on_head(point):
        return tuple(head_center + (np.array(point)-np.array([0,0,1.590])) * head_scale)
    add('HEAD_Cranium', ellipsoid(on_head((0,0,1.59)), (.173*head_scale,.146*head_scale,.184*head_scale),2),'skin')
    add('HEAD_Nose', ellipsoid(on_head((0,-.153,1.553)),(.032*head_scale,.032*head_scale,.039*head_scale),1),'skin')
    add('HEAD_Mouth', box(on_head((0,-.146,1.494)),(.061*head_scale,.009*head_scale,.008*head_scale)),'eyes')
    for side, s in [('L',1),('R',-1)]:
        add(f'HEAD_Ear_{side}',ellipsoid(on_head((s*.170,-.004,1.560)),(.042*head_scale,.043*head_scale,.077*head_scale),1),'skin')
        add(f'HEAD_Eye_{side}',ellipsoid(on_head((s*.060,-.144,1.610)),(.023*head_scale,.012*head_scale,.019*head_scale),1),'eyes')
        add(f'HEAD_Brow_{side}',box(on_head((s*.061,-.149,1.646)),(.055*head_scale,.013*head_scale,.012*head_scale)),'hair')
    cap=hair_dome()
    cap.vertices=np.asarray([on_head(p) for p in cap.vertices])
    add('HEAD_HairCap',cap,'hair')
    add('HEAD_RearHairVolume', ellipsoid(on_head((0,.078,1.591)),
        (.164*head_scale,.083*head_scale,.145*head_scale),1), 'hair')

    if spec.get('accessories', {}).get('backpack', False):
        add('GEAR_Backpack',box((0,.151,1.075),(.33,.160,.360)),'accent')
        for side,s in [('L',1),('R',-1)]:
            add(f'GEAR_Strap_{side}',box((s*.128,-.129,1.219),(.039,.026,.224)),'accent')

    # Scale height and align sole precisely to 0 at floor; source geometry has no rig.
    bounds=scene.bounds.copy()
    actual_h=float(bounds[1,2]-bounds[0,2])
    scale=height / actual_h
    transform=np.eye(4)
    transform[:3,:3]*=scale
    transform[2,3]=-bounds[0,2]*scale
    # glTF 2.0 is Y-up. Convert our authoring Z-up / -Y forward to glTF Y-up / +Z forward.
    axis_to_gltf=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],dtype=float)
    for node in scene.graph.nodes_geometry:
        transform_existing, geometry_name = scene.graph[node]
        scene.graph.update(frame_to=node, matrix=axis_to_gltf @ transform @ transform_existing, geometry=geometry_name)

    return scene, {
        'name':name, 'source':'procedural-static-starter', 'stage':'BLOCKOUT_ONLY',
        'style':'faceted-hero', 'pose':'A-pose',
        'rig':'none', 'animation_clips':[], 'has_uv0':False,
        'height_meters':height, 'head_scale':head_scale,
        'glb_axes':'Y-up, +Z character forward (Blender-like authoring was Z-up, -Y forward)',
        'triangles':int(sum(item['triangles'] for item in components)),
        'components':components, 'geometry_count':len(components),
        'limitations':[
            'Not a skinned/rigged or animated model',
            'Disconnected starter meshes and intentional open hair shell need artist topology review',
            'Needs actual front/profile/back visual review and production refinement in Blender',
            'No UV atlas; uses PBR solid color factors, so UV0 is not required',
            'Browser loading and performance have not been tested by this generator'
        ]
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True,help='JSON character specification')
    parser.add_argument('--out',type=Path,required=True,help='Destination .glb')
    parser.add_argument('--manifest',type=Path,help='Output manifest JSON')
    args=parser.parse_args()
    try:
        spec=json.loads(args.spec.read_text(encoding='utf-8'))
        scene, manifest=build(spec)
        args.out.parent.mkdir(parents=True,exist_ok=True)
        data=scene.export(file_type='glb', include_normals=True)
        if not isinstance(data,bytes) or data[:4]!=b'glTF':
            raise RuntimeError('The exporter did not produce a binary glTF')
        args.out.write_bytes(data)
        manifest['file']=str(args.out)
        manifest['size_bytes']=len(data)
        if args.manifest:
            args.manifest.parent.mkdir(parents=True,exist_ok=True)
            args.manifest.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(manifest,indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        parser.exit(1,f'ERROR: {exc}\n')


if __name__=='__main__':
    raise SystemExit(main())
