#!/usr/bin/env python3
"""Create an offline 6-view proof sheet for preliminary low-poly silhouette QA.

Requires `trimesh`, `numpy`, and `matplotlib`. This is not a real browser,
texture sampling, lighting, rig deformation or GLB spec compliance test.
"""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    import numpy as np
    import trimesh
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
except ImportError as exc:
    raise SystemExit('Install: python -m pip install trimesh numpy matplotlib') from exc


ANGLES = [
    ('Front -Y', 0, -90),
    ('Front 3/4', 10, -45),
    ('Subject left +X', 0, 0),
    ('Subject right -X', 0, 180),
    ('Rear +Y', 0, 90),
    ('Rear 3/4', 10, 135),
]


def color_of(mesh):
    visual=mesh.visual
    if hasattr(visual,'material') and visual.material is not None:
        vals=getattr(visual.material,'baseColorFactor',None)
        if vals is not None:
            vals=np.asarray(vals[:3],dtype=float)
            if float(vals.max()) > 1:
                vals /= 255.0
            return np.clip(vals,0,1)
    if hasattr(visual,'face_colors') and len(visual.face_colors):
        return np.asarray(visual.face_colors[:,:3],dtype=float).mean(axis=0)/255.0
    return (0.65,0.71,0.74)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('glb',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--dpi',type=int,default=110)
    ap.add_argument('--up-axis',choices=['y','z'],default='y',help='GLB is normally Y-up; z is for nonconforming raw assets')
    args=ap.parse_args()
    scene=trimesh.load(args.glb,force='scene')
    if args.up_axis=='y':
        # Re-orient from standard glTF Y-up/+Z-forward into the authoring Z-up/-Y-forward preview frame.
        scene.apply_transform(np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]],dtype=float))
    meshes=[m for m in scene.dump() if isinstance(m,trimesh.Trimesh)]
    if not meshes:
        ap.error('No triangles found in input model')
    center=scene.bounds.mean(axis=0)
    extents=scene.extents
    diameter=max(float(extents[2]),float(extents[0])*1.9,float(extents[1])*1.9)
    radius=diameter*.54
    fig=plt.figure(figsize=(14,11),facecolor='#eef1f4')
    for i,(title,elev,azim) in enumerate(ANGLES,1):
        ax=fig.add_subplot(2,3,i,projection='3d',proj_type='ortho')
        for mesh in meshes:
            faces=np.asarray(mesh.triangles)
            if len(faces)==0:
                continue
            material=color_of(mesh)
            ax.add_collection3d(Poly3DCollection(faces,facecolors=[material],linewidths=.04,
                                                   edgecolors=(.20,.21,.22,.09),zsort='average'))
        ax.set(xlim=(center[0]-radius,center[0]+radius),
               ylim=(center[1]-radius,center[1]+radius),
               zlim=(center[2]-radius,center[2]+radius))
        ax.set_box_aspect((1,1,1),zoom=1.04)
        ax.view_init(elev=elev,azim=azim)
        ax.set_title(title,fontsize=13,fontweight='bold',pad=6)
        ax.set_axis_off()
        ax.set_facecolor('#f7f8fa')
    fig.suptitle('Low-poly character | preliminary geometry views (not final QA)',fontsize=16)
    fig.subplots_adjust(left=.02,right=.98,top=.92,bottom=.03,wspace=.06,hspace=.10)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(args.out,dpi=args.dpi,facecolor=fig.get_facecolor())
    plt.close(fig)
    print(args.out)


if __name__=='__main__':
    main()
