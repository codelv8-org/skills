#!/usr/bin/env python3
"""Synthetic regression tests; never use these fixtures as production evidence."""
import copy
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_head_surface as qa
import regionalize_skin as rs

P=np.array([[[0,0,0],[1,0,0],[0,1,0]],[[1,1,0],[0,1,0],[1,0,0]]],float)
U=np.array([[[.1,.1],[.9,.1],[.1,.9]],[[.9,.9],[.1,.9],[.9,.1]]],float)


def glb(path,uv=U,metal=0,include_maps=True):
    blob=bytearray(); views=[]; acc=[]
    def view(data):
        while len(blob)%4: blob.append(0)
        i=len(views); views.append({'buffer':0,'byteOffset':len(blob),'byteLength':len(data)}); blob.extend(data); return i
    def accessor(array,type_):
        i=len(acc); acc.append({'bufferView':view(np.asarray(array,dtype='<f4').tobytes()),'componentType':5126,'count':len(array),'type':type_}); return i
    pos=accessor(P.reshape(-1,3),'VEC3'); tex=accessor(uv.reshape(-1,2),'VEC2'); norm=accessor(np.tile([0,0,1],(6,1)),'VEC3')
    images=[]; textures=[]; material={'name':'Skin','pbrMetallicRoughness':{'metallicFactor':1.0}}
    if include_maps:
        for color in [(185,141,116),(128,128,255),(255,125,metal)]:
            buf=io.BytesIO(); Image.new('RGB',(32,32),color).save(buf,format='PNG'); images.append({'bufferView':view(buf.getvalue()),'mimeType':'image/png'}); textures.append({'source':len(images)-1})
        material['pbrMetallicRoughness'].update(baseColorTexture={'index':0},metallicRoughnessTexture={'index':2}); material['normalTexture']={'index':1}
    while len(blob)%4: blob.append(0)
    doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':acc,'materials':[material],'images':images,'textures':textures,'meshes':[{'primitives':[{'attributes':{'POSITION':pos,'TEXCOORD_0':tex,'NORMAL':norm},'material':0}]}],'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0}
    j=json.dumps(doc).encode(); j+=b' '*((-len(j))%4); b=bytes(blob)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(b))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(b),b'BIN\0')+b)

class UVTests(unittest.TestCase):
    def test_shared_edge_not_overlap(self):
        s,e,_,_=qa.measure(P,U,'ccw'); self.assertFalse(e); self.assertEqual(s['overlap_pairs_found'],0); self.assertAlmostEqual(s['anisotropy_p95'],1)
    def test_identical_overlap_blocks(self):
        u=U.copy(); u[1]=u[0]; s,e,_,_=qa.measure(P,u,'ccw'); self.assertIn('overlap_pairs_found',e); self.assertEqual(s['overlap_pairs_found'],1)
    def test_partial_overlap_blocks(self):
        u=U.copy(); u[1]-=.05; s,e,_,_=qa.measure(P,u,'ccw'); self.assertIn('overlap_pairs_found',e)
    def test_flip_blocks(self):
        u=U.copy(); u[0]=u[0,::-1]; s,e,_,_=qa.measure(P,u,'ccw'); self.assertIn('wrong_winding',e)
    def test_degenerate_and_bounds(self):
        u=U.copy(); u[0,1]=u[0,0]; u[1,0]=[1.1,1.1]; s,e,_,_=qa.measure(P,u,'ccw'); self.assertIn('degenerate',e); self.assertIn('out_of_bounds',e)
    def test_stretch_blocks(self):
        u=U.copy(); u[:,:,0]*=.03; s,e,_,_=qa.measure(P,u,'ccw'); self.assertIn('anisotropy threshold',e)
    def test_nonfinite_blocks(self):
        u=U.copy();u[0,0,0]=float('nan'); self.assertRaises(ValueError,qa.measure,P,u,'ccw')
    def test_registration_shift(self):
        a={(0,0):U}; lm={k:{'mesh':0,'primitive':0,'triangle':0,'barycentric':[1,0,0],'texture_uv':[.1,.1]} for k in qa.LANDMARKS}; lm['ex_r'].update(barycentric=[0,1,0],texture_uv=[.9,.1]); _,e=qa.registration(a,lm,.01); self.assertFalse(e); lm['prn']['texture_uv']=[.2,.1]; _,e=qa.registration(a,lm,.01); self.assertTrue(any('prn' in x for x in e)); del lm['prn']; _,e=qa.registration(a,lm,.01); self.assertTrue(e)

