"""v3 reference calibration, evidence scoring and crowd cost regression."""
from __future__ import annotations
import sys, tempfile, json
from pathlib import Path
from PIL import Image, ImageDraw
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reference_intake import create_pack
from reference_review import build_board, make_scorecard, score_review
from scene_budget import audit
from projected_lod import projected_height_px, lod_tier

class ReferenceBudgetTests(unittest.TestCase):
    def test_four_views_and_unverified_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);source=d/'sheet.png'
            im=Image.new('RGB',(400,200),'white')
            draw=ImageDraw.Draw(im)
            for i in range(4):draw.rectangle((i*100+25,20,i*100+75,175),fill=(40+i*40,30,50))
            im.save(source)
            pack=create_pack(d/'crop',sheet=source)
            self.assertEqual(set(pack['source_views']),{'front','back','left','right'})
            self.assertEqual(pack['view_camera_type'],'UNVERIFIED')
            self.assertIsNone(pack['character_height_m'])
            with Image.open(d/'crop/front.png') as sample:
                self.assertEqual(sample.size,(100,180))
            self.assertIn('sha256',pack['origin_files'][0])
            for view in pack['source_views']:
                self.assertTrue((d/'crop'/f'{view}.png').exists())
            with self.assertRaises(ValueError):create_pack(d/'bad',sheet=source,order=('front',)*4)

    def test_multiple_inputs_and_comparison_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);sources={}
            for i,name in enumerate(['front','back','left','right']):
                f=d/(name+'_input.png');Image.new('RGB',(60,100),(20+i*30,25,60)).save(f);sources[name]=f
            pack=create_pack(d/'ref', views=sources)
            render=d/'renders';render.mkdir()
            for name in sources:Image.new('RGBA',(70,105),(50,100,160,255)).save(render/(name+'.png'))
            build_board(d/'ref',render,d/'review.png',width=120,height=150)
            with Image.open(d/'review.png') as board:
                self.assertEqual(board.size,(480,404))
            self.assertEqual(pack['source_type'],'separate_view_images')

    def test_artist_review_cannot_auto_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            obj=make_scorecard(Path(tmp)/'score.json')
            self.assertEqual(score_review(obj)['status'],'REVIEW_REQUIRED')
            evidence=Path(tmp)/'provided-by-reviewer.png'
            Image.new('RGB',(8,8),'white').save(evidence)
            for check in obj['checks']:
                check['rating']=5
                check['evidence']='provided-by-reviewer.png'
            obj['reference_camera_alignment_verified']=True
            obj['artist_name_or_role']='Test reviewer'
            self.assertEqual(score_review(obj, Path(tmp))['status'],'PASS')
            obj['checks'][0]['rating']=2
            self.assertEqual(score_review(obj, Path(tmp))['status'],'REVIEW_REQUIRED')
            obj['checks'][0]['rating']=6
            self.assertEqual(score_review(obj, Path(tmp))['status'],'BLOCKED')
            obj['checks'][0]['rating']=5
            evidence.unlink()
            self.assertEqual(score_review(obj, Path(tmp))['status'],'REVIEW_REQUIRED')

    def test_projected_lod_is_camera_dependent(self):
        near=projected_height_px(1.7,2,50,900)
        far=projected_height_px(1.7,30,50,900)
        self.assertGreater(near,far)
        self.assertEqual(lod_tier(near),'HERO_LOD0')
        self.assertIn(lod_tier(far),('CROWD_LOD2','DISTANT_IMPOSTOR_OR_CULL'))
        with self.assertRaises(ValueError):projected_height_px(1.7,0,50,900)

    def test_portable_bundled_glb_is_auditable(self):
        source=ROOT/'assets/examples/skinned_demo.glb'
        self.assertTrue(source.is_file())
        r=audit(source,'hero',(1,10,30))
        self.assertGreater(r['asset']['triangles'],0)
        self.assertGreater(r['asset']['primitive_submissions'],0)
        self.assertEqual(r['scenarios'][2]['estimated_triangles'],r['asset']['triangles']*30)
        self.assertFalse(r['is_fps_measurement'])

    def test_real_existing_glb_budget_is_not_fps(self):
        candidate=Path('/mnt/data/sentinel_character/sentinel_s3_a_pose.glb')
        if not candidate.is_file():self.skipTest('Prior Sentinel example not mounted in this runtime')
        r=audit(candidate,'npc',(1,10,50))
        self.assertEqual(r['asset']['triangles'],9134)
        self.assertEqual(r['asset']['primitive_submissions'],17)
        self.assertEqual(r['scenarios'][2]['estimated_base_pass_primitive_draws'],850)
        self.assertEqual(r['status'],'REVIEW_REQUIRED')
        self.assertFalse(r['is_fps_measurement'])

if __name__=='__main__':unittest.main()
