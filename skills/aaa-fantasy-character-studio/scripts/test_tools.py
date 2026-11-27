"""Synthetic fixtures only; these tests do not create or certify a character."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from gate import ROLES, run
from inspect_glb import inspect


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'evidence').mkdir()
        for stage, roles in ROLES.items():
            candidate = self.root / (stage + ('.zip' if stage == 'G11' else '.fixture'))
            if stage == 'G11':
                with ZipFile(candidate,'w') as z:
                    z.writestr('fixture.txt','synthetic only')
            else:
                candidate.write_text('synthetic candidate')
            files = {}
            for role in roles.split():
                p = self.root / f'{stage}-{role}.fixture'
                p.write_text('synthetic evidence')
                files[role] = p.name
            self.write(stage,dict(stage=stage,candidate=candidate.name,author='a',reviewer='b',reviewer_type='AI',decision='PASS',findings='synthetic test only',evidence=files))
    def tearDown(self):
        self.tmp.cleanup()
    def write(self,stage,data):
        (self.root/'evidence'/f'{stage}.json').write_text(json.dumps(data))
    def read(self,stage):
        return json.loads((self.root/'evidence'/f'{stage}.json').read_text())
    def seal_all(self):
        for stage in ROLES:
            run(self.root,stage)
    def test_chain_mutation(self):
        self.seal_all()
        self.assertEqual(run(self.root),'PASS_EVIDENCE_INTEGRITY_ONLY')
        (self.root/'G6.fixture').write_text('changed')
        with self.assertRaisesRegex(ValueError,'G6: missing/stale'):
            run(self.root)
        run(self.root,'G6')
        with self.assertRaisesRegex(ValueError,'G7: missing/stale'):
            run(self.root)
    def test_release_mutation(self):
        self.seal_all()
        with ZipFile(self.root/'G11.zip','a') as z:
            z.writestr('more.txt','changed')
        with self.assertRaisesRegex(ValueError,'G11: missing/stale'):
            run(self.root)
    def test_no_skip(self):
        with self.assertRaisesRegex(ValueError,'G0: missing/stale'):
            run(self.root,'G1')
    def test_self_review(self):
        d=self.read('G0');d['reviewer']='A';self.write('G0',d)
        with self.assertRaisesRegex(ValueError,'reviewer must differ'):
            run(self.root,'G0')
    def test_missing_role(self):
        d=self.read('G0');del d['evidence']['reference'];self.write('G0',d)
        with self.assertRaisesRegex(ValueError,'roles missing'):
            run(self.root,'G0')
    def test_path_escape(self):
        d=self.read('G0');d['candidate']='../outside';self.write('G0',d)
        with self.assertRaisesRegex(ValueError,'unsafe artifact'):
            run(self.root,'G0')
    def test_fail_review(self):
        d=self.read('G0');d['decision']='FAIL';self.write('G0',d)
        with self.assertRaisesRegex(ValueError,'missing PASS'):
            run(self.root,'G0')
    def test_release_requires_zip(self):
        for stage in list(ROLES)[:-1]:
            run(self.root,stage)
        d=self.read('G11');d['candidate']='G0.fixture';self.write('G11',d)
        with self.assertRaisesRegex(ValueError,'delivery ZIP'):
            run(self.root,'G11')
    def test_circular_release(self):
        for stage in list(ROLES)[:-1]:
            run(self.root,stage)
        with ZipFile(self.root/'G11.zip','a') as z:
            z.writestr('evidence/G11.json','circular')
        with self.assertRaisesRegex(ValueError,'circular'):
            run(self.root,'G11')


class GlbTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'fixture.glb'
        self.doc={'asset':{'version':'2.0'},'accessors':[{'count':3}]*5,'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2,'JOINTS_0':3,'WEIGHTS_0':4}}]}],'nodes':[{'mesh':0,'skin':0},{}],'skins':[{'joints':[1]}]}
    def tearDown(self):
        self.tmp.cleanup()
    def save(self):
        data=json.dumps(self.doc).encode();data+=b' '*((-len(data))%4)
        self.path.write_bytes(struct.pack('<4sIIII',b'glTF',2,len(data)+20,len(data),0x4E4F534A)+data)
    def test_metadata(self):
        self.save(); r=inspect(self.path,True,1)
        self.assertEqual((r['unique_mesh_triangles'],r['rigged_nodes']),(1,1))
    def test_budget(self):
        self.save()
        with self.assertRaisesRegex(ValueError,'budget'):
            inspect(self.path,max_triangles=0)
    def test_missing_skin(self):
        del self.doc['nodes'][0]['skin'];self.save()
        with self.assertRaisesRegex(ValueError,'no declared skinned'):
            inspect(self.path,True)
    def test_missing_weights(self):
        del self.doc['meshes'][0]['primitives'][0]['attributes']['WEIGHTS_0'];self.save()
        with self.assertRaisesRegex(ValueError,'lacks weights'):
            inspect(self.path,True)
    def test_invalid_header(self):
        self.path.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'header'):
            inspect(self.path)
    def test_instances(self):
        self.doc['nodes'].append({'mesh':0});self.save()
        with self.assertRaisesRegex(ValueError,'budget'):
            inspect(self.path,max_triangles=1)


if __name__=='__main__':
    unittest.main()
