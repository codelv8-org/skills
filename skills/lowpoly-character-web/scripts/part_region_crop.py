#!/usr/bin/env python3
"""Crop reference and render with the SAME region from globally aligned views.

Never independently auto-scale a model crop to match reference silhouettes.
Input JSON: {"reference_dir":"/path/ref", "render_dir":"/path/renders",
             "part":"HEAD", "roi_normalized":{
               "front":[.30,.05,.70,.35],"back":[.30,.05,.70,.35],
               "left":[.30,.05,.70,.35],"right":[.30,.05,.70,.35]}}
Images must have the same dimensions per view already; no camera calibration
is implied. Writes cropped inputs, overlay PNG and provenance manifest.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(config:Path,out:Path):
    d=json.loads(config.read_text(encoding='utf-8'))
    parent=config.resolve().parent
    ref=Path(d['reference_dir']); mod=Path(d['render_dir'])
    if not ref.is_absolute():ref=parent/ref
    if not mod.is_absolute():mod=parent/mod
    part=d.get('part','HEAD').upper()
    if not d.get('global_alignment_verified'):
        # Do not allow unverified inputs to be fed into a similarity gate and
        # mistakenly considered calibrated. Crops are still useful for review.
        calibrated=False
    else:calibrated=True
    results={}
    for view,box in d['roi_normalized'].items():
        if len(box)!=4 or not(0<=box[0]<box[2]<=1 and 0<=box[1]<box[3]<=1):
            raise ValueError(f'{view}: Invalid normalized ROI')
        rp=ref/f'{view}.png'; mp=mod/f'{view}.png'
        for f in (rp,mp):
            if not f.is_file():raise FileNotFoundError(f)
        with Image.open(rp) as rimg,Image.open(mp) as mimg:
            r=ImageOps.exif_transpose(rimg).convert('RGBA')
            m=ImageOps.exif_transpose(mimg).convert('RGBA')
        if r.size!=m.size:
            raise ValueError(f'{view}: Reference and render do not have common full-frame dimensions; calibration required')
        width,height=r.size
        roi=tuple(int(round(q*(width if j%2==0 else height))) for j,q in enumerate(box))
        rc=r.crop(roi);mc=m.crop(roi)
        target=out/view;target.mkdir(parents=True,exist_ok=True)
        rc.save(target/'reference.png');mc.save(target/'render.png')
        # Overlay for manual alignment check only; alpha does not represent a
        # valid segmentation mask.
        Image.blend(rc,mc,.5).save(target/'overlay.png')
        results[view]={
           'roi_px':list(roi),'raw_canvas_size':[width,height],
           'crop_size':list(rc.size),
           'reference_sha256':sha(rp),'render_sha256':sha(mp),
           'files':{'reference':'reference.png','render':'render.png','overlay':'overlay.png'},
        }
    output={'part':part,'status':'CROP_READY_ALIGNMENT_REVIEW_NEEDED' if not calibrated else 'CROPPED_FROM_REVIEWED_CALIBRATION',
            'global_alignment_verified_from_input':calibrated,
            'note':'Same ROI on both images; not a scored likeness measure and no mask inference.',
            'views':results}
    out.mkdir(parents=True,exist_ok=True)
    (out/'crop_manifest.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
    return output


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest',type=Path);ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    output=prepare(a.manifest,a.out)
    print(json.dumps({'status':output['status'],'part':output['part'],'views':list(output['views'])}))

if __name__=='__main__':main()
