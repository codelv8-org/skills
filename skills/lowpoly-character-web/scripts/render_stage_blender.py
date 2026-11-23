#!/usr/bin/env python3
"""Render the delivered GLB in Blender and record exact render provenance.

Run: blender -b -t 4 --python render_stage_blender.py -- model.glb --out review
Optional --camera-config cameras.json uses glTF coordinates (Y up, +Z front):
{"target":[0,1.45,0],"ortho_scale_m":0.6,"resolution":[600,660],
 "alignment":"APPROXIMATE_CONCEPT","views":{"front":{"yaw_deg":0},
 "left":{"yaw_deg":-80}}}
Camera metadata is a record of rendering parameters, not calibration proof.
Static rest-pose only. Use an animation-aware renderer for deformation evidence.
"""
from pathlib import Path
import argparse, hashlib, json, math, sys
import bpy
from mathutils import Vector

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model');p.add_argument('--out',required=True)
    p.add_argument('--camera-config');p.add_argument('--samples',type=int,default=32)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    src=Path(args.model).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    if src.suffix.lower()!='.glb' or src.read_bytes()[:4]!=b'glTF':raise ValueError('Input must be an actual GLB')
    cfg=json.loads(Path(args.camera_config).read_text()) if args.camera_config else {}
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(src))
    scene=bpy.context.scene
    for ob in scene.objects:
        if ob.type=='ARMATURE':ob.data.pose_position='REST'
        if ob.animation_data:ob.animation_data_clear()
    verts=[ob.matrix_world @ Vector(v) for ob in scene.objects if ob.type=='MESH' for v in ob.bound_box]
    if not verts:raise ValueError('GLB has no visible mesh to render')
    mins=Vector([min(v[i] for v in verts) for i in range(3)])
    maxs=Vector([max(v[i] for v in verts) for i in range(3)])
    midpoint=(mins+maxs)/2
    # Imported glTF Y maps to Blender Z and glTF Z maps to Blender -Y.
    tgt=cfg.get('target',[midpoint.x,midpoint.z,-midpoint.y])
    target=Vector((tgt[0],-tgt[2],tgt[1]))
    ortho=float(cfg.get('ortho_scale_m',max(maxs-mins)*1.25))
    if not math.isfinite(ortho) or ortho<=0:raise ValueError('ortho_scale_m must be finite and positive')
    res=cfg.get('resolution',[600,660])
    if len(res)!=2 or any(not isinstance(v,int) or v<16 or v>4096 for v in res):raise ValueError('Invalid resolution')
    scene.render.engine='CYCLES';scene.cycles.samples=max(1,args.samples);scene.cycles.use_denoising=False
    scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    world=bpy.data.worlds.new('QA neutral world');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.70,.80,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.35;scene.world=world
    def light(name,pos,power,size):
        dat=bpy.data.lights.new(name,'AREA');dat.energy=power;dat.shape='DISK';dat.size=size
        ob=bpy.data.objects.new(name,dat);scene.collection.objects.link(ob);ob.location=target+Vector(pos)
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    light('QA key',(-1.5,-2.5,2.55),150,3.5);light('QA fill',(2,-1,.75),50,3);light('QA rim',(0,2,1.55),100,3)
    camdata=bpy.data.cameras.new('QA camera');cam=bpy.data.objects.new('QA camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
    views=cfg.get('views',{'front':{'yaw_deg':0},'back':{'yaw_deg':180},'left':{'yaw_deg':-90},'right':{'yaw_deg':90}})
    result={'source_glb':str(src),'model_sha256':digest(src),'blender_version':bpy.app.version_string,
        'pose':'REST_STATIC','alignment':cfg.get('alignment','UNVERIFIED'),
        'note':'Recorded camera setup does not prove agreement with reference camera. Source/artistic QA remains separate.',
        'views':[]}
    for name,view in views.items():
        if not name or any(x in name for x in ('/','\\','..')):raise ValueError('View name must be a simple basename')
        yaw=float(view.get('yaw_deg',0));elev=float(view.get('elevation_deg',0));distance=float(view.get('distance_m',3))
        if any(not math.isfinite(x) for x in (yaw,elev,distance)) or distance<=0:raise ValueError('Invalid camera values')
        a=math.radians(yaw);b=math.radians(elev)
        cam.location=target+Vector((math.sin(a)*math.cos(b),-math.cos(a)*math.cos(b),math.sin(b)))*distance
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        camdata.type=view.get('camera_type','ORTHO');camdata.ortho_scale=float(view.get('ortho_scale_m',ortho))
        camdata.lens=float(view.get('focal_length_mm',50))
        image=out/(name+'.png');scene.render.filepath=str(image);bpy.ops.render.render(write_still=True)
        result['views'].append({'name':name,'camera_type':camdata.type,'yaw_deg':yaw,'elevation_deg':elev,'target_gltf':tgt,
            'ortho_scale_m':camdata.ortho_scale if camdata.type=='ORTHO' else None,'distance_m':distance,
            'focal_length_mm':camdata.lens if camdata.type=='PERSP' else None,'size':res,'rgba_png':image.name,'image_sha256':digest(image)})
    (out/'render_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RENDER_COMPLETE',str(out/'render_manifest.json'))

if __name__=='__main__':main()
