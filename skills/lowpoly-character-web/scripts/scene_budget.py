#!/usr/bin/env python3
"""Static GLB scene scaling audit; NOT an FPS benchmark.

Counts visible-scene primitive submissions under a worst-case assumption that
all supplied instances are visible. A real renderer may make more or fewer
calls (shadows, multi-pass, culling, batching, LOD, material sorting).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from inspect_character_glb import parse_glb

# Design starting points, not verified hardware-independent frame budgets.
PROFILES={
    'hero': {'max_triangles':12000, 'max_primitive_submissions':8, 'max_used_materials':8},
    'npc': {'max_triangles':5000, 'max_primitive_submissions':4, 'max_used_materials':4},
    'crowd': {'max_triangles':1500, 'max_primitive_submissions':2, 'max_used_materials':2},
}

def scene_nodes(doc:dict) -> set[int]:
    nodes=doc.get('nodes',[])
    scenes=doc.get('scenes',[])
    if not scenes:return set(range(len(nodes)))
    index=doc.get('scene',0)
    if not isinstance(index,int) or index<0 or index>=len(scenes):
        raise ValueError('Invalid glTF default scene')
    visited=set()
    stack=list(scenes[index].get('nodes',[]))
    while stack:
        idx=stack.pop()
        if not isinstance(idx,int) or idx<0 or idx>=len(nodes):
            raise ValueError('Invalid scene node')
        if idx in visited:continue
        visited.add(idx)
        stack.extend(nodes[idx].get('children',[]))
    return visited


def audit(path:Path, profile='npc', instances=(1,10,30,50,100)) -> dict:
    doc,_=parse_glb(path)
    active_nodes=scene_nodes(doc)
    meshes=doc.get('meshes',[])
    accessors=doc.get('accessors',[])
    nodes=doc.get('nodes',[])
    prim_count=triangles=0
    used_mats=set()
    skinned_nodes=0
    for ni in active_nodes:
        node=nodes[ni]
        mi=node.get('mesh')
        if mi is None:continue
        if not isinstance(mi,int) or mi>=len(meshes) or mi<0:
            raise ValueError('Scene references invalid mesh index')
        if 'skin' in node:skinned_nodes+=1
        for prim in meshes[mi].get('primitives',[]):
            prim_count+=1
            if 'material' in prim:used_mats.add(prim['material'])
            if prim.get('mode',4)!=4:continue
            if 'indices' in prim:
                count=accessors[prim['indices']]['count']
            else:
                count=accessors[prim['attributes']['POSITION']]['count']
            triangles+=count//3
    cap=PROFILES[profile]
    failed=[x for x,name in (
        ('triangles','max_triangles'),('primitive_submissions','max_primitive_submissions'),
        ('used_materials','max_used_materials'))
        if {'triangles':triangles, 'primitive_submissions':prim_count,
            'used_materials':len(used_mats)}[x]>cap[name]]
    scenarios=[]
    for n in instances:
        if n<1:raise ValueError('instances must be positive')
        scenarios.append({'characters_visible':n, 'estimated_triangles':triangles*n,
                          'estimated_base_pass_primitive_draws':prim_count*n,
                          'qualifier':'Not measured GPU draw calls; does not include shadows, LOD, culling or batching'})
    return {
        'file':str(path), 'profile':profile,
        'status':'REVIEW_REQUIRED' if failed else 'STATIC_BUDGET_OK_PER_ASSET',
        'is_fps_measurement':False,
        'asset':{'glb_bytes':path.stat().st_size,'triangles':triangles,
                 'primitive_submissions':prim_count,'used_materials':len(used_mats),
                 'defined_materials':len(doc.get('materials',[])),
                 'skinned_mesh_nodes':skinned_nodes,'skins':len(doc.get('skins',[])),
                 'joint_count_total':sum(len(s.get('joints',[])) for s in doc.get('skins',[])),
                 'animations':len(doc.get('animations',[])),
                 'image_count':len(doc.get('images',[]))},
        'targets':cap, 'over_budget_metrics':failed,
        'scenarios':scenarios,
        'next_steps':[
          'Create art-directed LOD0/LOD1/LOD2, optimize appearance at target screen sizes.',
          'Reduce material/primitives and retained named nodes without breaking skin/animations.',
          'Run a real WebGL benchmark on target desktop/mobile using same scene, lights and shadows.',
          'Record renderer.info calls/triangles, FPS percentiles, first-frame/asset load and memory.',
          'For many animated clones, profile SkeletonUtils.clone + per-instance AnimationMixer first.',
          'Do not assume ordinary InstancedMesh can independently animate SkinnedMesh skeletons.'
        ],
        'scope':'Primitive count per active scene mesh node; rough one-pass draw submission upper bound if all visible, no batching. No hardware-independent FPS claim.'
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('glb',type=Path)
    ap.add_argument('--profile',choices=PROFILES,default='npc')
    ap.add_argument('--instances',type=int,nargs='+',default=[1,10,30,50,100])
    ap.add_argument('--json',type=Path)
    args=ap.parse_args()
    result=audit(args.glb,args.profile,args.instances)
    value=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(value)
    print(value)

if __name__=='__main__':main()
