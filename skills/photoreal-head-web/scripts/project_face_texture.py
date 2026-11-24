#!/usr/bin/env python3
"""Bake calibrated, rectified photographs onto a locked GLB UV atlas (CPU).
Requires numpy, numba, scipy, Pillow; optional opencv-python-headless for pose fitting.
No generative filling or de-lighting. Unknown skin remains transparent.
"""
from __future__ import annotations
import argparse, io, json, hashlib, time
from pathlib import Path
import numpy as np
from PIL import Image
from numba import njit
from scipy.ndimage import distance_transform_edt
from render_uv_layout_glb import read_asset, accessor_data


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(a): return a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-30)


def srgb_to_linear(a): return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055)**2.4)


def linear_to_srgb(a):
    a=np.clip(a,0,1)
    return np.where(a <= .0031308, a*12.92, 1.055*a**(1/2.4)-.055)


def image8(a): return np.uint8(np.rint(np.clip(a,0,1)*255))


def transform(node):
    if 'matrix' in node: return np.array(node['matrix'],float).reshape(4,4).T
    from scipy.spatial.transform import Rotation
    m=np.eye(4); m[:3,:3]=Rotation.from_quat(node.get('rotation',[0,0,0,1])).as_matrix() @ np.diag(node.get('scale',[1,1,1])); m[:3,3]=node.get('translation',[0,0,0]); return m


def load_mesh(path, material, excluded=()):
    """Return world triangles for all opaque occluders, skin mask, skin UV0 and material.
    Static active GLB scene only. Skip alpha geometry explicitly; require disclosure.
    """
    j,b=read_asset(Path(path)); mats=j.get('materials',[])
    matches=[i for i,m in enumerate(mats) if m.get('name')==material]
    if len(matches)!=1: raise ValueError('Select exactly one named skin material')
    mi=matches[0]; parts=[]; target=[]; uv=[]; names=[]; skipped=[]
    if mats[mi].get('alphaMode','OPAQUE')!='OPAQUE': raise ValueError('Skin must be opaque')
    if material in excluded: raise ValueError('Cannot exclude target material')
    def walk(ni,parent,ancestors):
        if ni in ancestors: raise ValueError('Cyclic scene graph')
        node=j['nodes'][ni]; world=parent@transform(node)
        if node.get('skin') is not None or node.get('weights') or 'skin' in node: raise ValueError('Freeze skinned/morphed geometry first')
        if 'mesh' in node:
            mesh=j['meshes'][node['mesh']]
            for p in mesh['primitives']:
                if p.get('targets') or p.get('mode',4)!=4 or 'KHR_draco_mesh_compression' in p.get('extensions',{}): raise ValueError('Only static decoded triangles supported')
                i=p.get('material',-1); name=mats[i].get('name',str(i)) if i>=0 else '(default)'
                if name in excluded or (i>=0 and mats[i].get('alphaMode','OPAQUE')!='OPAQUE'):
                    skipped.append(name); continue
                a=p['attributes']; v=np.array(accessor_data(j,b,a['POSITION']),float)
                ind=(np.array(accessor_data(j,b,p['indices']),int).ravel() if 'indices' in p else np.arange(len(v))).reshape(-1,3)
                if ind.min()<0 or ind.max()>=len(v): raise ValueError('Invalid indices')
                v=v@world[:3,:3].T+world[:3,3]; triangles=v[ind]; is_skin=i==mi
                if np.linalg.det(world[:3,:3])<0: triangles=triangles[:,[0,2,1]]; ind=ind[:,[0,2,1]]
                if not np.isfinite(triangles).all(): raise ValueError('Nonfinite geometry')
                parts.append(triangles); target.extend([is_skin]*len(ind)); names.append(name)
                if is_skin:
                    u=np.array(accessor_data(j,b,a['TEXCOORD_0']),float)[ind]
                    if not np.isfinite(u).all() or np.any(u< -1e-7) or np.any(u>1+1e-7): raise ValueError('Invalid skin UV0')
                    uv.append(u)
        for child in node.get('children',[]): walk(child,world,ancestors+(ni,))
    for root in j['scenes'][j.get('scene',0)]['nodes']: walk(root,np.eye(4),())
    if not uv: raise ValueError('No target triangles in scene')
    return np.concatenate(parts),np.array(target,bool),np.concatenate(uv),j,b,mi,sorted(set(skipped))


