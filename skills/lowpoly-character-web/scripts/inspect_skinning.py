#!/usr/bin/env python3
"""Deep glTF skinned-character audit; complements (does not replace) glTF Validator.

Checks real JOINTS_0/WEIGHTS_0 data, inverse-bind matrices, skin nodes, clip
samplers and named animation clips. Connectivity can only be checked per indexed
primitive; UV/material seams can split vertices while the skin is visually smooth.
Artistic joint deformation still requires bent-pose screenshots and artist review.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
import numpy as np

TYPE_SHAPES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
COMPONENTS={5120:np.dtype('i1'),5121:np.dtype('u1'),5122:np.dtype('<i2'),5123:np.dtype('<u2'),5125:np.dtype('<u4'),5126:np.dtype('<f4')}


def parse(path):
    raw=path.read_bytes()
    if len(raw)<20 or raw[:4]!=b'glTF' or struct.unpack_from('<I',raw,4)[0]!=2:
        raise ValueError('Not a glTF 2.0 GLB')
    if struct.unpack_from('<I',raw,8)[0]!=len(raw):
        raise ValueError('GLB byteLength mismatch')
    off=12;js=bin_data=None
    while off<len(raw):
        n,typ=struct.unpack_from('<I4s',raw,off);off+=8
        if off+n>len(raw):raise ValueError('Chunk exceeds file length')
        if typ==b'JSON':js=json.loads(raw[off:off+n])
        if typ==b'BIN\0':bin_data=memoryview(raw)[off:off+n]
        off+=n
    if js is None or bin_data is None:raise ValueError('Missing JSON/BIN chunk')
    return js,bin_data


def accessor(doc,bin_data,idx):
    a=doc['accessors'][idx]
    if a.get('sparse'):raise ValueError(f'Sparse accessor {idx} is not supported by inspector')
    n=TYPE_SHAPES[a['type']];dt=COMPONENTS[a['componentType']];count=int(a['count'])
    if 'bufferView' not in a:return np.zeros((count,n),dtype=dt)
    view=doc['bufferViews'][a['bufferView']]
    if view.get('buffer',0)!=0:raise ValueError('External buffers unsupported')
    pos=view.get('byteOffset',0)+a.get('byteOffset',0)
    stride=view.get('byteStride',n*dt.itemsize)
    if pos<0 or pos+max(0,count-1)*stride+n*dt.itemsize>len(bin_data):
        raise ValueError(f'Accessor {idx} out of embedded buffer')
    if stride==n*dt.itemsize:
        arr=np.frombuffer(bin_data,dtype=dt,count=count*n,offset=pos).reshape(count,n).copy()
    else:
        arr=np.stack([np.frombuffer(bin_data,dtype=dt,count=n,offset=pos+i*stride) for i in range(count)])
    if a.get('normalized') and dt.kind in ('u','i'):
        limit=np.iinfo(dt)
        arr=arr.astype('f8')/(limit.max if dt.kind=='u' else limit.max)
        if dt.kind=='i':arr=np.maximum(-1,arr)
    return arr


def connected_components(n,triangles):
    parent=np.arange(n,dtype=np.int32)
    def find(v):
        v=int(v)
        while parent[v]!=v:
            parent[v]=parent[parent[v]];v=int(parent[v])
        return v
    for t in triangles:
        v0=find(t[0])
        for v in t[1:]:
            v1=find(v)
            if v0!=v1:parent[v1]=v0
    groups=Counter(find(i) for i in range(n))
    return sorted(groups.values(),reverse=True)


def inspect(path,required_clips=None,require_skin=True,require_blended=True):
    doc,binary=parse(path)
    report={'file':str(path),'status':'PASS','errors':[],'warnings':[],'skinned_primitives':[],
            'clips':[],'skin_count':len(doc.get('skins',[])),
            'rig_classification':'SKINNED' if doc.get('skins') else 'RIGID_OR_STATIC',
            'scope':'GLB data QA. Not a substitute for glTF Validator, Blender retopology, deformation-pose review or browser playback.'}
    error=report['errors'].append;warn=report['warnings'].append
    skins=doc.get('skins',[]);nodes=doc.get('nodes',[]);meshes=doc.get('meshes',[])
    if require_skin and not skins:error('No skin declared; animated rigid part hierarchy is not skinned mesh rigging')
    for si,skin in enumerate(skins):
        joints=skin.get('joints',[])
        if not joints:error(f'skin[{si}] has no joints')
        if len(set(joints))!=len(joints):error(f'skin[{si}] duplicate joint indices')
        if any(j<0 or j>=len(nodes) for j in joints):error(f'skin[{si}] invalid joint node')
        if 'inverseBindMatrices' in skin:
            inv=accessor(doc,binary,skin['inverseBindMatrices'])
            if inv.shape!=(len(joints),16):error(f'skin[{si}] inverseBindMatrices has wrong shape')
            if not np.isfinite(inv).all():error(f'skin[{si}] nonfinite inverse bind matrices')
    total_verts=0;blended=0
    for ni,node in enumerate(nodes):
        if 'skin' not in node:continue
        si=node['skin']
        if si>=len(skins) or si<0:error(f'node[{ni}] invalid skin ref');continue
        if 'mesh' not in node:error(f'node[{ni}] has skin but no mesh');continue
        for pi,prim in enumerate(meshes[node['mesh']].get('primitives',[])):
            attrs=prim.get('attributes',{})
            if not {'POSITION','JOINTS_0','WEIGHTS_0'}<=attrs.keys():
                error(f'node[{ni}].primitive[{pi}] missing position/joint/weight attribute');continue
            position=accessor(doc,binary,attrs['POSITION']);weights=accessor(doc,binary,attrs['WEIGHTS_0']);joints=accessor(doc,binary,attrs['JOINTS_0'])
            if weights.shape!=(len(position),4) or joints.shape!=(len(position),4):
                error(f'node[{ni}].primitive[{pi}] incompatible skin accessor shape');continue
            joint_desc=doc['accessors'][attrs['JOINTS_0']]
            if joint_desc['componentType'] not in (5121,5123):error('JOINTS_0 must be uint8/uint16')
            weight_desc=doc['accessors'][attrs['WEIGHTS_0']]
            if weight_desc['componentType'] not in (5126,5121,5123):error('WEIGHTS_0 must be float32 or unorm8/16')
            if weight_desc['componentType']!=5126 and not weight_desc.get('normalized'):
                error('Integer WEIGHTS_0 accessor lacks normalized=true')
            if not np.isfinite(position).all() or not np.isfinite(weights).all():error('Nonfinite vertex positions/weights')
            if (weights<-.000001).any():error('Negative vertex weights')
            norm_err=np.max(abs(weights.sum(axis=1)-1.0)) if len(weights) else 1
            if norm_err>.0002:error(f'Weights do not sum to 1: max error {norm_err:.5f}')
            limit=len(skins[si]['joints'])
            if ((joints>=limit)&(weights>1e-6)).any():error(f'JOINTS_0 index exceeds skin[{si}] joint count')
            nblend=int(((weights>1e-3).sum(axis=1)>1).sum());total_verts+=len(weights);blended+=nblend
            tri_count=0;components=[]
            if prim.get('mode',4)==4 and 'indices' in prim:
                idx=accessor(doc,binary,prim['indices']).reshape(-1).astype('i8')
                if len(idx)%3:error('Indices not divisible by 3')
                elif (idx<0).any() or (idx>=len(position)).any():error('Index outside vertex range')
                else:tri_count=len(idx)//3;components=connected_components(len(position),idx.reshape(-1,3))
            report['skinned_primitives'].append({'node':node.get('name',str(ni)),'primitive':pi,
                'vertex_count':len(position),'triangles':tri_count,'blended_vertices':nblend,
                'blended_ratio':round(nblend/max(1,len(position)),4),
                'connected_components':len(components),'largest_component_ratio':round(max(components,default=0)/max(1,len(position)),4),
                'weight_max_sum_error':round(float(norm_err),8)})
            if len(components)>1 and max(components)/max(1,len(position))<.90:
                warn('Skinned primitive has multiple disconnected topology islands (may be intentional material/UV sections)')
    report['skinned_vertices']=total_verts
    report['blended_vertices']=blended
    report['blended_ratio']=round(blended/max(1,total_verts),4)
    if require_skin and not total_verts:error('Skin exists but no mesh node has valid JOINTS_0 and WEIGHTS_0')
    if require_skin and require_blended and total_verts>0 and blended==0:
        error('No vertices blend multiple joints; this is rigid weighting, not smooth deformation-ready skinning')
    animated_nodes=set();clips=set()
    for i,clip in enumerate(doc.get('animations',[])):
        name=clip.get('name','');clips.add(name)
        duration=0;channels=clip.get('channels',[])
        for sampler in clip.get('samplers',[]):
            times=accessor(doc,binary,sampler['input']).reshape(-1)
            values=accessor(doc,binary,sampler['output'])
            if not np.isfinite(times).all() or (np.diff(times)<=0).any():error(f'clip {name} has invalid or duplicate times')
            if len(times):duration=max(duration,float(times.max()))
            if sampler.get('interpolation','LINEAR')=='CUBICSPLINE':
                if len(values)!=3*len(times):error(f'clip {name} cubic spline output count invalid')
            elif len(values)!=len(times):error(f'clip {name} sampler input/output count mismatch')
        for ch in channels:
            ni=ch.get('target',{}).get('node')
            if ni is None or ni<0 or ni>=len(nodes):error(f'clip {name} references invalid node')
            else:animated_nodes.add(ni)
        report['clips'].append({'name':name,'duration_s':round(duration,4),'channels':len(channels)})
    for clip in required_clips or []:
        if clip not in clips:error(f'Missing required animation clip {clip}')
    joint_nodes={j for skin in skins for j in skin.get('joints',[])}
    if require_skin and clips and joint_nodes and not animated_nodes.intersection(joint_nodes):
        warn('Clips do not target skin joints; inspect root/ancestor/object animation semantics')
    report['animated_skin_joints']=len(animated_nodes.intersection(joint_nodes))
    if any(not c['channels'] for c in report['clips']):warn('Empty clip with zero animation channels')
    if report['errors']:report['status']='FAIL'
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('glb',type=Path)
    p.add_argument('--required-clips',nargs='*',default=[])
    p.add_argument('--allow-rigid',action='store_true',help='Report segmented assets without failing')
    p.add_argument('--allow-rigid-weights',action='store_true',help='Allow skinned but 100%% rigid single-joint weighting')
    p.add_argument('--json',type=Path)
    a=p.parse_args(argv)
    try:result=inspect(a.glb,required_clips=a.required_clips,require_skin=not a.allow_rigid,require_blended=not a.allow_rigid_weights)
    except Exception as exc:
        result={'file':str(a.glb),'status':'FAIL','errors':[f'{type(exc).__name__}: {exc}']}
    text=json.dumps(result,ensure_ascii=False,indent=2)
    print(text)
    if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text,encoding='utf-8')
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
