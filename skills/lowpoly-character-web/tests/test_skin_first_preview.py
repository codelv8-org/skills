"""v2 regression checks: true skin requirement, continuity and website packaging."""
from pathlib import Path
import sys
import tempfile
import unittest
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_preview_site import build
from inspect_skinning import inspect


class SkinFirstPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.model=Path(cls.temp.name)/'skinned_demo.glb'
        from generate_skin_demo import export_demo
        cls.manifest=export_demo(cls.model,step=.047)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_skinned_demo_is_a_real_single_surface(self):
        r=inspect(self.model,required_clips=['Idle','Walk','Run','Salute'])
        self.assertEqual(r['status'],'PASS',r['errors'])
        self.assertEqual(r['skin_count'],1)
        self.assertEqual(len(r['skinned_primitives']),1)
        self.assertEqual(r['skinned_primitives'][0]['connected_components'],1)
        self.assertGreater(r['blended_ratio'],.2)
        self.assertEqual(r['animated_skin_joints'],9)
        self.assertEqual([x['name'] for x in r['clips']],['Idle','Walk','Run','Salute'])

    def test_skinless_animated_asset_fails(self):
        from generate_blockout import build as static_build
        cfg=json.loads((ROOT/'assets/templates/character_spec.json').read_text())
        scene,_=static_build(cfg)
        static_path=Path(self.temp.name)/'static.glb'
        static_path.write_bytes(scene.export(file_type='glb',include_normals=True))
        r=inspect(static_path,required_clips=['Idle'])
        self.assertEqual(r['status'],'FAIL')
        self.assertIn('RIGID_OR_STATIC',r['rig_classification'])
        self.assertTrue(any('No skin' in e for e in r['errors']))

    def test_missing_named_clip_fails(self):
        r=inspect(self.model,required_clips=['Dance'])
        self.assertEqual(r['status'],'FAIL')
        self.assertIn('Missing required animation clip Dance',r['errors'])

    def test_preview_contains_actual_glb_and_no_network_dependencies(self):
        out=Path(self.temp.name)/'preview'
        r=build(self.model,out)
        self.assertEqual((out/'model.glb').read_bytes(),self.model.read_bytes())
        self.assertIn('skinned demo',(out/'index.html').read_text())
        self.assertTrue(all((out/x).exists() for x in ('index.html','style.css','viewer.js','preview_manifest.json')))
        self.assertNotIn('https://',(out/'index.html').read_text())
        self.assertEqual(r['model_bytes'],self.model.stat().st_size)

    def test_invalid_model_rejected(self):
        with self.assertRaises(FileNotFoundError):
            build(Path(self.temp.name)/'missing.glb',Path(self.temp.name)/'web')

    def test_weight_corruption_detected(self):
        from inspect_skinning import parse
        doc,raw=parse(self.model)
        ix=doc['meshes'][0]['primitives'][0]['attributes']['WEIGHTS_0']
        a=doc['accessors'][ix];v=doc['bufferViews'][a['bufferView']]
        import struct
        blob=bytearray(self.model.read_bytes())
        jl=struct.unpack_from('<I',blob,12)[0]
        blob_offset=12+8+jl+8
        o=blob_offset+v.get('byteOffset',0)+a.get('byteOffset',0)
        struct.pack_into('<f',blob,o,3.0)
        corrupted=Path(self.temp.name)/'corrupt.glb';corrupted.write_bytes(blob)
        r=inspect(corrupted)
        self.assertEqual(r['status'],'FAIL')
        self.assertTrue(any('sum' in e for e in r['errors']))

if __name__=='__main__':unittest.main()