class GLBTests(unittest.TestCase):
    def test_numeric_and_heatmaps(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.glb';glb(p);r=qa.validate(p,'Skin','ccw',report_dir=Path(td)/'qa');self.assertEqual(r['status'],'PASS_NUMERIC_ONLY');self.assertTrue((Path(td)/'qa/uv_anisotropy.png').exists())
    def test_metallic_block(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.glb';glb(p,metal=128);r=qa.validate(p,'Skin','ccw');self.assertEqual(r['status'],'BLOCKED');self.assertIn('Skin effective metallic must be zero',r['errors'])
    def test_uv_only_without_maps(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.glb';glb(p,include_maps=False);self.assertEqual(qa.validate(p,'Skin','ccw',uv_only=True)['status'],'PASS_UV_ONLY');self.assertRaises(ValueError,qa.validate,p,'Skin','ccw')
    def test_blank_manifest_and_stale_hash_block(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.glb';glb(p);m=Path(td)/'manifest.json';m.write_text('{}');r=qa.validate(p,'Skin','ccw',m);self.assertEqual(r['status'],'BLOCKED');self.assertTrue(any('candidate_sha256' in e for e in r['errors']))
    def test_no_promotion_without_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);p=d/'a.glb';glb(p);result=subprocess.run([sys.executable,qa.__file__,str(p),'--skin-material','Skin','--winding','ccw','--report-dir',str(d/'qa'),'--promote',str(d/'release.glb')],capture_output=True);self.assertNotEqual(result.returncode,0);self.assertFalse((d/'release.glb').exists())

    def test_exact_candidate_promotion_and_stale_hash(self):
        # Synthetic evidence ONLY for exercising the state machine, never a real asset review.
        with tempfile.TemporaryDirectory() as td:
            d=Path(td); p=d/'a.candidate.glb'; glb(p); r=qa.validate(p,'Skin','ccw'); _,_,_,_,_,a,_=qa.load_skin(p,'Skin')
            uv=a[(0,0)][0]; lm={k:{'mesh':0,'primitive':0,'triangle':0,'barycentric':[1,0,0],'texture_uv':uv[0].tolist()} for k in qa.LANDMARKS}
            lm['ex_r'].update(barycentric=[0,1,0],texture_uv=uv[1].tolist())
            doc={k:r[k] for k in ['candidate_sha256','uv_sha256','skin_material','winding']}; doc.update(atlas_id='synthetic',source_license='synthetic',texture_provenance='synthetic',inferred_regions='synthetic',reviewer='TEST ONLY',semantic_alignment_reviewed=True,seam_padding_reviewed=True,color_normal_reviewed=True,landmarks=lm,reviews={})
            for i,k in enumerate(qa.REVIEWS):
                f=d/(k+'.png'); Image.new('RGB',(8,8),(i,0,0)).save(f); doc['reviews'][k]={'file':f.name,'sha256':qa.digest(f),'reviewed':True,'notes':'synthetic fixture, not visual proof'}
            m=d/'manifest.json'; m.write_text(json.dumps(doc)); e=d/'export.json'; e.write_text(json.dumps({'status':'CANDIDATE_NEEDS_SURFACE_QA','glb_sha256':qa.digest(p),'release_mode':True,'manual_anatomy_review_declared':True}))
            base=[sys.executable,qa.__file__,str(p),'--skin-material','Skin','--winding','ccw','--report-dir',str(d/'qa'),'--manifest',str(m),'--anatomy-export-report',str(e),'--promote']
            out=d/'approved.glb'; result=subprocess.run(base+[str(out)],capture_output=True); self.assertEqual(result.returncode,0,result.stderr.decode()); self.assertEqual(p.read_bytes(),out.read_bytes())
            doc['candidate_sha256']='stale';m.write_text(json.dumps(doc));bad=d/'bad.glb'; result=subprocess.run(base+[str(bad)],capture_output=True);self.assertNotEqual(result.returncode,0);self.assertFalse(bad.exists())

class RegionTests(unittest.TestCase):
    def test_region_masks_and_metal_channel(self):
        with tempfile.TemporaryDirectory() as td:
            doc={'coordinate_space':'gltf_uv_top_left','atlas_id':'synthetic-test','uv_sha256':'test','regions':{k:[[[i/11,0],[(i+1)/11,0],[(i+1)/11,1],[i/11,1]]] for i,k in enumerate(rs.PROFILES)}}
            out=Path(td);rs.generate(doc,Image.new('RGB',(128,128),(140,118,253)),Image.new('L',(128,128),128),out,0,1)
            packed=np.array(Image.open(out/'regional_metallicroughness.png'));self.assertTrue(np.all(packed[:,:,2]==0));self.assertGreater(packed[:,:,1].std(),1)
            n=np.array(Image.open(out/'regional_micro_normal_opengl.png')); i=list(rs.PROFILES).index('lips');self.assertTrue(np.all(abs(n[:,int((i+.5)*128/11),:2].astype(int)-128)<=1)); self.assertTrue((out/'region_coverage.png').exists())

if __name__=='__main__':unittest.main()
