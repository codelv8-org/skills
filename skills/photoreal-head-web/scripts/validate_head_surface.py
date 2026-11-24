#!/usr/bin/env python3
"""Measure an actual, uncompressed GLB skin atlas; optionally verify release evidence.
Requires numpy and Pillow. Numerical checks are not proof of photorealism.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import sys
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw
from render_uv_layout_glb import read_asset, accessor_data
from inspect_glb import inspect as inspect_glb

REGIONS = ('forehead', 'nose', 'cheek_l', 'cheek_r', 'eye_l', 'eye_r', 'lips', 'chin', 'ear_l', 'ear_r', 'scalp')
LANDMARKS = ('brow_inner_l', 'brow_arch_l', 'brow_outer_l', 'brow_inner_r', 'brow_arch_r', 'brow_outer_r', 'en_l', 'en_r', 'ex_l', 'ex_r', 'prn', 'al_l', 'al_r', 'sn', 'ch_l', 'ch_r', 'cupid_l', 'cupid_r', 'ear_l', 'ear_r', 'hairline')
REVIEWS = ('checker_front', 'checker_profile', 'checker_threequarter', 'albedo_unlit', 'normal_closeup', 'light_soft', 'light_side', 'light_rim', 'browser_front', 'browser_profile', 'browser_brow_switch')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cross(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def overlap_area(a, b):
    """Convex triangle clipping; shared edges/vertices have zero area."""
    poly = list(a)
    orient = 1 if cross(b[1]-b[0], b[2]-b[0]) > 0 else -1
    for i in range(3):
        p, q = b[i], b[(i+1)%3]
        old, poly = poly, []
        if not old:
            return 0.0
        for j, end in enumerate(old):
            start = old[j-1]
            ds, de = orient*cross(q-p, start-p), orient*cross(q-p, end-p)
            if (ds >= -1e-14) != (de >= -1e-14):
                poly.append(start + (end-start)*(ds/(ds-de)))
            if de >= -1e-14:
                poly.append(end)
    return abs(sum(cross(poly[i], poly[(i+1)%len(poly)]) for i in range(len(poly))))/2 if poly else 0.0


def measure(p, u, winding, max_anisotropy=4., max_density_ratio=4.):
    """Triangles in local meters; glTF UV convention is top-left origin (+v down)."""
    p, u = np.asarray(p, float), np.asarray(u, float)
    if p.ndim != 3 or p.shape[1:] != (3, 3) or u.shape != (len(p), 3, 2) or not len(p):
        raise ValueError('Expected nonempty aligned arrays of 3D/UV triangles')
    if not np.isfinite(p).all() or not np.isfinite(u).all():
        raise ValueError('Nonfinite positions or UVs')
    if winding not in ('cw', 'ccw'):
        raise ValueError('Explicit expected UV winding required')
    a, b = p[:,1]-p[:,0], p[:,2]-p[:,0]
    x, y = u[:,1]-u[:,0], u[:,2]-u[:,0]
    signed = x[:,0]*y[:,1]-x[:,1]*y[:,0]
    area3 = np.linalg.norm(np.cross(a,b),axis=1)/2
    area_uv = abs(signed)/2
    good = (area3 > 1e-14) & (area_uv > 1e-12)
    # Local surface basis -> UV Jacobian. Singular values quantify angular distortion.
    aniso = np.full(len(p), np.inf)
    density = np.zeros(len(p))
    if good.any():
        ag, bg = a[good], b[good]
        length = np.linalg.norm(ag,axis=1)
        proj = np.sum(ag*bg,axis=1)/length
        height = 2*area3[good]/length
        basis = np.zeros((sum(good),2,2)); basis[:,0,0]=length; basis[:,0,1]=proj; basis[:,1,1]=height
        mat = np.stack((x[good],y[good]),axis=-1) @ np.linalg.inv(basis)
        sv = np.linalg.svd(mat,compute_uv=False)
        aniso[good] = sv[:,0]/np.maximum(sv[:,1],1e-20)
        density[good] = np.sqrt(area_uv[good]/area3[good])
    median = float(np.median(density[good])) if good.any() else 0.
    ratio = np.full(len(p),np.inf)
    if median:
        ratio[good] = np.maximum(density[good]/median, median/density[good])
    outside = np.any((u < -1e-7) | (u > 1+1e-7),axis=(1,2))
    flipped = good & ((signed < 0) if winding=='ccw' else (signed > 0))
    # Spatial bins + exact intersection. Stop once enough counterexamples prove failure.
    bins = defaultdict(list); pairs = []; capped = False
    for i,t in enumerate(u):
        if not good[i] or outside[i]:
            continue
        lo = np.maximum(0,np.floor(t.min(0)*128).astype(int)); hi=np.minimum(127,np.floor(t.max(0)*128).astype(int))
        lo=np.minimum(lo,127)
        keys=[(j,k) for j in range(lo[0],hi[0]+1) for k in range(lo[1],hi[1]+1)]
        candidates=set(j for key in keys for j in bins[key])
        for j in candidates:
            if overlap_area(t,u[j]) > 1e-11:
                pairs.append([j,i])
                if len(pairs)>=100:
                    capped=True; break
        if capped: break
        for key in keys: bins[key].append(i)
    def p95(values):
        return float(np.percentile(values[good],95)) if good.any() else None
    stats = {'triangles':len(p), 'degenerate':int((~good).sum()), 'out_of_bounds':int(outside.sum()), 'wrong_winding':int(flipped.sum()), 'overlap_pairs_found':len(pairs), 'overlap_examples':pairs, 'overlap_scan_capped':capped, 'anisotropy_p95':p95(aniso), 'relative_density_ratio_p95':p95(ratio), 'median_uv_units_per_local_meter':median}
    errors = [k for k in ('degenerate','out_of_bounds','wrong_winding','overlap_pairs_found') if stats[k]]
    if not good.any() or stats['anisotropy_p95']>max_anisotropy: errors.append('anisotropy threshold')
    if not good.any() or stats['relative_density_ratio_p95']>max_density_ratio: errors.append('relative density threshold')
    return stats, errors, aniso, ratio


def load_skin(path, name):
    gltf, binary = read_asset(path)
    materials = gltf.get('materials',[])
    matches = [i for i,m in enumerate(materials) if m.get('name')==name]
    if len(matches)!=1: raise ValueError('Choose one unique named skin material')
    mi=matches[0]; meshes=[]; ps=[]; us=[]; anchors={}; h=hashlib.sha256()
    for mesh_index, mesh in enumerate(gltf.get('meshes',[])):
        for pi, prim in enumerate(mesh.get('primitives',[])):
            if prim.get('material')!=mi: continue
            if prim.get('mode',4)!=4 or 'KHR_draco_mesh_compression' in prim.get('extensions',{}): raise ValueError('Decode skin to triangle primitives before QA')
            attrs=prim['attributes']
            pos=np.asarray(accessor_data(gltf,binary,attrs['POSITION']),float)
            uv=np.asarray(accessor_data(gltf,binary,attrs['TEXCOORD_0']),float)
            idx=np.asarray(accessor_data(gltf,binary,prim['indices']),int).ravel() if 'indices' in prim else np.arange(len(pos))
            if len(idx)%3 or len(pos)!=len(uv) or idx.min()<0 or idx.max()>=len(pos): raise ValueError('Invalid skin primitive indices/UV0')
            idx=idx.reshape(-1,3); p=pos[idx]; u=uv[idx]
            ps.append(p); us.append(u); meshes.append(mesh_index); anchors[(mesh_index,pi)]=u
            h.update(np.asarray([mesh_index,pi,len(idx)],dtype='<i8').tobytes()); h.update(idx.astype('<i8').tobytes()); h.update(uv.astype('<f8').tobytes())
    if not ps or len(set(meshes))!=1: raise ValueError('Use one dedicated skin mesh/atlas; separate eyes, hair and decals')
    return gltf,binary,materials[mi],np.concatenate(ps),np.concatenate(us),anchors,h.hexdigest()


def read_map(gltf,binary,info):
    if not info or info.get('texCoord',0)!=0 or 'KHR_texture_transform' in info.get('extensions',{}): raise ValueError('Missing map or unsupported non-UV0/transformed map')
    tex=gltf['textures'][info['index']]; image=gltf['images'][tex['source']]
    if 'bufferView' not in image: raise ValueError('Require embedded PNG/JPEG for QA; decode KTX2 first')
    bv=gltf['bufferViews'][image['bufferView']]; off=bv.get('byteOffset',0)
    if bv.get('buffer',0)!=0: raise ValueError('Require embedded GLB image')
    with Image.open(io.BytesIO(binary[off:off+bv['byteLength']])) as im:
        return im.convert('RGB')


def map_checks(gltf,binary,mat,u):
    mr=mat.get('pbrMetallicRoughness',{}); result={}; errors=[]; warnings=[]
    if mat.get('alphaMode','OPAQUE')!='OPAQUE' or mat.get('extensions',{}).get('KHR_materials_transmission',{}).get('transmissionFactor',0)>0:
        errors.append('Skin must be opaque; transmission is not subsurface scattering')
    if mat.get('extensions',{}).get('KHR_materials_unlit') is not None:
        errors.append('Unlit skin is a diagnostic view, not a release material')
    for name,info in [('basecolor',mr.get('baseColorTexture')),('normal',mat.get('normalTexture')),('metallicroughness',mr.get('metallicRoughnessTexture'))]:
        im=read_map(gltf,binary,info); w,h=im.size
        # Sample only occupied UV texels, at a bounded resolution. Metallic zero is checked
        # against the full dedicated atlas to avoid missing tiny painted metallic areas.
        thumb=im.resize((min(w,1024),min(h,1024)),Image.Resampling.NEAREST); tw,th=thumb.size
        mask=Image.new('1',thumb.size); draw=ImageDraw.Draw(mask)
        for tri in u: draw.polygon([(float(a)*(tw-1),float(b)*(th-1)) for a,b in tri],fill=1)
        rgb=np.asarray(thumb)[np.asarray(mask,dtype=bool)]/255.
        if not len(rgb): raise ValueError('No occupied skin texels')
        result[name]={'size':[w,h], 'occupied_sample_pixels':len(rgb)}
        if name=='metallicroughness':
            metal=float(np.max(np.asarray(im)[:,:,2]))/255*float(mr.get('metallicFactor',1))
            rough=rgb[:,1]*float(mr.get('roughnessFactor',1))
            result[name].update(metallic_effective_max=metal,roughness_std=float(rough.std()),roughness_range=[float(rough.min()),float(rough.max())])
            if metal>1e-6: errors.append('Skin effective metallic must be zero')
            if rough.std()<.003: warnings.append('Near-uniform roughness; inspect regional variation')
        elif name=='normal':
            n=rgb*2-1; length=np.linalg.norm(n,axis=1)
            result[name].update(normal_length_median=float(np.median(length)),negative_z_fraction=float(np.mean(n[:,2]<0)))
            if np.mean(n[:,2]<0)>.01 or np.median(abs(length-1))>.15: errors.append('Invalid tangent normal data')
            if np.std(n[:,:2])<.008: warnings.append('Near-flat normal; verify baked detail')
    return result,errors,warnings


def registration(anchors, landmarks, tolerance):
    errors=[]; rows={}
    for name in LANDMARKS:
        try:
            item=landmarks[name]; key=(int(item['mesh']),int(item['primitive'])); i=int(item['triangle']); weight=np.asarray(item['barycentric'],float)
            if i<0 or i>=len(anchors[key]) or weight.shape!=(3,) or not np.isfinite(weight).all() or min(weight)<0 or abs(sum(weight)-1)>1e-5: raise ValueError('bad barycentric anchor')
            actual=weight@anchors[key][i]; target=np.asarray(item['texture_uv'],float)
            if target.shape!=(2,) or not np.isfinite(target).all() or min(target)<0 or max(target)>1: raise ValueError('bad annotated texture point')
            rows[name]={'actual_uv':actual.tolist(),'texture_uv':target.tolist(),'distance_uv':float(np.linalg.norm(actual-target))}
        except (KeyError,IndexError,TypeError,ValueError) as exc: errors.append(f'{name}: invalid/missing independent landmark ({exc})')
    if errors: return rows,errors
    span=float(np.linalg.norm(np.array(rows['ex_l']['texture_uv'])-rows['ex_r']['texture_uv']))
    if span<.02: return rows,['Invalid outer-eye UV span']
    for name,row in rows.items():
        row['error_over_eye_span']=row['distance_uv']/span
        if row['error_over_eye_span']>tolerance: errors.append(f'{name}: texture/mesh registration exceeds tolerance')
    return rows,errors


def heatmap(u,values,out,size=1024):
    im=Image.new('RGB',(size,size),(25,29,35)); d=ImageDraw.Draw(im)
    for tri,value in zip(u,values):
        t=min(1.,max(0.,math.log2(max(1.,float(value)))/3))
        d.polygon([(float(x)*(size-1),float(y)*(size-1)) for x,y in tri],fill=(round(45+210*t),round(190-145*t),70))
    im.save(out)


def validate(path,name,winding,manifest=None,report_dir=None,uv_only=False):
    gltf,binary,material,p,u,anchors,uv_hash=load_skin(path,name)
    stats,errors,aniso,ratio=measure(p,u,winding)
    maps,err,warnings=({},[],[]) if uv_only else map_checks(gltf,binary,material,u); errors+=err
    result={'candidate_sha256':digest(path),'uv_sha256':uv_hash,'skin_material':name,'winding':winding,'uv':stats,'maps':maps,'warnings':warnings,'errors':errors,'scope':'Numeric QA of dedicated skin atlas in local geometry; manual semantic, padding, seam, lighting, color-space and browser review still required.'}
    if report_dir:
        report_dir.mkdir(parents=True,exist_ok=True)
        heatmap(u,aniso,report_dir/'uv_anisotropy.png'); heatmap(u,ratio,report_dir/'uv_density.png')
    if manifest:
        doc=json.loads(manifest.read_text()); root=manifest.parent
        for field in ('candidate_sha256','uv_sha256','skin_material','winding'):
            if doc.get(field)!=result[field]: errors.append(f'Stale or mismatched {field}')
        if not str(doc.get('atlas_id','')).strip(): errors.append('Missing atlas identity/version')
        rows,err=registration(anchors,doc.get('landmarks',{}),.01); result['registration']=rows; errors+=err
        for key in ('source_license','texture_provenance','inferred_regions','reviewer'):
            if not str(doc.get(key,'')).strip(): errors.append(f'Missing {key}')
        if doc.get('semantic_alignment_reviewed') is not True or doc.get('seam_padding_reviewed') is not True or doc.get('color_normal_reviewed') is not True: errors.append('Require actual semantic, seam/padding and color/normal reviews')
        for key in REVIEWS:
            try:
                item=doc['reviews'][key]; f=root/item['file']
                if item.get('reviewed') is not True or not item.get('notes','').strip() or not f.is_file() or digest(f)!=item['sha256']: raise ValueError('missing/stale image evidence or review notes')
                with Image.open(f) as im: im.verify()
            except (KeyError,TypeError,ValueError,OSError) as exc: errors.append(f'{key}: {exc}')
        result['status']='BLOCKED' if errors else 'PASS_SURFACE_EVIDENCE'
    else: result['status']='BLOCKED' if errors else ('PASS_UV_ONLY' if uv_only else 'PASS_NUMERIC_ONLY')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('glb',type=Path); ap.add_argument('--skin-material',required=True); ap.add_argument('--winding',required=True,choices=['cw','ccw']); ap.add_argument('--uv-only',action='store_true'); ap.add_argument('--manifest',type=Path); ap.add_argument('--report-dir',type=Path,required=True); ap.add_argument('--anatomy-export-report',type=Path); ap.add_argument('--promote',type=Path)
    a=ap.parse_args(); a.report_dir.mkdir(parents=True,exist_ok=True)
    try:
        if a.uv_only and (a.manifest or a.promote): raise ValueError('UV-only cannot certify surface/release')
        result=validate(a.glb,a.skin_material,a.winding,a.manifest,a.report_dir,a.uv_only)
        if a.promote:
            if result['status']!='PASS_SURFACE_EVIDENCE' or not a.anatomy_export_report: raise ValueError('Promotion requires passing manifest and anatomy-gated candidate export report')
            e=json.loads(a.anatomy_export_report.read_text())
            if e.get('status')!='CANDIDATE_NEEDS_SURFACE_QA' or e.get('glb_sha256')!=result['candidate_sha256'] or e.get('release_mode') is not True or e.get('manual_anatomy_review_declared') is not True: raise ValueError('Anatomy candidate export report does not match this asset')
            structural=inspect_glb(a.glb,90000,25,True)
            result['structural']=structural
            if structural['status']!='PASS': raise ValueError('Candidate failed structural GLB audit: '+str(structural['errors']))
            if a.promote.exists() or a.promote.resolve()==a.glb.resolve(): raise ValueError('Refusing to overwrite an existing asset')
            a.promote.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(a.glb,a.promote); result['promoted']=str(a.promote)
    except (OSError,ValueError,KeyError,TypeError,IndexError,ArithmeticError,np.linalg.LinAlgError) as exc:
        result=locals().get('result',{'errors':[]})
        result['status']='BLOCKED'; result['errors'].append(str(exc))
    (a.report_dir/'surface_qa.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(result['status']); return 1 if result['status']=='BLOCKED' else 0

if __name__=='__main__': sys.exit(main())
