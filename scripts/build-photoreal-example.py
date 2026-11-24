#!/usr/bin/env python3
"""Rebuild the public example with the actual v3.1.1 projection engine.
The repo's licensed scan is the only default input. Rendered-asset B1, not real-photo QA.
"""
import argparse, base64, html, json, shutil, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/photoreal-head-web'
VERSION = '3.1.1'
SCAN = 'Infinite, 3D Head Scan by Lee Perry-Smith / Infinite Realities (CC BY 3.0)'


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def overview(path, report, comparison=None):
    head = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="960" height="540" viewBox="0 0 960 540" role="img" aria-label="Photoreal Head Projection Lab">'
    body = '<rect width="960" height="540" rx="20" fill="#0e1826"/><path d="M0 84H960" stroke="#334b5d"/><text x="30" y="35" fill="#9be2ce" font-family="sans-serif" font-size="14" letter-spacing="2">PHOTOREAL HEAD / v'+VERSION+'</text><text x="30" y="66" fill="#f1f5f7" font-family="sans-serif" font-size="27" font-weight="700">Robust Multi-view Texture Fusion</text>'
    if comparison:
        data = base64.b64encode(Path(comparison).read_bytes()).decode('ascii')
        body += '<image x="28" y="98" width="904" height="355" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/jpeg;base64,'+data+'"/>'
        s=report['stress']['mae']; line=f"Holdout color MAE: {s['tinted_mean']:.3f} / {s['tinted_robust']:.3f} / {s['reviewed_quarantine']:.3f}"
        body += '<text x="30" y="479" font-family="sans-serif" fill="#9be2ce" font-size="17">'+html.escape(line)+'</text>'
    else:
        for i,(n,title,sub) in enumerate([('01','Anatomy + UV QA','Lock the skin atlas'),('02','Calibrated views','Visibility + depth'),('03','Robust fusion','Reject conflicting samples'),('04','Holdout benchmark','Compare coverage and error')]):
            x=30+i%2*462; y=110+i//2*142
            body+=f'<rect x="{x}" y="{y}" width="438" height="122" rx="14" fill="#172a39" stroke="#344959"/><text x="{x+18}" y="{y+29}" fill="#9be2ce" font-family="sans-serif" font-size="15">{n}</text><text x="{x+18}" y="{y+64}" fill="#f1f5f7" font-family="sans-serif" font-size="23" font-weight="600">{title}</text><text x="{x+18}" y="{y+91}" fill="#b2c1ce" font-family="sans-serif" font-size="15">{sub}</text>'
        body += '<text x="30" y="453" font-family="sans-serif" fill="#f5d0a1" font-size="17">Benchmark output not available - see preview status.</text>'
    body += '<text x="30" y="514" font-family="sans-serif" font-size="13" fill="#b2c1ce">Rendered-asset diagnostic, not real-photo accuracy or production release.</text></svg>'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head+body+'\n', encoding='utf-8')


