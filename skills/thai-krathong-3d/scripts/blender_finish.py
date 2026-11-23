"""Optional Blender background helper: GLB -> editable .blend + transparent PNG.
Run: blender -b --python scripts/blender_finish.py -- --input model.glb --blend model.blend --render model.png
Works with Blender 3.6 and 4.x. No addon dependency.
"""
import argparse
import math
import sys
from mathutils import Vector

import bpy


def args():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--blend',required=True)
    p.add_argument('--render')
    p.add_argument('--resolution',type=int,default=1200)
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])


def aim(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def setup_scene(render_path,resolution):
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    if not objs:
        raise RuntimeError('No meshes imported from GLB')
    world_corners=[]
    for obj in objs:
        world_corners.extend([obj.matrix_world @ Vector(v) for v in obj.bound_box])
    lo=Vector(tuple(min(p[i] for p in world_corners) for i in range(3)))
    hi=Vector(tuple(max(p[i] for p in world_corners) for i in range(3)))
    target=(lo+hi)/2
    span=max(hi[i]-lo[i] for i in range(3))
    bpy.ops.object.camera_add(location=(target.x+span*2.5,target.y-span*3.0,target.z+span*2.4))
    cam=bpy.context.object
    cam.name='CAM_Studio_Orthographic'
    cam.data.type='ORTHO'
    cam.data.ortho_scale=span*1.85
    aim(cam,target)
    bpy.context.scene.camera=cam
    for n,location,power,size in [
        ('LIGHT_Key',(2, -3, 5),500,3),
        ('LIGHT_Fill',(-3, -1, 2),280,3),
        ('LIGHT_Rim',(0, 3, 4),350,2.5)]:
        bpy.ops.object.light_add(type='AREA',location=(target.x+location[0]*span,
                                                        target.y+location[1]*span,
                                                        target.z+location[2]*span))
        lamp=bpy.context.object
        lamp.name=n
        lamp.data.energy=power
        lamp.data.shape='DISK'
        lamp.data.size=size*span
        aim(lamp,target)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=32
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=True
    scene.render.resolution_x=resolution
    scene.render.resolution_y=resolution
    scene.render.resolution_percentage=100
    if scene.world:
        scene.world.use_nodes=True
        bg=scene.world.node_tree.nodes.get('Background')
        if bg:
            bg.inputs['Strength'].default_value=.65
    if render_path:
        scene.render.filepath=render_path
        bpy.ops.render.render(write_still=True)


def main():
    a=args()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=a.input)
    setup_scene(a.render,a.resolution)
    bpy.ops.wm.save_as_mainfile(filepath=a.blend)
    print(f'Saved Blender project: {a.blend}')

if __name__=='__main__':
    main()
