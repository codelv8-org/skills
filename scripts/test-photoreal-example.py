#!/usr/bin/env python3
"""Regression checks for failed public builds; never waive a UV gate."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_example',ROOT/'scripts/build-photoreal-example.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class FailedBuildEvidence(unittest.TestCase):
    def test_original_scan_is_blocked_and_retains_exact_uv_evidence(self):
        # This is the actual asset that exposed the CI failure, not a fabricated
        # success fixture. Its original UVs are intentionally retained as baseline.
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            report=builder.build(ROOT/'assets/examples/photoreal-head/model/head.glb',out,out/'overview.svg',128,128)
            self.assertEqual(report['status'],'BLOCKED')
            self.assertEqual(report['modes'],[])
            self.assertIn('overlap_pairs_found',report['uv']['errors'])
            evidence=json.loads((out/report['reports']['uv']).read_text())
            self.assertEqual(evidence['candidate_sha256'],report['sourceSha256'])
            self.assertEqual(evidence['status'],'BLOCKED')
            self.assertTrue((out/'projection-lab/uv_anisotropy.png').is_file())
            self.assertFalse(list((out/'projection-lab').glob('*.webp')))

    def test_missing_input_replaces_stale_results_with_blocked_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            stale=out/'projection-lab'
            stale.mkdir()
            (stale/'multiview.webp').write_bytes(b'stale output must not survive')
            report=builder.build(out/'missing.glb',out,out/'overview.svg',128,128)
            self.assertEqual(report['status'],'BLOCKED')
            self.assertEqual(report['modes'],[])
            self.assertIn('FileNotFoundError',report['reason'])
            self.assertFalse((stale/'multiview.webp').exists())
            self.assertEqual(json.loads((out/'reports/projection_lab.json').read_text())['status'],'BLOCKED')


if __name__=='__main__':
    unittest.main()
