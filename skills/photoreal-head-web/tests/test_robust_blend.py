"""Tests for the v3.1.1 consensus and ambiguity evidence contract."""
import json, tempfile, unittest, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from robust_texture_blend import robust_blend
from project_face_texture import project, sha, srgb_to_linear, linear_to_srgb
from compose_skin_atlas import compose
from test_surface_tools import glb


def fixture(colors, weights=None):
    linear=srgb_to_linear(np.array(colors,dtype=float)/255.)
    w=np.ones(len(colors)) if weights is None else np.asarray(weights,dtype=float)
    records=[(np.array([0],np.int32),a[None].astype(np.float32),np.array([b],np.float32)) for a,b in zip(linear,w)]
    return robust_blend(records,(linear*w[:,None]).sum(0)[None],np.array([w.sum()]),np.array([len(w)]))


class ConsensusTests(unittest.TestCase):
    def test_outlier_even_if_heavily_weighted(self):
        rgb,rejected,ambiguous,_,eligible,by_view=fixture([[180,130,100],[181,131,100],[240,85,60]],[1,1,100])
        self.assertEqual(rejected[0],1);self.assertFalse(ambiguous[0]);self.assertEqual(by_view.tolist(),[0,0,1]);self.assertEqual(eligible.tolist(),[1,1,1]);self.assertAlmostEqual(linear_to_srgb(rgb[0])[0]*255,180.5,places=2)
    def test_two_conflicting_views_are_not_rejected(self):
        _,rejected,ambiguous,*_=fixture([[180,130,100],[240,85,60]])
        self.assertTrue(ambiguous[0]);self.assertEqual(rejected[0],0)
    def test_no_majority_stays_ambiguous(self):
        _,rejected,ambiguous,*_=fixture([[30,40,50],[110,120,130],[220,230,240]])
        self.assertTrue(ambiguous[0]);self.assertEqual(rejected[0],0)
    def test_clean_and_single_view(self):
        for colors in ([[180,130,100]],[[180,130,100],[181,130,100],[182,130,100]]):
            _,rejected,ambiguous,*_=fixture(colors);self.assertEqual(rejected[0],0);self.assertFalse(ambiguous[0])
    def test_order_independent_without_exposure_matching(self):
        colors=[[180,130,100],[181,130,100],[240,85,60]];a=fixture(colors)[0];b=fixture(colors[::-1])[0];self.assertTrue(np.allclose(a,b,atol=1e-7))
    def test_report_masks_duplicate_and_composition(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp);mesh=d/'head.glb';glb(mesh);Image.new('L',(128,128),255).save(d/'mask.png')
            v={'id':'front','image':'a.png','mask':'mask.png','rectified':True,'role':'train','K':[[100,0,63.5],[0,100,63.5],[0,0,1]],'R':[[1,0,0],[0,-1,0],[0,0,-1]],'t':[-.5,.5,1.5]}
            Image.new('RGB',(128,128),(180,130,100)).save(d/'a.png');Image.new('RGB',(128,128),(240,85,60)).save(d/'b.png')
            m={'diagnostic_mode':True,'mesh':'head.glb','mesh_sha256':sha(mesh),'skin_material':'Skin','views':[v,{**v,'id':'second','image':'b.png'}],'blend_mode':'robust_consensus'}
            p=d/'manifest.json';p.write_text(json.dumps(m));o=d/'out';r=project(p,o,128)
            self.assertTrue(r['consensus']['review_required']);self.assertGreater(r['consensus']['ambiguous_texels'],0);self.assertEqual(r['consensus']['rejected_samples'],0);self.assertEqual(sha(o/'ambiguous_mask.png'),r['consensus']['ambiguous_mask_sha256'])
            Image.new('RGB',(128,128),(180,130,100)).save(d/'fallback.png')
            with self.assertRaisesRegex(ValueError,'reviewed ambiguity'):compose(o,d/'composed',d/'fallback.png','fixture')
            c=compose(o,d/'composed',d/'fallback.png','fixture',ambiguity_review_note='Synthetic fixture only; draft')
            self.assertEqual(c['ambiguous_texels'],r['consensus']['ambiguous_texels']);self.assertTrue((d/'composed/ambiguous_mask.png').exists())
            Image.new('L',(128,128),0).save(o/'ambiguous_mask.png')
            with self.assertRaisesRegex(ValueError,'Stale ambiguity'):compose(o,d/'composed',d/'fallback.png','fixture',ambiguity_review_note='draft')
            m['views'][1]['image']='a.png';p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'Duplicate training image'):project(p,d/'dup',128)


if __name__=='__main__':unittest.main()
