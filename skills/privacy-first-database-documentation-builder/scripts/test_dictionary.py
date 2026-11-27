#!/usr/bin/env python3
"""Offline regression tests; use synthetic structures only."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from validate_metadata import Block, validate, load, effective_field, effective_object
from build_dictionary import Builder, generate, diff, MODES
from release_check import scan
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'assets'/'metadata-template.json'

class Tests(unittest.TestCase):
    def setUp(self): self.d=load(FIX)
    def reject(self, fn):
        fn(self.d)
        with self.assertRaises(Block): validate(self.d)
    def test_valid(self): self.assertEqual(validate(self.d),self.d)
    def test_unknown_key(self): self.reject(lambda d:d.update(sample_rows=[]))
    def test_defaults(self): self.reject(lambda d:d['objects'][0]['columns'][0].update(default_value=None))
    def test_comments(self): self.reject(lambda d:d['objects'][0]['columns'][0].update(column_comment=None))
    def test_approval(self): self.reject(lambda d:d['approval'].update(reviewed=False))
    def test_synthetic_status(self): self.reject(lambda d:d.update(status='verified'))
    def test_bad_source(self): self.reject(lambda d:d['objects'][0].update(source_id='missing'))
    def test_duplicate_object(self): self.reject(lambda d:d['objects'].append(copy.deepcopy(d['objects'][0])))
    def test_duplicate_column(self): self.reject(lambda d:d['objects'][0]['columns'].append(copy.deepcopy(d['objects'][0]['columns'][0])))
    def test_nullable_pk(self): self.reject(lambda d:d['objects'][0]['columns'][0].update(nullable=True))
    def test_bad_fk(self): self.reject(lambda d:d['objects'][1]['foreign_keys'][0].update(target_name='missing'))
    def test_nonunique_fk(self): self.reject(lambda d:d['objects'][1]['foreign_keys'][0].update(target_columns=['label']))
    def test_arity(self): self.reject(lambda d:d['objects'][1]['foreign_keys'][0].update(columns=['service_id','department_code']))
    def test_composite(self):
        self.d['objects'][0]['keys'][0]['columns']=['code','label']; self.d['objects'][0]['columns'][1].update(nullable=False,type='integer',length=None,precision=10,scale=0)
        f=self.d['objects'][1]['foreign_keys'][0]; f['columns']=['department_code','service_id']; f['target_columns']=['code','label']
        validate(self.d); self.assertIn(r'department\_code, service\_id',Builder(self.d).erd())
    def test_unknown_restricted(self):
        o=self.d['objects'][1]; self.assertEqual(effective_field(o['columns'][2],o),'Restricted'); self.assertEqual(effective_object(o),'Restricted')
    def test_missing_class_restricted(self):
        o=self.d['objects'][0]; del o['columns'][0]['classification']; validate(self.d); self.assertEqual(effective_field(o['columns'][0],o),'Restricted')
    def test_sensitive_label_floor(self):
        o=self.d['objects'][1]; o['columns'][2]['classification']='Public'; validate(self.d); self.assertEqual(effective_field(o['columns'][2],o),'Restricted')
    def test_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'input.json'; p.write_text('{"contract_version":"2.0","contract_version":"2.0"}')
            with self.assertRaises(Block): load(p)
    def test_unsafe_type(self): self.reject(lambda d:d['objects'][0]['columns'][0].update(type="enum('DEMO_VALUE')"))
    def test_unsafe_definition(self): self.reject(lambda d:d['definitions'][0].update(definition='https://example.invalid'))
    def test_unknown_lineage(self): self.assertIn('ยังไม่ยืนยัน Data Lineage',Builder(self.d).lineage())
    def test_explicit_lineage(self):
        self.d['lineage']=[dict(from_schema='demo',from_object='department',to_schema='demo',to_object='service',kind='transforms',source_id='SRC_DEMO')]; validate(self.d); self.assertIn('transforms',Builder(self.d).lineage())
    def test_diff(self):
        previous=copy.deepcopy(self.d); self.d['schema_revision']='v2'; self.d['objects'][0]['columns'][1]['length']=100
        self.assertIn('Changed: length',diff(self.d,previous))
    def test_diff_scope(self):
        prev=copy.deepcopy(self.d); prev['scope_id']='different_scope'
        with self.assertRaises(Block): diff(self.d,prev)
    def test_all_modes(self):
        with tempfile.TemporaryDirectory() as t:
            for mode in MODES:
                p=Path(t)/mode; generate(self.d,mode,p,self.d if mode=='diff' else None)
                self.assertTrue((p/'release-manifest.md').is_file())
                self.assertIn('PENDING',(p/'release-manifest.md').read_text())
                self.assertFalse(any(x.suffix=='.json' for x in p.iterdir()))
                if mode=='dictionary': self.assertEqual({x.name for x in p.iterdir()},{'data-dictionary.md','release-manifest.md'})
    def test_existing_dir(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(Block): generate(self.d,'dictionary',Path(t))
    def test_invalid_cli_no_output(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.json'; out=Path(t)/'out'; self.d['sample_rows']=[]; p.write_text(json.dumps(self.d))
            r=subprocess.run([sys.executable,str(ROOT/'scripts'/'build_dictionary.py'),str(p),'--out',str(out)],capture_output=True)
            self.assertNotEqual(r.returncode,0); self.assertFalse(out.exists()); self.assertNotIn(b'sample_rows',r.stdout)
    def test_lint(self): self.assertTrue(any(scan('-----BEGIN PRIVATE KEY-----')))

if __name__=='__main__': unittest.main(verbosity=2)
