"""Blender-only guardrail exporter for an ALREADY retopologized human body + armature.

Usage (Blender 4.x/5.x; run inside Blender, NOT with system Python):
  blender -b source/character.blend --python scripts/blender_skin_export.py -- \
    --body Body --rig Rig --out export/character_skinned.glb \
    --clips Idle Walk Run Salute

This does not magically fuse a collection of objects or generate a humanoid.
A continuous deforming body with joint-aligned loops and a fitted armature are
prerequisites; --auto-weights can initialize weights but an artist must refine.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import traceback

try:
    import bpy
except ImportError:
    bpy=None


def parse_args(args=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--body',default='Body',help='Name of CONTINUOUS body mesh object')
    p.add_argument('--rig',default='Rig',help='Name of Armature object')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--clips',nargs='+',default=['Idle','Walk','Run','Salute'])
    p.add_argument('--auto-weights',action='store_true',help='Only create initial weights if none exist. Never use for final QA without pose review.')
    p.add_argument('--allow-unverified-nla',action='store_true',help='Permit export with missing NLA tracks; output audit must verify clips')
    return p.parse_args(args)


def connected_body(mesh):
    # Structural vertex graph check; UV splits may not affect the Blender edit mesh.
    if not mesh.vertices or not mesh.polygons:raise RuntimeError('Body contains no mesh faces')
    parent=list(range(len(mesh.vertices)))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]];a=parent[a]
        return a
    for poly in mesh.polygons:
        vs=list(poly.vertices)
        for v in vs[1:]:
            a,b=find(vs[0]),find(v)
            if a!=b:parent[b]=a
    seen={find(i) for i in range(len(mesh.vertices))}
    return len(seen)


def attach_armature(body,rig,auto_weights=False):
    modifier=next((m for m in body.modifiers if m.type=='ARMATURE'),None)
    if modifier is None:modifier=body.modifiers.new('Skin Deform','ARMATURE')
    modifier.object=rig
    if auto_weights and not body.vertex_groups:
        for obj in bpy.context.selected_objects:obj.select_set(False)
        body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
        bpy.ops.object.parent_set(type='ARMATURE_AUTO',keep_transform=True)
        modifier=next((m for m in body.modifiers if m.type=='ARMATURE'),modifier)
        modifier.object=rig
    bone_names={b.name for b in rig.data.bones if b.use_deform}
    group_names={g.name for g in body.vertex_groups}
    return bone_names.intersection(group_names)


def group_weight_stats(body,rig):
    bone_names={b.name for b in rig.data.bones if b.use_deform}
    groups={g.index:g.name for g in body.vertex_groups}
    n_blend=0;n_unweighted=0;max_err=0
    for vert in body.data.vertices:
        weighted=[g.weight for g in vert.groups if groups.get(g.group) in bone_names and g.weight>1e-5]
        if not weighted:n_unweighted+=1;continue
        n_blend+=len(weighted)>1;max_err=max(max_err,abs(sum(weighted)-1))
    return {'total_vertices':len(body.data.vertices),'unweighted':n_unweighted,'blend_count':n_blend,
            'blend_fraction':n_blend/max(1,len(body.data.vertices)),'max_sum_error':max_err}


def ensure_clips(rig,expected,allow_unverified=False):
    existing={a.name for a in bpy.data.actions}
    missing=[name for name in expected if name not in existing]
    if missing:raise RuntimeError(f'Animation actions not found: {missing}; create them on the armature first')
    # A named action alone is not exported by Blender; ensure it is actually
    # active or stashed on an NLA track. Verify after GLB export regardless.
    ad=rig.animation_data
    tracks=[]
    if ad:
        tracks=[(tr.name,[s.action.name for s in tr.strips if s.action]) for tr in ad.nla_tracks]
    linked=set(x for _,strip_actions in tracks for x in strip_actions)
    if ad and ad.action:linked.add(ad.action.name)
    unlinked=[c for c in expected if c not in linked]
    if unlinked and not allow_unverified:
        raise RuntimeError('Animations are named but not active/stashed on Rig NLA tracks: '+str(unlinked)+'. Push Down/Stash each Action into its own NLA Track before export.')
    return {'nla_tracks':tracks,'expected':expected,'unlinked_actions':unlinked}


def execute(opts):
    if bpy is None:raise RuntimeError('This script must run inside Blender (bpy required)')
    bpy.ops.object.mode_set(mode='OBJECT') if bpy.context.object and bpy.context.object.mode!='OBJECT' else None
    body=bpy.data.objects.get(opts.body);rig=bpy.data.objects.get(opts.rig)
    if body is None or body.type!='MESH':raise RuntimeError(f'Body mesh {opts.body!r} not found')
    if rig is None or rig.type!='ARMATURE':raise RuntimeError(f'Armature {opts.rig!r} not found')
    components=connected_body(body.data)
    if components!=1:
        raise RuntimeError(f'Deforming body is not topologically continuous ({components} disconnected islands). Retopologize and weld the body; do NOT merely Join objects.')
    matched=attach_armature(body,rig,opts.auto_weights)
    if not matched:raise RuntimeError('No body vertex groups match deforming rig bones; enable --auto-weights to initialize, then correct in Weight Paint')
    stats=group_weight_stats(body,rig)
    if stats['unweighted']:raise RuntimeError(f"Body has {stats['unweighted']} unweighted vertices")
    if stats['max_sum_error']>.0005:raise RuntimeError('Weight sums deviate from 1.0; normalize in Weight Paint')
    if stats['blend_count']==0:raise RuntimeError('No blended skin weights; likely rigid segmentation')
    clip_audit=ensure_clips(rig,opts.clips,opts.allow_unverified_nla)
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    props=bpy.ops.export_scene.gltf.get_rna_type().properties
    kwargs={'filepath':str(opts.out.resolve()),'export_format':'GLB','export_animations':True,'export_skins':True}
    if 'export_animation_mode' in props:kwargs['export_animation_mode']='ACTIONS'
    elif 'export_nla_strips' in props:kwargs['export_nla_strips']=True
    if 'export_all_armature_actions' in props:kwargs['export_all_armature_actions']=True
    if 'export_extras' in props:kwargs['export_extras']=True
    # Export full scene: skinned clothing and rigid accessories can coexist.
    bpy.ops.export_scene.gltf(**kwargs)
    report={'source_blend':bpy.data.filepath,'exported_glb':str(opts.out.resolve()),'body':body.name,'rig':rig.name,
            'continuous_body_components':components,'rig_bones':len(rig.data.bones),'weight_stats':stats,
            'clip_audit':clip_audit,'status':'EXPORTED_NOT_YET_VERIFIED',
            'next':'Run inspect_character_glb.py + inspect_skinning.py, plus joint bend and browser pose QA.'}
    report_path=opts.out.with_suffix('.blender_audit.json')
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return report


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    try:execute(parse_args(args))
    except Exception:
        traceback.print_exc()
        sys.exit(1)
