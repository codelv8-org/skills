#!/usr/bin/env python3
"""Compose observed colors with an explicit compatible fallback, retaining inference mask.
Never invent missing skin or treat this as measured albedo. RGB output is draft material input.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from project_face_texture import sha,srgb_to_linear,linear_to_srgb,image8


def compose(projection,out,fallback=None,provenance=None,padding=8):
    projection=Path(projection);out=Path(out);r=json.loads((projection/'projection_report.json').read_text());p=projection/'projected_rgba.png'
    if sha(p)!=r['projected_sha256'] or r['sampled_overlap_pixels']:raise ValueError('Stale or overlapping projected atlas')
    rgba=np.asarray(Image.open(p).convert('RGBA')); uv=np.asarray(Image.open(projection/'atlas_mask.png').convert('L'))>127; observed=rgba[:,:,3]>127
    if uv.shape!=observed.shape or observed.sum()!=r['observed_texels'] or uv.sum()!=r['atlas_texels'] or np.any(observed&~uv):raise ValueError('Projection mask/evidence mismatch')
    missing=uv&~observed; color=srgb_to_linear(rgba[:,:,:3]/255.)
    if missing.any():
        if fallback is None or not provenance:raise ValueError('Unobserved skin requires explicitly authorized UV-compatible fallback and provenance; do not fill automatically')
        fb=np.asarray(Image.open(fallback).convert('RGB')); 
        if fb.shape!=rgba[:,:,:3].shape:raise ValueError('Fallback must use exact same atlas layout and dimensions')
        color[missing]=srgb_to_linear(fb[missing]/255.)
    if not 0<=padding<=64:raise ValueError('Padding outside shell must be 0..64 pixels')
    if padding and uv.any():
        distance,indices=distance_transform_edt(~uv,return_indices=True); edge=(~uv)&(distance<=padding); color[edge]=color[indices[0,edge],indices[1,edge]]
    out.mkdir(parents=True,exist_ok=True);Image.fromarray(image8(linear_to_srgb(color))).save(out/'basecolor_draft.png');Image.fromarray(image8(missing.astype(float))).save(out/'inferred_mask.png');Image.fromarray(image8(observed.astype(float))).save(out/'observed_mask.png')
    report={'status':'DRAFT_COLOR_REQUIRES_VISUAL_AND_DELIGHTING_QA','mesh_sha256':r['mesh_sha256'],'projection_sha256':sha(p),'fallback_sha256':sha(fallback) if fallback else None,'fallback_provenance':provenance,'inferred_texels':int(missing.sum()),'observed_texels':int(observed.sum()),'padding_px':padding,'basecolor_sha256':sha(out/'basecolor_draft.png'),'warning':'No intrinsic albedo estimation. Fallback compatibility must be visually verified against locked UV. Dilation outside shells only; inspect mips/seams and preserve masks.'};(out/'composition_report.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('projection',type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--fallback',type=Path);p.add_argument('--fallback-provenance');p.add_argument('--padding',type=int,default=8);a=p.parse_args();print(json.dumps(compose(a.projection,a.out,a.fallback,a.fallback_provenance,a.padding),indent=2))

if __name__=='__main__':main()