@njit(cache=False)
def raster(xy,z,width,height,perspective):
    """Pixel-center triangle raster, perspective-correct weights and z buffer.
    Atlas collision count excludes shared edges (strict interior only).
    """
    ids=np.full((height,width),-1,np.int32); depth=np.full((height,width),np.inf,np.float32)
    weights=np.zeros((height,width,2),np.float32); hits=np.zeros((height,width),np.uint16)
    for k in range(len(xy)):
        a,b,c=xy[k]; den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-12: continue
        x0=max(0,int(np.ceil(min(a[0],b[0],c[0])))); x1=min(width-1,int(np.floor(max(a[0],b[0],c[0]))))
        y0=max(0,int(np.ceil(min(a[1],b[1],c[1])))); y1=min(height-1,int(np.floor(max(a[1],b[1],c[1]))))
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den; w2=1-w0-w1
                if min(w0,w1,w2)<-1e-8: continue
                if min(w0,w1,w2)>1e-7 and hits[y,x]<65535: hits[y,x]+=1
                if perspective:
                    s=w0/z[k,0]+w1/z[k,1]+w2/z[k,2]
                    if s<=0: continue
                    d=1/s; w0=w0*d/z[k,0]; w1=w1*d/z[k,1]
                else: d=1.
                if d<depth[y,x]:
                    ids[y,x]=k; depth[y,x]=d; weights[y,x,0]=w0; weights[y,x,1]=w1
    return ids,depth,weights,hits


def camera(view,base):
    im=Image.open(base/view['image']).convert('RGB'); mask=Image.open(base/view['mask']).convert('L')
    if im.size!=mask.size: raise ValueError('Image and mask sizes differ')
    w,h=im.size; K=np.asarray(view['K'],float)
    if min(w,h)<2: raise ValueError('Image must be at least 2x2')
    if K.shape!=(3,3) or not np.isfinite(K).all() or K[0,0]<=0 or K[1,1]<=0 or not np.allclose(K,[[K[0,0],0,K[0,2]],[0,K[1,1],K[1,2]],[0,0,1]]): raise ValueError('Expected rectified pinhole K without skew')
    if view.get('rectified') is not True: raise ValueError('Rectify image AND mask before projecting; set rectified=true only after verification')
    if 'landmarks' in view:
        R,t,fit=fit_pose(K,view['landmarks'],view.get('max_validation_rmse_px',3.0))
    else:
        R=np.asarray(view['R'],float); t=np.asarray(view['t'],float); fit={'method':'provided_pose','validation':'independent overlay required'}
    if R.shape!=(3,3) or t.shape!=(3,) or not np.isfinite(R).all() or not np.isfinite(t).all() or not np.allclose(R@R.T,np.eye(3),atol=1e-5) or not np.isclose(np.linalg.det(R),1,atol=1e-5): raise ValueError('Invalid right-handed world-to-camera transform')
    return K,R,t,np.asarray(im)/255.,np.asarray(mask)>127,fit


def fit_pose(K,landmarks,threshold=3.):
    import cv2
    train=landmarks['fit']; val=landmarks['validate']
    if len(train)<6 or len(val)<3: raise ValueError('At least 6 fit + 3 independent validation landmarks required')
    def unpack(x): return np.array([a['xyz'] for a in x],np.float64),np.array([a['xy'] for a in x],np.float64)
    a,b=unpack(train); va,vb=unpack(val)
    if not np.isfinite(a).all() or not np.isfinite(b).all() or not np.isfinite(va).all() or not np.isfinite(vb).all() or np.linalg.matrix_rank(a-a.mean(0))<3: raise ValueError('Fit landmarks must be noncoplanar and finite')
    if any(np.min(np.linalg.norm(a-x,axis=1))<1e-7 for x in va): raise ValueError('Fit and validation anchors must be independent')
    ok,r,t,inliers=cv2.solvePnPRansac(a,b,K,None,reprojectionError=3.,iterationsCount=200,confidence=.999,flags=cv2.SOLVEPNP_EPNP)
    if not ok or inliers is None or len(inliers)<6: raise ValueError('Pose fitting failed')
    ii=inliers.ravel(); r,t=cv2.solvePnPRefineLM(a[ii],b[ii],K,None,r,t)
    R=cv2.Rodrigues(r)[0]; t=t.ravel(); xy,zz=project_points(va,K,R,t)
    rmse=float(np.sqrt(np.mean(np.sum((xy-vb)**2,axis=1))))
    if np.any(zz<=0) or not np.isfinite(rmse) or rmse>threshold: raise ValueError(f'Independent pose validation failed: {rmse:.3f}px')
    return R,t,{'method':'PnP RANSAC + LM','inliers':int(len(ii)),'fit_count':len(a),'validation_count':len(va),'validation_rmse_px':rmse,'threshold_px':float(threshold)}


def project_points(p,K,R,t):
    q=p@R.T+t; z=q[...,2]; xy=(q@K.T)[...,:2]/np.maximum(z[...,None],1e-30); return xy,z


def screen(tri,K,R,t,w,h):
    xy,z=project_points(tri,K,R,t)
    if np.any(z<=1e-6): raise ValueError('Near-plane clipping unsupported: all scene triangles must be in front of camera')
    return raster(xy,z,w,h,True)


