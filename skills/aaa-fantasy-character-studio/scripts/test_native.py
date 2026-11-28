"""Regression tests for native compilation and actual binary geometry."""
import copy, json, struct, tempfile, unittest
from pathlib import Path
from native_mesh import compile_ir, mesh_part
from inspect_glb import inspect
from render_clay import read_native, render, png
from preflight import report

BASE=Path(__file__).resolve().parents[1]/'assets'
class NativeTests(unittest.TestCase):
    def setUp(self): self.ir=json.loads((BASE/'mesh-fixture.json').read_text())
    def compile(self):return compile_ir(self.ir,BASE)
    def test_deterministic_and_decode(self):
        raw,r=self.compile(); self.assertEqual(raw,self.compile()[0]);self.assertEqual(r['triangles'],18);self.assertEqual(r['vertices'],19);self.assertEqual(r['skinned_parts'],2)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'x.glb';p.write_bytes(raw);d=inspect(p,True);self.assertEqual(d['animations'],['fixture_bend']);self.assertEqual(d['unique_mesh_triangles'],18);self.assertEqual(d['warnings'],[])
            parts=read_native(p);self.assertEqual(sum(len(t) for _,t in parts),18)
        n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);data=raw[28+n:]
        for view in doc['bufferViews']:
            self.assertEqual(view['byteOffset']%4,0);self.assertLessEqual(view['byteOffset']+view['byteLength'],len(data))
        for m in doc['meshes']:
            a=doc['accessors'][m['primitives'][0]['attributes']['WEIGHTS_0']];v=doc['bufferViews'][a['bufferView']];offset=v['byteOffset']
            for row in struct.iter_unpack('<4f',data[offset:offset+v['byteLength']]):self.assertAlmostEqual(sum(row),1)
        a=doc['accessors'][doc['skins'][0]['inverseBindMatrices']];v=doc['bufferViews'][a['bufferView']];m=list(struct.iter_unpack('<16f',data[v['byteOffset']:v['byteOffset']+v['byteLength']]));self.assertAlmostEqual(m[1][13],-.5)
    def test_texture_embedding(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);png(p/'tex.png',2,2,bytes([128,128,128]*4));self.ir['materials'][0]['textures']={'base_color':'tex.png','orm':'tex.png'};raw,r=compile_ir(self.ir,p);self.assertEqual(r['embedded_images'],1);self.assertIn(b'\x89PNG\r\n\x1a\n',raw)
    def test_bad_weight(self):
        self.ir['parts'][0]['ring_weights'][0]={'root':.6};self.assertRaises(ValueError,self.compile)
    def test_bad_index(self):
        self.ir['parts'][1]['faces'][0][2]=99;self.assertRaises(ValueError,self.compile)
    def test_degenerate(self):
        self.ir['parts'][1]['positions'][1]=self.ir['parts'][1]['positions'][0];self.assertRaises(ValueError,self.compile)
    def test_bad_uv(self):
        self.ir['parts'][1]['uv'][0]=[2,0];self.assertRaises(ValueError,self.compile)
    def test_bad_joint(self):
        self.ir['joints'][1]['parent']='missing';self.assertRaises(ValueError,self.compile)
    def test_bad_animation(self):
        self.ir['animations'][0]['tracks'][0]['values'][1]=[0,0,0,2];self.assertRaises(ValueError,self.compile)
    def test_path_escape(self):
        self.ir['materials'][0]['textures']={'normal':'../SKILL.md'};self.assertRaises(ValueError,self.compile)
    def test_smooth_seam_and_render(self):
        p=mesh_part(self.ir['parts'][0]);self.assertEqual(p['normals'][0],p['normals'][4]);raw,_=self.compile()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'model.glb';path.write_bytes(raw);parts=read_native(path);img,coverage=render(parts,(0,0,1),(0,.5,0),80,128);self.assertGreater(coverage,100);self.assertEqual(len(img),128*128*3);png(Path(tmp)/'out.png',128,128,img);self.assertTrue((Path(tmp)/'out.png').read_bytes().startswith(b'\x89PNG'))
    def test_preflight_does_not_attest(self):
        r=report('PLATFORM_CLOUD','example');self.assertFalse(r['runtime_attested']);self.assertFalse(r['model_verified']);self.assertTrue(r['native_compiler'])
if __name__=='__main__':unittest.main()
