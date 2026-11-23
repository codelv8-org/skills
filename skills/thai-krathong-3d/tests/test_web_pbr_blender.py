"""Real Cycles bake and corruption/overwrite tests; run in background Blender.

Optional -- --out-dir PATH retains fixture, maps, GLBs, reports and logs.
Without it a temporary directory is used. Requires no external Python packages.
"""
from array import array
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import bpy
from check_reference_model import _read_glb, check


def pixels(path):
    img = bpy.data.images.load(str(path), check_existing=False)
    img.colorspace_settings.name = "Non-Color"
    values = array('f', [0])*(img.size[0]*img.size[1]*4)
    img.pixels.foreach_get(values)
    bpy.data.images.remove(img)
    return values


def mutate_glb(source, target, mutate):
    raw = source.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+length])
    mutate(doc)
    payload = json.dumps(doc, separators=(',', ':')).encode()
    payload += b' '*((-len(payload))%4)
    tail = raw[20+length:]
    target.write_bytes(struct.pack('<4sII', b'glTF', 2, 20+len(payload)+len(tail))+
                       struct.pack('<II', len(payload), 0x4E4F534A)+payload+tail)


def fixture(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Krathong_Asset")
    bpy.context.scene.collection.children.link(col)
    # Test bake machinery independently of the krathong geometry generators.
    bpy.ops.mesh.primitive_cube_add(size=.26)
    obj = bpy.context.object
    for c in list(obj.users_collection): c.objects.unlink(obj)
    col.objects.link(obj)
    mat=bpy.data.materials.new("Spatial_PBR_Fixture");mat.use_nodes=True
    obj.data.materials.append(mat)
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    bsdf=nodes.get('Principled BSDF')
    coords=nodes.new('ShaderNodeTexCoord')
    noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=9
    links.new(coords.outputs['UV'],noise.inputs['Vector'])
    links.new(noise.outputs['Color'],bsdf.inputs['Base Color'])
    links.new(noise.outputs['Fac'],bsdf.inputs['Roughness'])
    links.new(noise.outputs['Fac'],bsdf.inputs['Metallic'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.01
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    bpy.ops.wm.save_as_mainfile(filepath=str(path),check_existing=False)


class WebPBRTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = OUTPUT
        cls.source = cls.path/'source.blend'
        fixture(cls.source)
        cls.digest=hashlib.sha256(cls.source.read_bytes()).hexdigest()
        cls.out=cls.path/'baked'
        cls.command=[bpy.app.binary_path,'--background','--factory-startup','--python-exit-code','1',
                     '--python',str(ROOT/'scripts/bake_web_pbr.py'),'--','--input',str(cls.source),
                     '--out-dir',str(cls.out),'--resolution','256','--samples','4','--margin','2']
        run=subprocess.run(cls.command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        (cls.path/'bake.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:
            raise AssertionError('Real fixture bake failed; see '+str(cls.path/'bake.log'))

    def test_bake_success_and_source_preserved(self):
        report=json.loads((self.out/'web-pbr-report.json').read_text())
        self.assertTrue(report['passed']);self.assertTrue(report['input_unchanged'])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.digest)
        self.assertEqual(len(report['bakes']),5)

    def test_pixel_content_and_orm_channels(self):
        raw={n:pixels(self.out/(n+'.png')) for n in ('BaseColor','Normal','AO','Roughness','Metallic','ORM')}
        # Procedural metallic and roughness must survive as spatial maps, not
        # scalar defaults. Normal bake must capture non-flat micro-surface.
        for name in ('BaseColor','Normal','Roughness','Metallic'):
            self.assertGreater(max(raw[name][0::4])-min(raw[name][0::4]),.01,name)
        for channel,name in enumerate(('AO','Roughness','Metallic')):
            error=max(abs(a-b) for a,b in zip(raw['ORM'][channel::4],raw[name][0::4]))
            self.assertLessEqual(error,1/255+.0001,name)
        self.assertTrue(all(0 <= v <= 1 for v in raw['Normal']))

    def test_embedded_export_pixels_and_roundtrip(self):
        path=self.out/'krathong-web.glb'
        r=check(path,web_pbr=True)
        self.assertTrue(r['passed'],r['errors'])
        self.assertEqual(r['source_glb']['embedded_images'],3)
        self.assertEqual(r['source_glb']['mesh_primitives'],1)
        doc,_,_=_read_glb(path)
        data=path.read_bytes();jl=struct.unpack_from('<I',data,12)[0];binary=data[28+jl:]
        mat=doc['materials'][0]
        texs={'BaseColor':mat['pbrMetallicRoughness']['baseColorTexture'], 'Normal':mat['normalTexture'],
              'ORM':mat['pbrMetallicRoughness']['metallicRoughnessTexture']}
        for name,info in texs.items():
            image=doc['images'][doc['textures'][info['index']]['source']]
            view=doc['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0)
            extracted=self.path/('embedded-'+name+'.png')
            extracted.write_bytes(binary[offset:offset+view['byteLength']])
            a,b=pixels(extracted),pixels(self.out/(name+'.png'))
            self.assertEqual(len(a),len(b))
            self.assertLessEqual(max(abs(x-y) for x,y in zip(a,b)),1/255+.0001,name)

    def test_reject_missing_normal_in_real_glb(self):
        broken=self.path/'missing-normal.glb'
        mutate_glb(self.out/'krathong-web.glb',broken,lambda d:d['materials'][0].pop('normalTexture'))
        r=check(broken,web_pbr=True)
        self.assertFalse(r['passed']);self.assertTrue(any('Normal texture' in e for e in r['errors']))

    def test_reject_missing_uv_in_real_glb(self):
        broken=self.path/'missing-uv.glb'
        mutate_glb(self.out/'krathong-web.glb',broken,lambda d:d['meshes'][0]['primitives'][0]['attributes'].pop('TEXCOORD_0'))
        self.assertFalse(check(broken,web_pbr=True)['passed'])

    def test_reject_zero_tangent_in_real_glb(self):
        source=self.out/'krathong-web.glb'
        data=bytearray(source.read_bytes())
        doc,_,_=_read_glb(source)
        p=doc['meshes'][0]['primitives'][0]
        a=doc['accessors'][p['attributes']['TANGENT']]
        view=doc['bufferViews'][a['bufferView']]
        binary=28+struct.unpack_from('<I',data,12)[0]
        struct.pack_into('<fff',data,binary+view.get('byteOffset',0)+a.get('byteOffset',0),0,0,0)
        broken=self.path/'zero-tangent.glb';broken.write_bytes(data)
        r=check(broken,web_pbr=True)
        self.assertFalse(r['passed'])
        self.assertTrue(any('Non-unit exported TANGENT' in e for e in r['errors']))

    def test_refuse_overwrite(self):
        before=(self.out/'krathong-web.glb').read_bytes()
        run=subprocess.run(self.command,capture_output=True,timeout=60)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(before,(self.out/'krathong-web.glb').read_bytes())
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.digest)

    def test_unsupported_generated_coordinates_fail_without_source_changes(self):
        bpy.ops.wm.open_mainfile(filepath=str(self.source))
        mat=next(o for o in bpy.context.scene.objects if o.type=='MESH').data.materials[0]
        noise=next(n for n in mat.node_tree.nodes if n.type=='TEX_NOISE')
        mat.node_tree.links.remove(noise.inputs['Vector'].links[0])
        bad=self.path/'unsupported-source.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(bad),check_existing=False)
        before=bad.read_bytes()
        command=list(self.command)
        command[command.index('--input')+1]=str(bad)
        out=self.path/'unsupported-output'
        command[command.index('--out-dir')+1]=str(out)
        run=subprocess.run(command,capture_output=True,timeout=60)
        self.assertNotEqual(run.returncode,0)
        self.assertEqual(before,bad.read_bytes())
        report=json.loads((out/'web-pbr-report.json').read_text())
        self.assertFalse(report['passed'])
        self.assertIn('explicit UV coordinates',report['errors'][0])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    temporary=tempfile.TemporaryDirectory() if not args.out_dir else None
    OUTPUT=Path(args.out_dir if args.out_dir else temporary.name).resolve()
    if args.out_dir and OUTPUT.exists() and any(OUTPUT.iterdir()):
        parser.error('Test output directory must be empty/new')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WebPBRTests))
    if temporary:temporary.cleanup()
    if not result.wasSuccessful():raise SystemExit(1)