def build(mesh, output, overview_path, size, view_size, skill=SKILL, material=None, label=SCAN, baseline=None, preparation=None):
    sys.path.insert(0, str(skill/'scripts'))
    from project_face_texture import sha
    from render_uv_layout_glb import read_asset
    from validate_head_surface import load_skin, validate
    from benchmark_projection_robustness import stress
    mesh=mesh.resolve(); output=output.resolve(); target=output/'projection-lab'
    if target.exists(): shutil.rmtree(target)
    target.mkdir(parents=True)
    baseline=(baseline or mesh).resolve()
    r={'schemaVersion':1,'skillVersion':VERSION,'sourceAsset':label,'sourceSha256':None,'baselineSha256':None,'status':'NOT_RUN','scope':'Rendered asset B1 only, on a separate reparameterized unlit copy of the licensed scan. Baseline geometry and PBR maps are retained. Synthetic color cast on one training view; no independent real photos, measured reflectance, likeness or production release. Unknown surface remains gray.','atlasSize':size,'viewSize':view_size,'modes':[],'reports':{}}
    try:
        r['sourceSha256']=sha(mesh);r['baselineSha256']=sha(baseline)
        if preparation:
            prepared=json.loads(preparation.read_text())
            if prepared['source_sha256']!=r['baselineSha256'] or prepared['output_sha256']!=r['sourceSha256']:
                raise ValueError('Stale atlas preparation: source or derived mesh hash changed')
            r['atlasPreparation']='reports/atlas_preparation.json'
        if mesh.parent==output/'model':
            r['projectionMesh']=f'model/{mesh.name}'
        j,_=read_asset(mesh)
        if material is None:
            candidates=[m['name'] for m in j.get('materials',[]) if m.get('name') and m.get('pbrMetallicRoughness',{}).get('baseColorTexture')]
            if len(candidates)!=1: raise ValueError('Expected one named textured scan material')
            material=candidates[0]
        r['skinMaterial']=material
        _,_,_,_,u,_,_=load_skin(mesh,material)
        d=u[:,1]-u[:,0]; e=u[:,2]-u[:,0]; signed=d[:,0]*e[:,1]-d[:,1]*e[:,0]
        winding='ccw' if (signed>0).sum()>(signed<0).sum() else 'cw'
        uv=validate(mesh,material,winding,report_dir=target,uv_only=True)
        r['uv']={'status':uv['status'],'winding':winding,'windingBasis':'dominant sign, diagnostic only','metrics':uv['uv'],'errors':uv['errors']}
        write_json(target/'uv_report.json',uv)
        r['reports']['uv']='projection-lab/uv_report.json'
        if baseline!=mesh:
            bj,_=read_asset(baseline)
            bm=[m['name'] for m in bj['materials'] if m.get('pbrMetallicRoughness',{}).get('baseColorTexture')]
            if len(bm)!=1: raise ValueError('Expected one textured baseline material')
            _,_,_,_,bu,_,_=load_skin(baseline,bm[0])
            bd=bu[:,1]-bu[:,0]; be=bu[:,2]-bu[:,0]; bs=bd[:,0]*be[:,1]-bd[:,1]*be[:,0]
            baseline_uv=validate(baseline,bm[0],'ccw' if (bs>0).sum()>(bs<0).sum() else 'cw',uv_only=True)
            r['baselineUV']={'status':baseline_uv['status'],'metrics':baseline_uv['uv'],'errors':baseline_uv['errors']}
            write_json(target/'baseline_uv_report.json',baseline_uv)
            r['reports']['baselineUV']='projection-lab/baseline_uv_report.json'
        if uv['status']!='PASS_UV_ONLY' or uv['errors']:
            raise ValueError('Projection atlas failed exact UV validation: '+', '.join(uv['errors']))
        with tempfile.TemporaryDirectory(prefix='public-head-b1-') as tmp:
            run=Path(tmp)
            result=stress(mesh,material,run,size,view_size,'+z')
            rt=json.loads((run/'roundtrip/benchmark_report.json').read_text())
            if result['mesh_sha256']!=r['sourceSha256'] or rt['mesh_sha256']!=r['sourceSha256']: raise ValueError('Source mesh changed during build')
            modes=[('front_only',run/'roundtrip/front_only','Front-only projection'),('multiview',run/'roundtrip/multiview','8-view clean projection'),('tinted_mean',run/'tinted_mean','Tinted weighted mean'),('tinted_robust',run/'tinted_robust','Robust consensus'),('reviewed_quarantine',run/'reviewed_quarantine','Reviewed quarantine')]
            def save_mode(key,title,arr):
                f=target/f'{key}.webp'; Image.fromarray(arr).save(f,lossless=True)
                r['modes'].append({'id':key,'label':title,'path':f'projection-lab/{f.name}','sha256':sha(f)})
            for key,folder,title in modes:
                arr=np.asarray(Image.open(folder/'projected_rgba.png').convert('RGBA'))
                rgb=np.where((arr[:,:,3]>127)[:,:,None],arr[:,:,:3],np.array([120,120,120],dtype=np.uint8)).astype(np.uint8)
                save_mode(key,title,rgb)
            for key,source,title in [('coverage',run/'tinted_robust/coverage_heatmap.png','Coverage: green observed / red missing'),('ambiguity',run/'tinted_robust/ambiguous_mask.png','Ambiguity: white = review required'),('uv_anisotropy',target/'uv_anisotropy.png','UV anisotropy heatmap'),('uv_density',target/'uv_density.png','UV density heatmap')]:
                save_mode(key,title,np.asarray(Image.open(source).convert('RGB')))
            shutil.copyfile(run/'comparison.jpg',target/'comparison.jpg')
            write_json(target/'stress_report.json',result); write_json(target/'roundtrip_report.json',rt)
            r['skinTriangles']=result['skin_triangles']
            r['coverage']={k:rt['results'][k]['projection_coverage'] for k in ('front_only','multiview')}
            r['stress']={'mae':result['paired_weighted_mae_srgb_255'],'coverage':{k:v['coverage'] for k,v in result['results'].items()},'ambiguity':{k:v['consensus']['ambiguous_texels'] for k,v in result['results'].items() if v.get('consensus')},'flaggedViews':[v['id'] for v in result['results']['tinted_robust']['views'] if v.get('inspect_view')],'corruption':result['corruption']}
            r['holdoutAngles']=rt['heldout_angles']; r['status']='B1_DIAGNOSTIC_COMPLETE'; r['comparison']='projection-lab/comparison.jpg'; r['comparisonSha256']=sha(target/'comparison.jpg')
            r['reports'].update(stress='projection-lab/stress_report.json',roundtrip='projection-lab/roundtrip_report.json')
            overview(overview_path,r,target/'comparison.jpg')
    except Exception as exc:
        print(f'Projection lab blocked: {type(exc).__name__}: {exc}',file=sys.stderr)
        # Retain exact UV reports and heatmaps when a gate fails. Remove only
        # partial display assets so a failed build cannot expose stale modes.
        for partial in list(target.glob('*.webp'))+list(target.glob('comparison.jpg')):
            partial.unlink()
        r.update(status='BLOCKED',reason=f'{type(exc).__name__}: {exc}',modes=[])
        for k in ('comparison','comparisonSha256','stress','coverage'): r.pop(k,None)
        overview(overview_path,r)
    write_json(output/'reports/projection_lab.json',r)
    print(f"Photoreal projection lab: {r['status']}")
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mesh',type=Path,default=ROOT/'assets/examples/photoreal-head/model/projection-head.glb');p.add_argument('--output',type=Path,default=ROOT/'assets/examples/photoreal-head');p.add_argument('--overview',type=Path,default=ROOT/'assets/skill-overviews/photoreal-head-web-v311.svg');p.add_argument('--skill',type=Path,default=SKILL);p.add_argument('--size',type=int,default=512);p.add_argument('--view-size',type=int,default=512);p.add_argument('--material');p.add_argument('--label',default=SCAN);p.add_argument('--strict',action='store_true');p.add_argument('--baseline',type=Path);p.add_argument('--preparation',type=Path);a=p.parse_args()
    if a.mesh.resolve()==ROOT/'assets/examples/photoreal-head/model/projection-head.glb':
        a.baseline=a.baseline or ROOT/'assets/examples/photoreal-head/model/head.glb'
        a.preparation=a.preparation or ROOT/'assets/examples/photoreal-head/reports/atlas_preparation.json'
    r=build(a.mesh,a.output,a.overview,a.size,a.view_size,a.skill,a.material,a.label,a.baseline,a.preparation)
    if a.strict and r['status']!='B1_DIAGNOSTIC_COMPLETE':sys.exit(1)
