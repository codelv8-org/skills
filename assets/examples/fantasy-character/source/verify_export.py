#!/usr/bin/env python3
"""Independent decoding route for the exact exported GLB; not Khronos validation."""
import json, struct, hashlib, sys
from pathlib import Path
import numpy as np
import trimesh

root=Path(__file__).resolve().parents[1]
p=root/'export'/'sword-immortal-blockout.glb'
b=p.read_bytes();magic,v,length=struct.unpack_from('<4sII',b);assert magic==b'glTF' and v==2 and length==len(b)
n,kind=struct.unpack_from('<II',b,12);assert kind==0x4e4f534a
d=json.loads(b[20:20+n]);l,kind=struct.unpack_from('<II',b,20+n);assert kind==0x004e4942;bin=b[28+n:];assert len(bin)==l==d['buffers'][0]['byteLength']
DT={5126:'<f4',5123:'<u2',5125:'<u4'};DIM={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def arr(i):
    a=d['accessors'][i];bv=d['bufferViews'][a['bufferView']];off=bv.get('byteOffset',0)+a.get('byteOffset',0);dt=np.dtype(DT[a['componentType']]);count=a['count']*DIM[a['type']];assert off+count*dt.itemsize<=bv.get('byteOffset',0)+bv['byteLength']<=len(bin);return np.frombuffer(bin,dtype=dt,count=count,offset=off).reshape(a['count'],DIM[a['type']])
prim=d['meshes'][0]['primitives'][0];a=prim['attributes'];pos=arr(a['POSITION']);norm=arr(a['NORMAL']);j=arr(a['JOINTS_0']);w=arr(a['WEIGHTS_0']);idx=arr(prim['indices']).reshape(-1,3);sk=d['skins'][0];ib=arr(sk['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
assert np.isfinite(pos).all() and np.isfinite(norm).all() and np.isfinite(w).all();assert idx.max()<len(pos) and j.max()<len(sk['joints']) and w.min()>=0 and np.allclose(w.sum(axis=1),1,atol=1e-6);assert len(j)==len(w)==len(norm)==len(pos);assert np.allclose(np.linalg.norm(norm,axis=1),1,atol=1e-5)
nodes=d['nodes'];parent={c:i for i,node in enumerate(nodes) for c in node.get('children',[])}
def global_matrix(i):
    m=np.eye(4);m[:3,3]=nodes[i].get('translation',[0,0,0]);return global_matrix(parent[i])@m if i in parent else m
bind=np.stack([global_matrix(i) for i in sk['joints']])@ib;assert np.allclose(bind,np.eye(4),atol=1e-6)
for animation in d['animations']:
    for s in animation['samplers']:
        t=arr(s['input']).flatten();q=arr(s['output']);assert len(t)==len(q) and np.all(np.diff(t)>0) and np.allclose(np.linalg.norm(q,axis=1),1,atol=1e-6)
mesh=trimesh.Trimesh(vertices=pos,faces=idx,process=False);assert mesh.is_watertight and np.all(mesh.area_faces>1e-12)
reimport=trimesh.load(p,force='scene');assert len(reimport.geometry)==1 and sum(len(g.faces) for g in reimport.geometry.values())==len(idx)
report={'status':'PASS_BINARY_DIAGNOSTIC_ONLY','sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'vertices':len(pos),'triangles':len(idx),'joints':len(sk['joints']),'skinned_nodes':sum('skin' in node for node in nodes),'animation_clips':[a['name'] for a in d['animations']],'max_weight_sum_error':float(abs(w.sum(axis=1)-1).max()),'max_bind_matrix_error':float(abs(bind-np.eye(4)).max()),'normal_length_max_error':float(abs(np.linalg.norm(norm,axis=1)-1).max()),'geometry_reimport':'trimesh PASS (does not validate animation or engine behavior)','uv_present':'TEXCOORD_0' in a,'khronos_validator':'NOT RUN','threejs_runtime':'NOT RUN','production_quality':'BLOCKED G1; silhouette hull not accepted anatomy'}
(root/'evidence'/'export-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
