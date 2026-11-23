#!/usr/bin/env python3
"""Lightweight structural/size checks for LOW-POLY CHARACTER GLB files.

A strict Khronos glTF Validator and actual artist/pose/browser checks are still needed.
UVs and image textures are OPTIONAL for solid-color low-poly materials.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

HEADER=struct.Struct('<4sII')
CHUNK=struct.Struct('<I4s')
PROFILES={
    'icon': (1500, 2.0),
    'mobile': (5000, 5.0),
    'balanced': (12000, 12.0),
    'hero': (25000, 20.0),
}


def parse_glb(path: Path) -> tuple[dict, int]:
    raw=path.read_bytes()
    if len(raw)<HEADER.size:
        raise ValueError('File smaller than GLB header')
    magic,version,length=HEADER.unpack_from(raw)
    if magic!=b'glTF' or version!=2:
        raise ValueError('Expected GLB v2 magic/version')
    if length!=len(raw):
        raise ValueError(f'GLB header length {length} != actual {len(raw)}')
    offset=HEADER.size
    chunks=[]
    while offset<len(raw):
        if offset+CHUNK.size>len(raw):
            raise ValueError('Truncated GLB chunk header')
        size,kind=CHUNK.unpack_from(raw,offset)
        offset+=CHUNK.size
        if size%4!=0:
            raise ValueError('GLB chunk byteLength must be 4-byte aligned')
        if offset+size>len(raw):
            raise ValueError('GLB chunk exceeds declared size')
        chunks.append((kind,raw[offset:offset+size]))
        offset+=size
    if not chunks or chunks[0][0]!=b'JSON':
        raise ValueError('First GLB chunk must be JSON')
    gltf=json.loads(chunks[0][1].decode('utf-8').rstrip(' \x00\r\n\t'))
    if not isinstance(gltf,dict):
        raise ValueError('glTF JSON root must be an object')
    bin_size=sum(len(x) for kind,x in chunks[1:] if kind==b'BIN\0')
    return gltf,bin_size


def inspect(path: Path, profile='balanced', max_triangles=None, max_mb=None,
            require_skin=False, require_animations=False) -> dict:
    gltf,bin_bytes=parse_glb(path)
    errors=[]
    warnings=[]
    meshes=gltf.get('meshes',[])
    materials=gltf.get('materials',[])
    accessors=gltf.get('accessors',[])
    nodes=gltf.get('nodes',[])
    skins=gltf.get('skins',[])
    anim=gltf.get('animations',[])
    images=gltf.get('images',[])
    views=gltf.get('bufferViews',[])
    buffers=gltf.get('buffers',[])
    size_mb=path.stat().st_size/1048576

    target_tri,target_mb=PROFILES[profile]
    target_tri=target_tri if max_triangles is None else max_triangles
    target_mb=target_mb if max_mb is None else max_mb
    if target_tri<0 or target_mb<0:
        errors.append('Size/triangle budgets must be nonnegative')

    if gltf.get('asset',{}).get('version')!='2.0':
        errors.append('glTF asset.version must equal 2.0')
    if not buffers:
        errors.append('Missing glTF buffers')
    else:
        b0=buffers[0]
        if 'uri' in b0:
            errors.append('GLB main buffer has external/data URI; expected embedded BIN')
        if int(b0.get('byteLength',0))>bin_bytes:
            errors.append('Embedded BIN bytes shorter than buffer[0].byteLength')
    for i,buf in enumerate(buffers[1:],start=1):
        if 'uri' in buf and not str(buf['uri']).startswith('data:'):
            errors.append(f'External buffer[{i}] URI not self-contained in GLB')
    for i,view in enumerate(views):
        bi=view.get('buffer',0)
        if not isinstance(bi,int) or not 0<=bi<len(buffers):
            errors.append(f'bufferView[{i}] invalid buffer index')
            continue
        st=int(view.get('byteOffset',0))
        length=int(view.get('byteLength',0))
        if st<0 or length<0 or st+length>int(buffers[bi].get('byteLength',0)):
            errors.append(f'bufferView[{i}] out of declared buffer range')
    for i,acc in enumerate(accessors):
        if acc.get('count',0)<0:
            errors.append(f'accessor[{i}] negative count')
        if 'bufferView' in acc and (not isinstance(acc['bufferView'],int) or not 0<=acc['bufferView']<len(views)):
            errors.append(f'accessor[{i}] references invalid bufferView')

    def acc_count(value,tag):
        if not isinstance(value,int) or not 0<=value<len(accessors):
            errors.append(f'{tag} references invalid accessor {value!r}')
            return 0
        return int(accessors[value].get('count',0))

    triangle_by_mesh=[]
    primitives=0
    textured_primitives=0
    uv0_primitives=0
    for mi,mesh in enumerate(meshes):
        tri=0
        for pi,prim in enumerate(mesh.get('primitives',[])):
            tag=f'mesh[{mi}].primitive[{pi}]'
            primitives+=1
            attrs=prim.get('attributes',{})
            if 'POSITION' not in attrs:
                errors.append(f'{tag} missing POSITION')
                continue
            vertex_count=acc_count(attrs['POSITION'],tag+'.POSITION')
            if vertex_count==0:
                errors.append(f'{tag} has no vertices')
            if 'NORMAL' not in attrs:
                warnings.append(f'{tag} lacks vertex normals; faceted appearance may differ')
            if 'TEXCOORD_0' in attrs:
                uv0_primitives+=1
                if acc_count(attrs['TEXCOORD_0'],tag+'.TEXCOORD_0')!=vertex_count:
                    errors.append(f'{tag} UV0 count does not equal vertex count')
            if 'material' in prim:
                mindex=prim['material']
                if not isinstance(mindex,int) or not 0<=mindex<len(materials):
                    errors.append(f'{tag} invalid material reference')
                    material={}
                else:
                    material=materials[mindex]
            else:
                material={}
            mapped_textures=[]
            pbr=material.get('pbrMetallicRoughness',{})
            for key in ('baseColorTexture','metallicRoughnessTexture'):
                if isinstance(pbr.get(key),dict):
                    mapped_textures.append(pbr[key])
            for key in ('normalTexture','occlusionTexture','emissiveTexture'):
                if isinstance(material.get(key),dict):
                    mapped_textures.append(material[key])
            if mapped_textures:
                textured_primitives+=1
                for tinfo in mapped_textures:
                    coord='TEXCOORD_'+str(tinfo.get('texCoord',0))
                    if coord not in attrs:
                        errors.append(f'{tag} material uses {coord} but mesh has none')
                    elif acc_count(attrs[coord],tag+'.'+coord)!=vertex_count:
                        errors.append(f'{tag} {coord} count != POSITION count')
            if prim.get('mode',4)!=4:
                warnings.append(f'{tag} primitive is not TRIANGLES; excluded from triangle total')
            else:
                num=acc_count(prim['indices'],tag+'.indices') if 'indices' in prim else vertex_count
                if num%3:
                    errors.append(f'{tag} index/vertex count not divisible by 3')
                tri+=num//3
        triangle_by_mesh.append(tri)

    if not meshes or not primitives:
        errors.append('No character mesh primitives found')
    for i,image in enumerate(images):
        uri=image.get('uri')
        if uri and not str(uri).startswith('data:'):
            errors.append(f'image[{i}] references external URI')
        if 'bufferView' in image and (not isinstance(image['bufferView'],int) or not 0<=image['bufferView']<len(views)):
            errors.append(f'image[{i}] invalid bufferView')
        if not uri and 'bufferView' not in image:
            errors.append(f'image[{i}] has no bytes reference')

    mesh_ref_count=[0]*len(meshes)
    skinned_meshes=[]
    for ni,node in enumerate(nodes):
        mi=node.get('mesh')
        if mi is not None:
            if not isinstance(mi,int) or not 0<=mi<len(meshes):
                errors.append(f'node[{ni}] invalid mesh index')
            else:
                mesh_ref_count[mi]+=1
        if 'skin' in node:
            si=node['skin']
            if not isinstance(si,int) or not 0<=si<len(skins):
                errors.append(f'node[{ni}] invalid skin index')
            if mi is None or not isinstance(mi,int) or not 0<=mi<len(meshes):
                errors.append(f'node[{ni}] has skin but no valid mesh')
            else:
                skinned_meshes.append(mi)
                for pi,prim in enumerate(meshes[mi].get('primitives',[])):
                    attrs=prim.get('attributes',{})
                    label=f'node[{ni}].mesh[{mi}].primitive[{pi}]'
                    for key in ('JOINTS_0','WEIGHTS_0'):
                        if key not in attrs:
                            errors.append(f'{label} skinned primitive missing {key}')
                        elif 'POSITION' in attrs and acc_count(attrs[key],label+'.'+key)!=acc_count(attrs['POSITION'],label+'.POSITION'):
                            errors.append(f'{label} {key} count differs from POSITION count')
    for i,skin in enumerate(skins):
        joints=skin.get('joints',[])
        if not joints:
            errors.append(f'skin[{i}] missing joints')
        for j in joints:
            if not isinstance(j,int) or not 0<=j<len(nodes):
                errors.append(f'skin[{i}] refers to invalid joint node')
        if 'inverseBindMatrices' in skin and acc_count(skin['inverseBindMatrices'],f'skin[{i}].inverseBindMatrices') < len(joints):
            errors.append(f'skin[{i}] inverseBindMatrices count less than joints')
    if require_skin and not skinned_meshes:
        errors.append('Rig requested but GLB has no skinned mesh nodes')
    if require_animations and not any(a.get('channels') for a in anim):
        errors.append('Animations requested but GLB contains no animation channels')
    for i,a in enumerate(anim):
        if not a.get('channels'):
            warnings.append(f'animation[{i}] has no channels')
    for mi,c in enumerate(mesh_ref_count):
        if c==0:
            warnings.append(f'mesh[{mi}] is unreferenced by scene nodes')
    triangles_unique=sum(triangle_by_mesh)
    triangles_instances=sum(triangle_by_mesh[mi]*c for mi,c in enumerate(mesh_ref_count))
    if triangles_instances>target_tri:
        errors.append(f'Triangle budget exceeded: instantiated {triangles_instances} > {target_tri}')
    if size_mb>target_mb:
        errors.append(f'GLB byte budget exceeded: {size_mb:.3f} MB > {target_mb} MB')
    if skins and not skinned_meshes:
        warnings.append('Skins declared but none bound to a mesh node')
    if len(meshes)>20:
        warnings.append('High mesh-part count for a lightweight character; review draw calls on target hardware')

    return {
        'file':str(path), 'profile':profile, 'size_mb':round(size_mb,4),
        'budget_max_triangles':target_tri, 'budget_max_mb':target_mb,
        'mesh_count':len(meshes), 'primitive_count':primitives,
        'node_count':len(nodes), 'triangles_unique':triangles_unique,
        'triangles_instantiated':triangles_instances,
        'materials':len(materials), 'images':len(images),
        'textured_primitives':textured_primitives,
        'uv0_primitives':uv0_primitives,
        'skins':len(skins), 'skinned_mesh_nodes':len(skinned_meshes),
        'animations':len(anim), 'animation_clip_names':[a.get('name','') for a in anim],
        'extensions_required':gltf.get('extensionsRequired',[]),
        'status':'PASS' if not errors else 'FAIL',
        'errors':errors, 'warnings':warnings,
        'validation_scope':'Structural/metadata checks only. Not an official glTF Validator, visual anatomy check, rig pose test or browser verification.'
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('glb',type=Path)
    ap.add_argument('--profile',choices=sorted(PROFILES),default='balanced')
    ap.add_argument('--max-triangles',type=int)
    ap.add_argument('--max-mb',type=float)
    ap.add_argument('--require-skin',action='store_true')
    ap.add_argument('--require-animations',action='store_true')
    ap.add_argument('--strict-warnings',action='store_true')
    ap.add_argument('--json',type=Path)
    args=ap.parse_args()
    try:
        result=inspect(args.glb,args.profile,args.max_triangles,args.max_mb,
                       args.require_skin,args.require_animations)
    except (OSError,ValueError,TypeError,json.JSONDecodeError,struct.error) as exc:
        result={'file':str(args.glb),'status':'FAIL','errors':[str(exc)],'warnings':[]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 1 if result['status']=='FAIL' or args.strict_warnings and result['warnings'] else 0


if __name__=='__main__':
    sys.exit(main())