def atlas_samples(tri,uv,size):
    ids,_,b,hits=raster(uv*size-.5,np.ones((len(uv),3)),size,size,False)
    valid=ids>=0; ti=ids[valid]; bw=b[valid]; bw=np.c_[bw,1-bw.sum(1)]
    points=np.einsum('ni,nij->nj',bw,tri[ti]); normals=normalize(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]))[ti]
    return ids,valid,points,normals,hits


def sample(im,xy):
    """Bilinear, pixel-center coordinates. Input is linear-light RGB."""
    h,w=im.shape[:2]; x=np.clip(xy[:,0],0,w-1); y=np.clip(xy[:,1],0,h-1)
    x0=np.floor(x).astype(int); y0=np.floor(y).astype(int); x1=np.minimum(x0+1,w-1); y1=np.minimum(y0+1,h-1); dx=(x-x0)[:,None];dy=(y-y0)[:,None]
    return (im[y0,x0]*(1-dx)+im[y0,x1]*dx)*(1-dy)+(im[y1,x0]*(1-dx)+im[y1,x1]*dx)*dy


def project(manifest_path,out,size=1024):
    start=time.monotonic(); manifest_path=Path(manifest_path); base=manifest_path.parent; m=json.loads(manifest_path.read_text()); mesh=base/m['mesh']; out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if m.get('mesh_sha256')!=sha(mesh): raise ValueError('Mesh hash mismatch; regenerate manifest after geometry/UV changes')
    diagnostic=m.get('diagnostic_mode') is True
    if not diagnostic:
        if m.get('rights_verified') is not True or not m.get('source_provenance'): raise ValueError('Verify source rights and provenance before production projection')
        report_path=base/m['uv_qa_report']; qa=json.loads(report_path.read_text())
        if qa.get('candidate_sha256')!=sha(mesh) or qa.get('skin_material')!=m['skin_material'] or qa.get('status') not in ('PASS_UV_ONLY','PASS_NUMERIC_ONLY') or qa.get('errors')!=[]: raise ValueError('Current mesh must pass v3 exact UV QA before production projection')
        if m.get('diagnostic_allow_overlap'): raise ValueError('Overlap override is diagnostic-only')
        if any(v.get('pose_overlay_reviewed') is not True for v in m.get('views',[])): raise ValueError('Inspect and attest independent pose overlay for each view')
    if not 64<=size<=4096: raise ValueError('Atlas size outside 64..4096')
    tri,target,uv,_,_,_,skipped=load_mesh(mesh,m['skin_material'],m.get('exclude_materials',[])); skin=tri[target]
    if skipped and m.get('acknowledge_skipped_occluders') is not True: raise ValueError(f'Explicitly acknowledge skipped materials and mask their projected pixels: {skipped}')
    ids,valid,points,normals,hits=atlas_samples(skin,uv,size)
    overlaps=int(np.count_nonzero(hits>1)); n=len(points)
    if n==0: raise ValueError('Empty rasterized skin atlas')
    if overlaps and not m.get('diagnostic_allow_overlap',False): raise ValueError(f'UV overlap at {overlaps} sampled pixels; fix with v3 UV validator first')
    accum=np.zeros((n,3),np.float64); weight=np.zeros(n); counts=np.zeros(n,np.uint16); sources=[]; debug=[]
    tol=float(m.get('depth_tolerance_m',.001)); mincos=float(m.get('min_view_cosine',.25)); feather=float(m.get('mask_feather_px',8))
    if not 0<tol<=.005 or not 0<mincos<1 or not 1<=feather<=100: raise ValueError('Unsafe visibility parameters')
    if not m.get('views') or len(m['views'])>256: raise ValueError('Expected 1..256 projection views')
    exposure=m.get('exposure_match','off')
    if exposure not in ('off','overlap_scalar'): raise ValueError('Unsupported exposure matching mode')
    seen=set()
    for view in m['views']:
        name=view['id'];
        if not isinstance(name,str) or not name or name in seen: raise ValueError('Unique view IDs required')
        seen.add(name)
        if view.get('role','train')!='train': raise ValueError('Holdout views must not enter projection manifest')
        K,R,t,im,mask,fit=camera(view,base); h,w=mask.shape; sid,depth,_,_=screen(tri,K,R,t,w,h); skin_screen=np.zeros_like(mask); fg=sid>=0; skin_screen[fg]=target[sid[fg]]; mask=mask&skin_screen
        xy,z=project_points(points,K,R,t); center=-R.T@t; cos=np.sum(normals*normalize(center-points),axis=1)
        xx=np.clip(np.rint(xy[:,0]).astype(int),0,w-1); yy=np.clip(np.rint(xy[:,1]).astype(int),0,h-1)
        # Require four bilinear source pixels inside the independently reviewed mask/skin.
        fx=np.clip(np.floor(xy[:,0]).astype(int),0,w-2); fy=np.clip(np.floor(xy[:,1]).astype(int),0,h-2)
        support=mask[fy,fx]&mask[fy+1,fx]&mask[fy,fx+1]&mask[fy+1,fx+1]
        ok=(z>0)&(xy[:,0]>=0)&(xy[:,0]<w-1)&(xy[:,1]>=0)&(xy[:,1]<h-1)&support&(cos>=mincos)&(abs(depth[yy,xx]-z)<=tol)
        ii=np.flatnonzero(ok); d=distance_transform_edt(mask); q=np.clip(d[yy[ii],xx[ii]]/feather,0,1)*cos[ii]**4
        # Camera exposure/color correction supplied explicitly, in linear RGB. Not inverse lighting.
        gain=np.asarray(view.get('linear_gain',[1,1,1]),float)
        if gain.shape!=(3,) or not np.isfinite(gain).all() or np.any(gain<=0) or np.any(gain>4): raise ValueError('Invalid color correction gain')
        color=np.clip(sample(srgb_to_linear(im),xy[ii])*gain,0,1)
        scalar, match_count = 1.,0
        if exposure=='overlap_scalar' and sources:
            # Estimate exposure only, not white balance, shadows, or intrinsic albedo.
            match=(weight[ii]>.1)&(q>.1)
            prev=accum[ii[match]]/weight[ii[match],None]; current=color[match]
            lum=np.array([.2126,.7152,.0722]); old=prev@lum; new=current@lum
            good=(old>.04)&(old<.90)&(new>.04)&(new<.90); match_count=int(good.sum())
            if match_count>=128: scalar=float(np.clip(np.exp(np.median(np.log(old[good]/new[good]))),.67,1.5))
            color=np.clip(color*scalar,0,1)
        accum[ii]+=color*q[:,None]; weight[ii]+=q; counts[ii]+=1
        sources.append({'id':name,'covered_texels':int(len(ii)),'image_sha256':sha(base/view['image']),'mask_sha256':sha(base/view['mask']),'pose':fit,'linear_gain':gain.tolist(),'overlap_exposure_gain':scalar,'exposure_overlap_samples':match_count})
    covered=weight>1e-10; color=np.zeros((n,3));color[covered]=accum[covered]/weight[covered,None]
    rgb=np.zeros((size,size,3),float); rgb[valid]=linear_to_srgb(color); alpha=np.zeros((size,size));alpha[valid]=covered
    # Do not inpaint holes inside atlas. Padding outside UV shells only, retained separately.
    rgba=np.dstack((rgb,alpha));Image.fromarray(image8(rgba),'RGBA').save(out/'projected_rgba.png')
    cov=np.zeros_like(alpha);cov[valid]=covered;Image.fromarray(image8(cov),'L').save(out/'observed_mask.png')
    Image.fromarray(image8(valid.astype(float)),'L').save(out/'atlas_mask.png')
    c=np.zeros_like(alpha);c[valid]=np.minimum(counts/ max(1,len(m['views'])),1);Image.fromarray(image8(c),'L').save(out/'view_support.png')
    missing=valid&(cov==0); im=np.zeros((size,size,3),np.uint8);im[valid]=[34,139,95];im[missing]=[225,60,65];Image.fromarray(im).save(out/'coverage_heatmap.png')
    coverage=float(covered.mean()); report={'status':'DRAFT_PROJECTION' if diagnostic or coverage<1 or overlaps else 'COMPLETE_NUMERIC_COVERAGE_ONLY','diagnostic_mode':diagnostic,'source_kind':m.get('source_kind','unspecified'),'mesh_sha256':sha(mesh),'manifest_sha256':sha(manifest_path),'size':size,'skin_material':m['skin_material'],'skin_triangles':int(len(skin)),'scene_opaque_triangles':len(tri),'skipped_occluders':skipped,'atlas_texels':n,'observed_texels':int(covered.sum()),'coverage':coverage,'unobserved_texels':int((~covered).sum()),'sampled_overlap_pixels':overlaps,'view_count':len(sources),'exposure_match':exposure,'views':sources,'projected_sha256':sha(out/'projected_rgba.png'),'elapsed_seconds':round(time.monotonic()-start,3),'warning':'Observed color only; not measured albedo. No true de-lighting, no inpainting, not photoreal or release QA. Exact UV overlap requires v3 validator.'}
    (out/'projection_report.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('manifest',type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--size',type=int,default=1024);a=ap.parse_args();print(json.dumps(project(a.manifest,a.out,a.size),indent=2))

if __name__=='__main__': main()
