#!/usr/bin/env python3
"""Reproducible existing-head asset benchmark using calibrated rendered views.
NOT a real-photo or real-scan benchmark. Keep source assets private.
"""
from __future__ import annotations
import argparse, io, json, math
from pathlib import Path
import numpy as np
from PIL import Image
from project_face_texture import load_mesh, screen, project, sha, sample, srgb_to_linear, linear_to_srgb, image8, normalize


def look_at(center,eye,size,focal):
    forward=normalize(center-eye); right=normalize(np.cross(forward,[0,1,0])); down=np.cross(forward,right)
    R=np.stack([right,down,forward]); t=-R@eye
    return np.array([[focal,0,(size-1)/2],[0,focal,(size-1)/2],[0,0,1.]]),R,t


def texture(j,b,mi):
    p=j['materials'][mi]['pbrMetallicRoughness']; tex=p['baseColorTexture']
    if tex.get('texCoord',0)!=0 or tex.get('extensions'): raise ValueError('Requires untransformed baseColor UV0')
    img=j['images'][j['textures'][tex['index']]['source']]; bv=j['bufferViews'][img['bufferView']]; off=bv.get('byteOffset',0)
    im=Image.open(io.BytesIO(b[off:off+bv['byteLength']])).convert('RGB')
    return srgb_to_linear(np.asarray(im)/255.)*np.array(p.get('baseColorFactor',[1,1,1,1]))[:3]


def render_uv(tri,target,uv,K,R,t,size,height=None):
    ids,_,w,_=screen(tri,K,R,t,size,height or size); m=ids>=0; fg=np.zeros_like(m);fg[m]=target[ids[m]]
    mapidx=np.full(len(tri),-1);mapidx[target]=np.arange(target.sum()); bi=w[fg];bi=np.c_[bi,1-bi.sum(1)]
    coords=np.einsum('ni,nij->nj',bi,uv[mapidx[ids[fg]]]); return fg,coords


def render_map(im,fg,coords,observed=None):
    h,w=im.shape[:2]; xy=coords*[w,h]-.5; rgb=np.full((*fg.shape,3),.09)
    valid=np.ones(len(coords),bool)
    if observed is not None:
        x0=np.clip(np.floor(xy[:,0]).astype(int),0,w-1);y0=np.clip(np.floor(xy[:,1]).astype(int),0,h-1);x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1)
        valid=observed[y0,x0]&observed[y0,x1]&observed[y1,x0]&observed[y1,x1]
    rr=np.full((len(coords),3),.20);rr[valid]=sample(im,xy[valid]);rgb[fg]=rr;mask=np.zeros_like(fg);mask[fg]=valid
    return rgb,mask


def stats(pred,truth,valid,den):
    if not valid.any(): return {'coverage':0,'mae_srgb_255':None,'psnr_srgb_db':None,'pixels':0,'eligible_pixels':int(den)}
    delta=linear_to_srgb(pred[valid])-linear_to_srgb(truth[valid]); mse=np.mean(delta**2)
    return {'coverage':float(valid.sum()/den),'mae_srgb_255':float(np.mean(abs(delta))*255),'psnr_srgb_db':float(-10*np.log10(mse)) if mse>0 else None,'pixels':int(valid.sum()),'eligible_pixels':int(den)}


