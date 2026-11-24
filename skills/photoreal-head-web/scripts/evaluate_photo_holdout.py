#!/usr/bin/env python3
"""Evaluate projected atlas on independent calibrated holdout photos; report coverage and appearance residual, not albedo accuracy."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
from project_face_texture import load_mesh,camera,sha,srgb_to_linear,linear_to_srgb,image8
from benchmark_head_projection import render_uv,render_map,stats


def evaluate(manifest,projection_dirs,out):
    manifest=Path(manifest); base=manifest.parent; m=json.loads(manifest.read_text()); mesh=base/m['mesh']; mesh_hash=sha(mesh)
    if m.get('mesh_sha256')!=mesh_hash: raise ValueError('Stale mesh hash')
    tri,target,uv,_,_,_,skipped=load_mesh(mesh,m['skin_material'],m.get('exclude_materials',[]));
    if skipped and m.get('acknowledge_skipped_occluders') is not True: raise ValueError('Acknowledge excluded occluders and mask them')
    candidates=[];train_hashes=set();names=set()
    for d in map(Path,projection_dirs):
        r=json.loads((d/'projection_report.json').read_text()); p=d/'projected_rgba.png'
        if d.name in names: raise ValueError('Distinct projection directory names required')
        names.add(d.name)
        if r['mesh_sha256']!=mesh_hash or r['skin_material']!=m['skin_material'] or r['projected_sha256']!=sha(p): raise ValueError('Projection not bound to target mesh/material or stale atlas')
        if r['sampled_overlap_pixels']: raise ValueError('Diagnostic overlap atlas cannot be benchmarked as valid')
        if sorted(r['skipped_occluders'])!=skipped: raise ValueError('Occluder policy mismatch')
        with Image.open(p) as im: a=np.asarray(im.convert('RGBA'))
        candidates.append((d.name,srgb_to_linear(a[:,:,:3]/255.),a[:,:,3]>127,sha(p)))
        train_hashes.update(v['image_sha256'] for v in r['views'])
    if not candidates or not m.get('views'): raise ValueError('Need candidate atlas and holdout views')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);results=[];seen=set();
    for i,v in enumerate(m['views']):
        if v.get('role')!='holdout': raise ValueError('Only role=holdout views allowed')
        ih=sha(base/v['image'])
        if ih in train_hashes or ih in seen: raise ValueError('Training/holdout leakage or duplicate holdout image')
        seen.add(ih)
        K,R,t,im,mask,fit=camera(v,base); h,w=mask.shape; fg,coords=render_uv(tri,target,uv,K,R,t,w,h); eligible=fg&mask
        union=(fg|mask).sum();iou=float(eligible.sum()/union) if union else 0.
        min_iou=float(m.get('min_skin_mask_iou',.80))
        if not 0<min_iou<=1 or not eligible.any() or iou<min_iou: raise ValueError(f'Holdout {v["id"]} mask/mesh IoU {iou:.3f} insufficient; check alignment and skin-only mask')
        gt=srgb_to_linear(im)*np.array(v.get('linear_gain',[1,1,1]),float); gt=np.clip(gt,0,1)
        preds=[]; matched=eligible.copy();den=int(eligible.sum())
        for name,atlas,cov,hash_ in candidates:
            pred,visible=render_map(atlas,fg,coords,cov); visible&=eligible;matched&=visible
            preds.append((name,pred,visible,hash_));
        rec={'id':v['id'],'image_sha256':ih,'skin_mask_iou':iou,'pose':fit,'eligible_pixels':den,'candidates':{}}
        for k,(name,pred,visible,hash_) in enumerate(preds):
            rec['candidates'][name]={'atlas_sha256':hash_,'own_support':stats(pred,gt,visible,den),'common_support':stats(pred,gt,matched,den)}
            # Gray represents excluded/unobserved; separately store mask and residual map.
            preview=np.full_like(pred,.09);preview[visible]=pred[visible]; Image.fromarray(image8(linear_to_srgb(preview))).save(out/f'view_{i:02}_candidate_{k:02}.png')
            error=np.zeros((h,w),float);error[visible]=np.mean(abs(linear_to_srgb(pred[visible])-linear_to_srgb(gt[visible])),axis=1)
            Image.fromarray(image8(error),'L').save(out/f'view_{i:02}_candidate_{k:02}_error.png');Image.fromarray(image8(visible.astype(float)),'L').save(out/f'view_{i:02}_candidate_{k:02}_support.png')
        results.append(rec)
    report={'status':'APPEARANCE_METRICS_ONLY_REVIEW_REQUIRED','mesh_sha256':mesh_hash,'holdout_manifest_sha256':sha(manifest),'source_kind':m.get('source_kind','unspecified'),'views':results,'warning':'Holdout images must be independently acquired and calibrated, not crops/duplicates of training images. Hash checks only catch exact duplicates. Pixel residual includes light, camera and shape differences; no identity, albedo or release proof. For fair comparisons inspect both coverage and common-support error.'}
    (out/'photo_holdout_report.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('holdout_manifest',type=Path);p.add_argument('--projection',action='append',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(evaluate(a.holdout_manifest,a.projection,a.out),indent=2))

if __name__=='__main__': main()
