"""Executable smoke tests for the static blockout and structural inspector."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load_script(filename: str):
    spec=importlib.util.spec_from_file_location(filename[:-3],ROOT/'scripts'/filename)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class SkillToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator=load_script('generate_blockout.py')
        cls.inspector=load_script('inspect_character_glb.py')
        cls.tmp=tempfile.TemporaryDirectory()
        cls.path=Path(cls.tmp.name)/'sample.glb'
        cls.spec=json.loads((ROOT/'assets/templates/character_spec.json').read_text())
        cls.scene,cls.manifest=cls.generator.build(cls.spec)
        cls.path.write_bytes(cls.scene.export(file_type='glb',include_normals=True))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_real_glb_generated(self):
        data=self.path.read_bytes()
        self.assertEqual(data[:4],b'glTF')
        gltf,_=self.inspector.parse_glb(self.path)
        self.assertEqual(gltf['asset']['version'],'2.0')
        self.assertGreater(self.manifest['triangles'],100)
        self.assertEqual(len(gltf.get('skins',[])),0)
        self.assertEqual(len(gltf.get('animations',[])),0)
        self.assertEqual(self.manifest['glb_axes'].split(',')[0],'Y-up')

    def test_no_uv_is_valid_for_flat_palette(self):
        result=self.inspector.inspect(self.path,'balanced')
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['textured_primitives'],0)
        self.assertEqual(result['uv0_primitives'],0)
        self.assertGreater(result['materials'],2)
        self.assertEqual(result['triangles_instantiated'],self.manifest['triangles'])

    def test_rig_requirements_are_not_faked(self):
        result=self.inspector.inspect(self.path,require_skin=True,require_animations=True)
        self.assertEqual(result['status'],'FAIL')
        self.assertTrue(any('Rig requested' in msg for msg in result['errors']))
        self.assertTrue(any('Animations requested' in msg for msg in result['errors']))

    def test_budget_is_enforced(self):
        result=self.inspector.inspect(self.path,max_triangles=200)
        self.assertEqual(result['status'],'FAIL')
        self.assertTrue(any('Triangle budget exceeded' in e for e in result['errors']))

    def test_wrong_magic_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/'bad.glb'
            data=bytearray(self.path.read_bytes())
            data[:4]=b'WRNG'
            bad.write_bytes(data)
            with self.assertRaises(ValueError):
                self.inspector.parse_glb(bad)

    def test_reject_fake_rig_option(self):
        bad=dict(self.spec)
        bad['rig']='skinned'
        with self.assertRaises(ValueError):
            self.generator.build(bad)

    def test_invalid_color_rejected(self):
        with self.assertRaises(ValueError):
            self.generator.rgb('#GGGFFF')


if __name__=='__main__':
    unittest.main()