def benchmark(mesh,material,out,size=512,view_size=640,front_axis='+z',exclude=(),diagnostic=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); mesh=Path(mesh).resolve()
    tri,target,uv,j,b,mi,skipped=load_mesh(mesh,material,exclude); source=texture(j,b,mi); skin=tri[target]; low=skin.min((0,1));high=skin.max((0,1));center=(low+high)/2
    extent=max(high-low); distance=extent*3.2; focal=view_size*2.1; sign=1 if front_axis=='+z' else -1
    train=[0,-45,45,-90,90,-140,140,180];hold=[-25,25,-65,65,115]; views={}; renders={}
    for angle in train+hold:
        theta=math.radians(angle); eye=center+distance*np.array([math.sin(theta)*sign,0,math.cos(theta)*sign]); K,R,t=look_at(center,eye,view_size,focal)
        fg,coords=render_uv(tri,target,uv,K,R,t,view_size); im,_=render_map(source,fg,coords)
        name=f'view_{angle:+d}';folder=out/('train' if angle in train else 'holdout');folder.mkdir(exist_ok=True)
        Image.fromarray(image8(linear_to_srgb(im))).save(folder/f'{name}.png');Image.fromarray(image8(fg.astype(float))).save(folder/f'{name}_mask.png')
        views[angle]={'id':name,'role':'train' if angle in train else 'holdout','image':str((folder/f'{name}.png').resolve()),'mask':str((folder/f'{name}_mask.png').resolve()),'rectified':True,'K':K.tolist(),'R':R.tolist(),'t':t.tolist()};renders[angle]=(fg,coords,im)
    common={'diagnostic_mode':True,'source_kind':'rendered_asset','mesh':str(mesh),'mesh_sha256':sha(mesh),'skin_material':material,'exclude_materials':list(exclude),'acknowledge_skipped_occluders':True,'diagnostic_allow_overlap':diagnostic,'depth_tolerance_m':.00075,'min_view_cosine':.25,'mask_feather_px':5}
    results={}; maps={}
    gt=sample(source,np.stack(np.meshgrid((np.arange(size)+.5)/size,(np.arange(size)+.5)/size),-1).reshape(-1,2)*[source.shape[1],source.shape[0]]-.5).reshape(size,size,3)
    for label,angles in [('front_only',[0]),('multiview',train)]:
        m={**common,'views':[views[a] for a in angles]}; p=out/f'{label}_manifest.json';p.write_text(json.dumps(m,indent=2)); folder=out/label; r=project(p,folder,size)
        im=srgb_to_linear(np.asarray(Image.open(folder/'projected_rgba.png').convert('RGB'))/255); mask=np.asarray(Image.open(folder/'observed_mask.png'))>127
        maps[label]=(im,mask); atlas=np.asarray(Image.open(folder/'atlas_mask.png'))>127
        result={'projection_coverage':r['coverage'],'atlas_error':stats(im,gt,mask,int(atlas.sum())),'sampled_overlap_pixels':r['sampled_overlap_pixels'],'holdout':{},'elapsed_seconds':r['elapsed_seconds']}
        for a in hold:
            fg,coords,gtimg=renders[a]; pred,valid=render_map(im,fg,coords,mask);result['holdout'][str(a)]=stats(pred,gtimg,valid,int(fg.sum()));Image.fromarray(image8(linear_to_srgb(pred))).save(folder/f'heldout_{a:+d}.png')
        results[label]=result
    paired={}
    for a in hold:
        fg,coords,gtimg=renders[a]; p0,v0=render_map(maps['front_only'][0],fg,coords,maps['front_only'][1]); p1,v1=render_map(maps['multiview'][0],fg,coords,maps['multiview'][1]); common_mask=v0&v1
        paired[str(a)]={'front':stats(p0,gtimg,common_mask,int(fg.sum())),'multi':stats(p1,gtimg,common_mask,int(fg.sum()))}
    report={'benchmark_type':'existing_textured_head_asset_rendered_views_not_real_photographs','mesh_sha256':sha(mesh),'material':material,'skin_triangles':int(target.sum()),'atlas_size':size,'view_size':view_size,'train_angles':train,'heldout_angles':hold,'results':results,'paired_holdout_same_pixels':paired,'limits':'Calibrated unlit renders of an existing asset. No independent photo or scan truth, no perceptual score or generalization guarantee. Coverage only inside rasterized skin UV; hidden areas remain unknown. Transparent occluders omitted from rendering; use real masks on photographs. Not a release gate.'}
    (out/'benchmark_report.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('--skin-material',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--size',type=int,default=512);p.add_argument('--view-size',type=int,default=640);p.add_argument('--front-axis',choices=['+z','-z'],default='+z');p.add_argument('--exclude-material',action='append',default=[]);p.add_argument('--diagnostic-allow-overlap',action='store_true');a=p.parse_args();print(json.dumps(benchmark(a.mesh,a.skin_material,a.out,a.size,a.view_size,a.front_axis,a.exclude_material,a.diagnostic_allow_overlap),indent=2))

if __name__=='__main__': main()
