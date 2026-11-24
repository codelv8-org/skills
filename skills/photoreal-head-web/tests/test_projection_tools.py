"""Regression fixtures for calibrated projection; NOT real-photo evidence."""
import json,tempfile,unittest,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_surface_tools import glb,U
from project_face_texture import project,sha,raster,fit_pose,project_points,srgb_to_linear,linear_to_srgb
from evaluate_photo_holdout import evaluate
from compose_skin_atlas import compose

class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.mesh=self.d/'head.glb';glb(self.mesh);self.path=self.d/'manifest.json'
        Image.new('RGB',(128,128),(180,130,100)).save(self.d/'front.png');Image.new('L',(128,128),255).save(self.d/'mask.png')
        self.view={'id':'front','image':'front.png','mask':'mask.png','rectified':True,'role':'train','K':[[100,0,63.5],[0,100,63.5],[0,0,1]],'R':[[1,0,0],[0,-1,0],[0,0,-1]],'t':[-.5,.5,1.5]}
        self.m={'diagnostic_mode':True,'mesh':'head.glb','mesh_sha256':sha(self.mesh),'skin_material':'Skin','views':[self.view],'min_view_cosine':.25,'depth_tolerance_m':.001,'mask_feather_px':2}
    def tearDown(self):self.tmp.cleanup()
    def run_projection(self):
        self.path.write_text(json.dumps(self.m));return project(self.path,self.d/'out',128)
    def test_color_and_alpha(self):
        r=self.run_projection();self.assertGreater(r['coverage'],.85);a=np.asarray(Image.open(self.d/'out/projected_rgba.png'));self.assertTrue(np.all(a[a[:,:,3]>0,:3]==[180,130,100]));self.assertTrue((a[:,:,3]==0).any())
    def test_mask_no_observations(self):
        Image.new('L',(128,128),0).save(self.d/'mask.png');r=self.run_projection();self.assertEqual(r['coverage'],0);self.assertEqual(r['status'],'DRAFT_PROJECTION')
    def test_production_requires_rights_and_uv_qa(self):
        self.m['diagnostic_mode']=False;self.assertRaisesRegex(ValueError,'source rights',self.run_projection)
        self.m.update(rights_verified=True,source_provenance='synthetic test',uv_qa_report='uv.json');(self.d/'uv.json').write_text(json.dumps({'candidate_sha256':sha(self.mesh),'skin_material':'Skin','status':'BLOCKED','errors':['wrong_winding']}));self.assertRaisesRegex(ValueError,'exact UV QA',self.run_projection)
    def test_stale_mesh(self):
        self.m['mesh_sha256']='wrong';self.assertRaisesRegex(ValueError,'hash mismatch',self.run_projection)
    def test_unobserved_fallback_must_be_explicit(self):
        Image.new('L',(128,128),0).save(self.d/'mask.png');r=self.run_projection();self.assertRaisesRegex(ValueError,'Unobserved skin',compose,self.d/'out',self.d/'composed');Image.new('RGB',(128,128),(110,90,70)).save(self.d/'fb.png');c=compose(self.d/'out',self.d/'composed',self.d/'fb.png','synthetic fixture');self.assertEqual(c['inferred_texels'],r['atlas_texels'])
    def test_holdout_leakage(self):
        self.run_projection();self.view['role']='holdout';self.path.write_text(json.dumps(self.m));self.assertRaisesRegex(ValueError,'leakage',evaluate,self.path,[self.d/'out'],self.d/'eval')
    def test_holdout_metrics(self):
        self.run_projection();Image.new('RGB',(128,128),(181,130,100)).save(self.d/'hold.png');self.view.update(role='holdout',image='hold.png');self.m['min_skin_mask_iou']=.2;self.path.write_text(json.dumps(self.m));r=evaluate(self.path,[self.d/'out'],self.d/'eval');result=r['views'][0]['candidates']['out']['own_support'];self.assertGreater(result['coverage'],.8);self.assertAlmostEqual(result['mae_srgb_255'],1/3,places=3)
    def test_holdout_not_training(self):
        self.view['role']='holdout';self.assertRaisesRegex(ValueError,'Holdout',self.run_projection)
    def test_overlap_rejected(self):
        u=U.copy();u[1]=u[0];glb(self.mesh,u);self.m['mesh_sha256']=sha(self.mesh);self.assertRaisesRegex(ValueError,'UV overlap',self.run_projection)
    def test_exposure_matching(self):
        orig=srgb_to_linear(np.array([180,130,100])/255.);dim=np.uint8(np.rint(linear_to_srgb(orig*.8)*255));Image.new('RGB',(128,128),tuple(dim)).save(self.d/'dim.png');self.m['views'].append({**self.view,'id':'dim','image':'dim.png'});self.m['exposure_match']='overlap_scalar';r=self.run_projection();self.assertGreater(r['views'][1]['exposure_overlap_samples'],128);self.assertAlmostEqual(r['views'][1]['overlap_exposure_gain'],1.25,delta=.05)
    def test_depth_occlusion(self):
        xy=np.array([[[3.,3.],[12.,3.],[3.,12.]],[[3.,3.],[12.,3.],[3.,12.]]]);z=np.array([[2.,2.,2.],[1.,1.,1.]]);ids,depth,_,_=raster(xy,z,16,16,True);self.assertEqual(ids[5,5],1);self.assertAlmostEqual(depth[5,5],1.)
    def test_pnp_independent_validation(self):
        rng=np.random.default_rng(8);p=rng.uniform(-.10,.10,(16,3));K=np.array([[900.,0,500],[0,900,400],[0,0,1.]]);R=np.eye(3);t=np.array([0.,0.,.6]);xy,_=project_points(p,K,R,t);lm=[{'xyz':x.tolist(),'xy':y.tolist()} for x,y in zip(p,xy)];doc={'fit':lm[:12],'validate':lm[12:]};rr,tt,r=fit_pose(K,doc,.2);self.assertLess(r['validation_rmse_px'],.01);self.assertTrue(np.allclose(tt,t,atol=1e-4));doc['validate'][0]['xy'][0]+=10;self.assertRaisesRegex(ValueError,'Independent pose validation failed',fit_pose,K,doc,.2)

if __name__=='__main__':unittest.main()
