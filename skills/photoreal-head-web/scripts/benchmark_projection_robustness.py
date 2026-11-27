#!/usr/bin/env python3
"""B1 stress benchmark on fixed rendered head inputs; not a real-photo study."""
import argparse, copy, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from project_face_texture import project, sha, load_mesh, srgb_to_linear, linear_to_srgb, image8
from benchmark_head_projection import benchmark, render_uv, render_map, stats, look_at
from math import radians,sin,cos


def stress(mesh, material, out, size=1024, view_size=768, front_axis='+z'):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    mesh=Path(mesh).resolve(); clean=out/'roundtrip'
    base_report=benchmark(mesh,material,clean,size,view_size,front_axis)
    m=json.loads((clean/'multiview_manifest.json').read_text())
    if m['mesh_sha256']!=sha(mesh): raise ValueError('Stale benchmark mesh')
    tri,target,uv,_,_,_,_=load_mesh(mesh,material,m.get('exclude_materials',[]))
    # Preset corruption: independently of holdout, tint one oblique training photo.
    bad=copy.deepcopy(m);v=next(x for x in bad['views'] if x['id']=='view_+45')
    im=np.asarray(Image.open(v['image']).convert('RGB'))/255.
    mask=np.asarray(Image.open(v['mask']).convert('L'))>127
    im[mask]=np.clip(im[mask]+np.array([.16,-.09,-.10]),0,1)
    p=out/'corrupted_training_view.png';Image.fromarray(image8(im)).save(p);v['image']=str(p)
    maps={}; reports={}
    reviewed=copy.deepcopy(bad); reviewed['views']=[x for x in reviewed['views'] if x['id']!='view_+45']
    for label,manifest,mode in [('clean_mean',m,'weighted_mean'),('clean_robust',m,'robust_consensus'),('tinted_mean',bad,'weighted_mean'),('tinted_robust',bad,'robust_consensus'),('reviewed_quarantine',reviewed,'robust_consensus')]:
        doc={**manifest,'blend_mode':mode,'consensus_threshold_srgb':.06}; mp=out/f'{label}_manifest.json';mp.write_text(json.dumps(doc,indent=2));d=out/label
        r=project(mp,d,size);rgba=np.asarray(Image.open(d/'projected_rgba.png').convert('RGBA'))
        maps[label]=(srgb_to_linear(rgba[:,:,:3]/255.),rgba[:,:,3]>127)
        reports[label]={'coverage':r['coverage'],'consensus':r['consensus'],'views':[{k:v[k] for k in ('id','consensus_eligible_texels','consensus_rejected_texels','consensus_rejected_fraction','inspect_view') if k in v} for v in r['views']],'holdout':{}}
    skin=tri[target];low=skin.min((0,1));high=skin.max((0,1));center=(low+high)/2;dist=max(high-low)*3.2;sign=1 if front_axis=='+z' else -1
    paired={}; panel=[]
    for angle in base_report['heldout_angles']:
        a=radians(angle);eye=center+dist*np.array([sin(a)*sign,0,cos(a)*sign]);K,R,t=look_at(center,eye,view_size,view_size*2.1)
        fg,coords=render_uv(tri,target,uv,K,R,t,view_size)
        truth=srgb_to_linear(np.asarray(Image.open(clean/'holdout'/f'view_{angle:+d}.png').convert('RGB'))/255.)
        rendered={};common=fg.copy()
        for name,(atlas,support) in maps.items():
            pred,valid=render_map(atlas,fg,coords,support);common&=valid;rendered[name]=(pred,valid)
            reports[name]['holdout'][str(angle)]=stats(pred,truth,valid,int(fg.sum()))
        paired[str(angle)]={name:stats(pred,truth,common,int(fg.sum())) for name,(pred,_) in rendered.items()}
        if angle in (25,65): panel.append((angle,[truth]+[rendered[n][0] for n in ('tinted_mean','tinted_robust','reviewed_quarantine')]))
    aggregate={}
    for name in maps:
        entries=[x[name] for x in paired.values()];n=sum(x['pixels'] for x in entries)
        aggregate[name]=sum(x['mae_srgb_255']*x['pixels'] for x in entries if x['pixels'])/n if n else None
    result={'status':'B1_STRESS_ONLY_NOT_RELEASE','mesh_sha256':sha(mesh),'skin_triangles':int(target.sum()),'atlas_size':size,'view_size':view_size,'corruption':{'view':'view_+45','srgb_delta':[.16,-.09,-.10],'threshold_srgb':.06},'results':reports,'paired_holdout':paired,'paired_weighted_mae_srgb_255':aggregate,'limitations':'Synthetic color corruption of one rendered training view. Reviewed quarantine removes the deliberately corrupted view by predefined training-only diagnosis; not a general automatic decision. Not real photographs, albedo recovery, UV repair or photorealism proof.'}
    (out/'stress_report.json').write_text(json.dumps(result,indent=2)+'\n')
    w=320;h=344;sheet=Image.new('RGB',(w*4,h*len(panel)),(23,29,38));draw=ImageDraw.Draw(sheet)
    for row,(angle,images) in enumerate(panel):
        for col,(label,img) in enumerate(zip(('Reference','Weighted mean','Robust consensus','Reviewed quarantine'),images)):
            preview=Image.fromarray(image8(linear_to_srgb(img))).resize((w,w));sheet.paste(preview,(col*w,row*h+24));draw.text((col*w+10,row*h+5),f'{angle:+d} deg | {label}',fill='white')
    sheet.save(out/'comparison.jpg',quality=94)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('--skin-material',required=True);p.add_argument('--out',required=True,type=Path);p.add_argument('--size',type=int,default=1024);p.add_argument('--view-size',type=int,default=768);p.add_argument('--front-axis',choices=['+z','-z'],default='+z');a=p.parse_args();r=stress(a.mesh,a.skin_material,a.out,a.size,a.view_size,a.front_axis);print(json.dumps(r['paired_weighted_mae_srgb_255'],indent=2))
