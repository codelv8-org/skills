#!/usr/bin/env python3
"""Generate region masks and a supporting microdetail/roughness set from annotated actual UVs.
Never invent a facial albedo. Input regions use glTF/image top-left coordinates, not generic face positions.
"""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# Artistic starting points, NOT measured population/individual skin properties.
PROFILES = {'forehead':(.48,.75), 'nose':(.38,1.0), 'cheek_l':(.55,.7), 'cheek_r':(.55,.7), 'eye_l':(.56,.25), 'eye_r':(.56,.25), 'lips':(.48,.0), 'chin':(.52,.75), 'ear_l':(.57,.55), 'ear_r':(.57,.55), 'scalp':(.55,.65)}

def generate(doc, normal, roughness, out, feather=4, mix=.35):
    if doc.get('coordinate_space')!='gltf_uv_top_left' or not doc.get('atlas_id') or not doc.get('uv_sha256'): raise ValueError('Use independently annotated, versioned actual UV atlas')
    if not 0<=mix<=1 or not 0<=feather<=64: raise ValueError('Invalid mix or feather')
    size=normal.size
    if size!=roughness.size or size[0]!=size[1]: raise ValueError('Require same square normal and roughness maps')
    out.mkdir(parents=True,exist_ok=True)
    weights=[]; profiles=[]
    for name,(r,s) in PROFILES.items():
        polygons=doc.get('regions',{}).get(name)
        if not polygons: raise ValueError('Missing annotated region '+name)
        im=Image.new('L',size); draw=ImageDraw.Draw(im)
        for poly in polygons:
            pts=np.asarray(poly,float)
            if pts.ndim!=2 or pts.shape[1]!=2 or len(pts)<3 or not np.isfinite(pts).all() or pts.min()<0 or pts.max()>1: raise ValueError('Invalid polygon '+name)
            draw.polygon([(float(x)*(size[0]-1),float(y)*(size[1]-1)) for x,y in pts],fill=255)
        im=im.filter(ImageFilter.GaussianBlur(feather)); im.save(out/(name+'.png'))
        mask=np.asarray(im,dtype=np.float32)/255.; weights.append(mask)
        override=doc.get('profiles',{}).get(name,{})
        r=float(override.get('roughness',r)); s=float(override.get('micro_strength',s))
        if not 0<=r<=1 or not 0<=s<=1: raise ValueError('Invalid region profile '+name)
        profiles.append((r,s))
    w=np.stack(weights); summed=w.sum(0); denom=np.maximum(summed,1e-6); coverage=np.clip(summed,0,1)
    rfield=np.tensordot(np.array([p[0] for p in profiles],np.float32),w,axes=1)/denom
    strength=np.tensordot(np.array([p[1] for p in profiles],np.float32),w,axes=1)/denom
    # Do not invent detail in unmapped areas. Lips receive no generic pore detail.
    n=np.asarray(normal.convert('RGB'),np.float32)/127.5-1
    n[:,:,:2]*=(strength*coverage)[:,:,None]; n[:,:,2]=np.maximum(n[:,:,2],1e-5); n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-6)
    r0=np.asarray(roughness.convert('L'),np.float32)/255; rmap=np.clip(r0*(1-mix*coverage)+rfield*mix*coverage,0,1)
    Image.fromarray(np.round((n*.5+.5)*255).astype(np.uint8)).save(out/'regional_micro_normal_opengl.png')
    Image.fromarray(np.round(rmap*255).astype(np.uint8)).save(out/'regional_roughness.png')
    pack=np.zeros((*rmap.shape,3),np.uint8); pack[:,:,0]=255; pack[:,:,1]=np.round(rmap*255).astype(np.uint8)
    Image.fromarray(pack).save(out/'regional_metallicroughness.png')
    Image.fromarray(np.round(coverage*255).astype(np.uint8)).save(out/'region_coverage.png')
    (out/'manifest.json').write_text(json.dumps({'atlas_id':doc['atlas_id'],'uv_sha256':doc['uv_sha256'],'profiles':dict(zip(PROFILES,profiles)),'mix':mix,'warning':'Supporting microdetail only. Combine with baked macro normals using RNM or Blender bake; not an albedo or measured reflectance. Review actual UV seams and pixel scale.'},indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('regions',type=Path); p.add_argument('--normal',type=Path,required=True); p.add_argument('--roughness',type=Path,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--feather',type=float,default=4); p.add_argument('--mix',type=float,default=.35); a=p.parse_args()
    with Image.open(a.normal) as n, Image.open(a.roughness) as r: generate(json.loads(a.regions.read_text()),n,r,a.out,a.feather,a.mix)
if __name__=='__main__': main()
