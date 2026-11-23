#!/usr/bin/env python3
"""Generate a real single-body skinned glTF demo, NOT a production humanoid.

Purpose: test the skill's skin+animation GLB inspector and built-in preview viewer.
The underlying smooth-union / marching-cubes topology is NOT final retopology for
high-quality elbow/shoulder/knee bending. It must not be presented as a finished
character or as a substitute for quad retopo in Blender.
Requires numpy, scipy, scikit-image, trimesh.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
import numpy as np
from skimage.measure import marching_cubes
import trimesh

JOINTS = [
    ('Pelvis',None,(0,.96,0)),
    ('Spine','Pelvis',(0,1.29,0)),
    ('Neck','Spine',(0,1.59,0)),
    ('Head','Neck',(0,1.75,0)),
    ('Shoulder_L','Spine',(-.31,1.46,0)),
    ('Elbow_L','Shoulder_L',(-.52,1.16,0)),
    ('Wrist_L','Elbow_L',(-.68,.97,0)),
    ('Shoulder_R','Spine',(.31,1.46,0)),
    ('Elbow_R','Shoulder_R',(.52,1.16,0)),
    ('Wrist_R','Elbow_R',(.68,.97,0)),
    ('Hip_L','Pelvis',(-.14,.89,0)),
    ('Knee_L','Hip_L',(-.14,.48,0)),
    ('Ankle_L','Knee_L',(-.14,.15,0)),
    ('Hip_R','Pelvis',(.14,.89,0)),
    ('Knee_R','Hip_R',(.14,.48,0)),
    ('Ankle_R','Knee_R',(.14,.15,0)),
]
JOINT_IDS={name:i for i,(name,_,_) in enumerate(JOINTS)}


def smooth_min(a,b,k=.07):
    h=np.maximum(k-np.abs(a-b),0)/k
    return np.minimum(a,b)-h*h*k*.25


def capsule(x,y,z,a,b,r):
    a=np.array(a);b=np.array(b)
    p=np.stack(np.broadcast_arrays(x,y,z),axis=-1)
    ba=b-a
    h=np.clip(np.sum((p-a)*ba,axis=-1)/np.dot(ba,ba),0,1)
    return np.linalg.norm(p-a-ba*h[...,None],axis=-1)-r


def ellipsoid(x,y,z,c,r):
    # Approximate signed distance suitable for a smooth blockout, not exact SDF.
    return (np.sqrt(((x-c[0])/r[0])**2+((y-c[1])/r[1])**2+((z-c[2])/r[2])**2)-1)*min(r)


def body_mesh(step=.042):
    axes=[np.arange(a,b+step,step,dtype='f4') for a,b in [(-.95,.95),(-.08,2.18),(-.48,.48)]]
    x,y,z=np.meshgrid(*axes,indexing='ij')
    d=ellipsoid(x,y,z,(0,1.24,0),(.30,.39,.16))
    parts=[ellipsoid(x,y,z,(0,.95,0),(.255,.2,.16)),
        capsule(x,y,z,(0,1.48,0),(0,1.69,0),.105),
        ellipsoid(x,y,z,(0,1.83,0),(.18,.22,.165)),
        capsule(x,y,z,(-.31,1.46,0),(-.70,.95,0),.103),
        capsule(x,y,z,(.31,1.46,0),(.70,.95,0),.103),
        capsule(x,y,z,(-.14,.87,0),(-.14,.15,0),.116),
        capsule(x,y,z,(.14,.87,0),(.14,.15,0),.116),
        ellipsoid(x,y,z,(-.14,.085,.07),(.13,.10,.215)),
        ellipsoid(x,y,z,(.14,.085,.07),(.13,.10,.215))]
    for part in parts:d=smooth_min(d,part,.11)
    verts,faces,normals,_=marching_cubes(d,0,spacing=(step,step,step))
    verts=verts+np.array([a[0] for a in axes])
    tm=trimesh.Trimesh(vertices=verts,faces=faces,process=True)
    if not tm.is_winding_consistent:
        tm.fix_normals()
    parts=tm.split(only_watertight=False)
    if len(parts)!=1:
        raise RuntimeError(f'Expected continuous body, got {len(parts)} topological components')
    return tm


def stepf(a,b,x):
    u=np.clip((x-a)/(b-a),0,1)
    return u*u*(3-2*u)


def weights_for(p):
    x,y,z=p;ab=abs(x);w={}
    def add(name,val):
        if val>1e-6:w[JOINT_IDS[name]]=w.get(JOINT_IDS[name],0)+val
    # Base torso and neck/head blends.
    spine=stepf(.96,1.24,y)
    add('Pelvis',1-spine)
    add('Spine',spine)
    if y>1.48:
        h=stepf(1.51,1.76,y);mid=stepf(1.47,1.57,y)*(1-h)
        for k in list(w):w[k]*=(1-h)*(1-mid)
        add('Neck',mid)
        add('Head',h)
    # Arm transitions into shoulder girdle and between shoulder/elbow/wrist.
    if y>.82 and ab>.23:
        sign='L' if x<0 else 'R';a=stepf(.26,.41,ab)
        prog=np.clip((ab-.32)/.38,0,1)
        distal=stepf(.65,.90,prog);middle=stepf(.20,.52,prog)*(1-distal)
        prox=(1-distal)*(1-stepf(.20,.52,prog))
        for k in list(w):w[k]*=(1-a)
        add('Shoulder_'+sign,a*prox);add('Elbow_'+sign,a*middle);add('Wrist_'+sign,a*distal)
    # Legs share continuous pelvis surface; blend smoothly near inguinal region.
    if y<.99 and ab>.045:
        sign='L' if x<0 else 'R';a=stepf(.99,.79,y)
        hip=stepf(.44,.76,y);ank=1-stepf(.16,.42,y)
        knee=np.clip(1-hip-ank,0,1)
        for k in list(w):w[k]*=(1-a)
        add('Hip_'+sign,a*hip);add('Knee_'+sign,a*knee);add('Ankle_'+sign,a*ank)
    inds=sorted(w,key=lambda k:w[k],reverse=True)[:4]
    vals=np.array([w[i] for i in inds]);vals/=max(vals.sum(),1e-9)
    return inds+[0]*(4-len(inds)),list(vals)+[0.]*(4-len(vals))


def animation_sequences():
    wave=[0,.25,.5,.75,1]
    def clip(name,times,channels):return name,times,channels
    return [
        clip('Idle',wave,{'Head':('Y',[0,2,0,-2,0]),'Shoulder_L':('X',[0,2,0,-2,0]),'Shoulder_R':('X',[0,-2,0,2,0])}),
        clip('Walk',wave,{'Hip_L':('X',[28,0,-28,0,28]),'Hip_R':('X',[-28,0,28,0,-28]),'Knee_L':('X',[2,30,2,7,2]),'Knee_R':('X',[2,7,2,30,2]),'Shoulder_L':('X',[-18,0,18,0,-18]),'Shoulder_R':('X',[18,0,-18,0,18]),'Elbow_L':('X',[12]*5),'Elbow_R':('X',[12]*5)}),
        clip('Run',wave,{'Hip_L':('X',[44,0,-44,0,44]),'Hip_R':('X',[-44,0,44,0,-44]),'Knee_L':('X',[10,55,10,15,10]),'Knee_R':('X',[10,15,10,55,10]),'Shoulder_L':('X',[-32,0,32,0,-32]),'Shoulder_R':('X',[32,0,-32,0,32]),'Elbow_L':('X',[30]*5),'Elbow_R':('X',[30]*5)}),
        clip('Salute',[0,.2,.45,1.25,1.5],{'Shoulder_R':('Z',[0,32,76,76,0]),'Elbow_R':('X',[0,-10,-65,-65,0]),'Head':('Y',[0,0,3,3,0])}),
    ]


def qaxis(axis,deg):
    v={'X':(1,0,0),'Y':(0,1,0),'Z':(0,0,1)}[axis]
    r=math.radians(deg)/2
    return [v[0]*math.sin(r),v[1]*math.sin(r),v[2]*math.sin(r),math.cos(r)]


class Buffer:
    def __init__(self):self.data=bytearray();self.views=[];self.acc=[]
    def append(self,array,ty,component=5126,minmax=False):
        arr=np.asarray(array,dtype={5126:'<f4',5123:'<u2',5125:'<u4'}[component])
        self.data.extend(b'\0'*((-len(self.data))%4))
        start=len(self.data)
        self.data.extend(arr.tobytes())
        bv=len(self.views);self.views.append({'buffer':0,'byteOffset':start,'byteLength':arr.nbytes})
        n=arr.shape[0];a={'bufferView':bv,'componentType':component,'count':n,'type':ty}
        if minmax:a['min']=arr.min(axis=0).astype(float).tolist();a['max']=arr.max(axis=0).astype(float).tolist()
        ai=len(self.acc);self.acc.append(a);return ai


def export_demo(out,step=.042):
    mesh=body_mesh(step)
    verts=np.asarray(mesh.vertices,dtype='f4')
    normals=np.asarray(mesh.vertex_normals,dtype='f4')
    faces=np.asarray(mesh.faces,dtype='u4')
    joints=[];weights=[]
    for v in verts:
        j,w=weights_for(v)
        joints.append(j);weights.append(w)
    joints=np.asarray(joints,dtype='u2');weights=np.asarray(weights,dtype='f4')
    # Primary color layer; this is a topology/skin proof, not finished uniform design.
    colors=np.tile(np.array([.13,.24,.37,1.],dtype='f4'),(len(verts),1))
    skin_mask=(verts[:,1]>1.67)|((np.abs(verts[:,0])>.60)&(verts[:,1]<1.11))
    colors[skin_mask]=[.69,.46,.33,1]
    pants=verts[:,1]<.91
    colors[pants]=[.075,.125,.19,1]
    boots=verts[:,1]<.19
    colors[boots]=[.035,.067,.10,1]
    face=(verts[:,1]>1.66)&(verts[:,2]>.04)
    colors[face]=[.78,.54,.39,1]
    hair=(verts[:,1]>1.98)
    colors[hair]=[.055,.11,.17,1]
    b=Buffer()
    attrs={'POSITION':b.append(verts,'VEC3',minmax=True),'NORMAL':b.append(normals,'VEC3'),'COLOR_0':b.append(colors,'VEC4'),
           'JOINTS_0':b.append(joints,'VEC4',5123),'WEIGHTS_0':b.append(weights,'VEC4')}
    indices=b.append(faces.reshape(-1,1),'SCALAR',5125)
    nodes=[{'name':'Body_Skinned','mesh':0,'skin':0}]
    root=1
    for name,parent,world in JOINTS:
        if parent is None:local=world
        else:
            prior=dict((n,w) for n,_,w in JOINTS)[parent]
            local=tuple(world[i]-prior[i] for i in range(3))
        nodes.append({'name':name,'translation':list(local)})
    for i,(name,parent,_) in enumerate(JOINTS):
        if parent:nodes[JOINT_IDS[parent]+root].setdefault('children',[]).append(i+root)
    ibm=[]
    for _,_,p in JOINTS:
        m=np.eye(4,dtype='f4');m[:3,3]=-np.array(p);ibm.append(m.T.reshape(-1))
    ibidx=b.append(np.array(ibm),'MAT4')
    animations=[]
    for name,times,channels in animation_sequences():
        a={'name':name,'samplers':[],'channels':[]}
        tidx=b.append(np.array(times,dtype='f4').reshape(-1,1),'SCALAR',minmax=True)
        for jname,(axis,angles) in channels.items():
            qidx=b.append(np.array([qaxis(axis,deg) for deg in angles]),'VEC4')
            sid=len(a['samplers']);a['samplers'].append({'input':tidx,'output':qidx,'interpolation':'LINEAR'})
            a['channels'].append({'sampler':sid,'target':{'node':JOINT_IDS[jname]+root,'path':'rotation'}})
        animations.append(a)
    doc={'asset':{'version':'2.0','generator':'Low-poly Character Studio v2 — skin format demonstrator'},'scene':0,
         'scenes':[{'nodes':[0,root]}], 'nodes':nodes,
         'meshes':[{'name':'ContinuousBody_Demo_NotProductionRetopo','primitives':[{'attributes':attrs,'indices':indices,'material':0}]}],
         'materials':[{'name':'vertex-palette','pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'metallicFactor':0,'roughnessFactor':.83},'doubleSided':True}],
         'skins':[{'name':'HumanoidSkin','joints':list(range(root,root+len(JOINTS))),'skeleton':root,'inverseBindMatrices':ibidx}],
         'animations':animations,'bufferViews':b.views,'accessors':b.acc,'buffers':[{'byteLength':len(b.data)}]}
    j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);bin_data=bytes(b.data);bin_data+=b'\0'*((-len(bin_data))%4)
    pack=struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(bin_data))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(bin_data),b'BIN\0')+bin_data
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(pack)
    manifest={'output':str(out),'triangles':len(faces),'vertices':len(verts),'skins':1,'joints':len(JOINTS),'animations':[a['name'] for a in animations],
       'source_method':'implicit single surface with smooth union, marching cubes','continuous_topological_components':1,
       'IMPORTANT':'Only GLB skinning/viewer/QA format demonstrator. Marching cubes lacks joint-aligned quad retopology. Not a finished deformation-ready human.'}
    out.with_suffix('.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--step',type=float,default=.042)
    args=p.parse_args();print(json.dumps(export_demo(args.out,args.step),indent=2))
