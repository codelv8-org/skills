#!/usr/bin/env python3
"""Render 3 orthographic diagnostic views without Blender/GPU (Pillow + trimesh)."""
import argparse
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont


def normalize(x):
    x = np.asarray(x, dtype=float)
    return x / max(np.linalg.norm(x), 1e-12)


def mesh_material_rgb(mesh):
    mat = getattr(mesh.visual, "material", None)
    col = getattr(mat, "baseColorFactor", None)
    if col is None:
        return np.array([175,175,175], dtype=float)
    c = np.asarray(col[:3], dtype=float)
    if c.max() <= 1.0:
        c *= 255
    return c


def draw_view(all_tri, all_col, direction, up, label, size=520):
    cam = normalize(direction)
    right = normalize(np.cross(up, cam))
    upward = normalize(np.cross(cam, right))
    basis = np.stack([right, upward, cam], axis=1)
    projection = all_tri @ basis
    center_xy = projection[:,:,:2].reshape(-1,2)
    lo, hi = np.min(center_xy,axis=0), np.max(center_xy,axis=0)
    center=(lo+hi)/2
    span=max((hi-lo).max(), 1e-6)
    scale=size*.81/span
    projected = (projection[:,:,:2]-center)*scale + np.array([size/2, size/2])
    projected[:,:,1] = size-projected[:,:,1]
    depth=projection[:,:,2].mean(axis=1)
    edge1=all_tri[:,1,:]-all_tri[:,0,:]
    edge2=all_tri[:,2,:]-all_tri[:,0,:]
    normal=np.cross(edge1,edge2)
    nl=np.linalg.norm(normal,axis=1)
    safe_n=normal / np.maximum(nl[:,None],1e-12)
    light=normalize([.5,1.5,1.2])
    shade=(0.56 + .44*np.abs(safe_n @ light))
    colors = np.clip(all_col * shade[:,None],0,255).astype(np.uint8)
    image=Image.new("RGB",(size,size),(247,248,246))
    draw=ImageDraw.Draw(image)
    for ix in np.argsort(depth):
        if nl[ix] < 1e-13:
            continue
        poly=[tuple(p) for p in projected[ix]]
        draw.polygon(poly, fill=tuple(int(v) for v in colors[ix]))
    draw.rounded_rectangle((10,10,145,43),radius=8,fill=(255,255,255))
    draw.text((22,19),label, fill=(36,54,45))
    return image


def load_triangles(scene):
    triangles=[]
    colors=[]
    for node in scene.graph.nodes_geometry:
        transform,name=scene.graph.get(node)
        m=scene.geometry[name]
        tri=m.triangles
        xyz = trimesh.transform_points(tri.reshape(-1,3),transform).reshape(-1,3,3)
        triangles.append(xyz)
        colors.append(np.repeat(mesh_material_rgb(m)[None,:],len(tri),axis=0))
    return np.concatenate(triangles), np.concatenate(colors)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--size",type=int,default=480)
    a=p.parse_args()
    scene=trimesh.load(str(a.model),force="scene")
    tri,col=load_triangles(scene)
    panels=[
        draw_view(tri,col,[1,1.3,1.6],[0,1,0],"ISOMETRIC",a.size),
        draw_view(tri,col,[0,0.45,1.0],[0,1,0],"FRONT",a.size),
        draw_view(tri,col,[0,1,0],[0,0,-1],"TOP",a.size)
    ]
    canvas=Image.new("RGB",(a.size*3,a.size),(245,246,244))
    for i,im in enumerate(panels):
        canvas.paste(im,(i*a.size,0))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(a.out)
    print(f"preview: {a.out}")

if __name__ == "__main__":
    main()
