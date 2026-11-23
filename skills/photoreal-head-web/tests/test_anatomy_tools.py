#!/usr/bin/env python3
"""Deterministic tests: they validate QA logic, not realism of any real head."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import analyze_anatomy
import compare_photo_landmarks


def synthetic_3d():
    return {
        'n': [0, -.047, .145], 'se': [0, -.042, .136],
        'rh': [0, -.062, .111], 'g': [0, -.055, .166], 'pg': [0, -.036, -.033],
        'prn': [0, -.088, .083],
        'sn': [0, -.050, .065], 'sto': [0, -.039, .023],
        'gn': [0, -.028, -.048],
        'en_l': [.016, -.035, .127], 'en_r': [-.016, -.035, .127],
        'ex_l': [.052, -.041, .128], 'ex_r': [-.052, -.041, .128],
        'al_l': [.022, -.060, .072], 'al_r': [-.022, -.060, .072],
        'ch_l': [.033, -.038, .024], 'ch_r': [-.033, -.038, .024],
        't_l': [.087, .014, .102], 't_r': [-.087, .014, .102],
        'sa_l': [.091, .020, .146], 'sa_r': [-.091, .020, .146],
        'sba_l': [.089, .021, .045], 'sba_r': [-.089, .021, .045],
    }


def record(points, width=1024, height=1024, view='front'):
    return {
        'coordinate_space': 'image_pixels_xy_down',
        'image_size': [width, height], 'view': view, 'points': points,
    }


class AnatomyTests(unittest.TestCase):
    def test_healthy_layout_is_review_without_external_reference(self):
        result = analyze_anatomy.check(synthetic_3d())
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertEqual(result['errors'], [])

    def test_reference_match_only_passes_metrics(self):
        p = synthetic_3d()
        result = analyze_anatomy.check(p, p)
        self.assertEqual(result['status'], 'PASS_METRICS_ONLY')
        self.assertTrue(all(x['relative_drift'] == 0 for x in result['reference_comparison'].values()))

    def test_high_fidelity_requires_bridge_and_ear_detail(self):
        p = synthetic_3d()
        self.assertNotEqual(analyze_anatomy.check(p, high_fidelity=True)['status'], 'BLOCKED')
        p.pop('rh')
        self.assertEqual(analyze_anatomy.check(p, high_fidelity=True)['status'], 'BLOCKED')

    def test_swapped_landmark_blocks(self):
        p = synthetic_3d()
        p['en_l'], p['en_r'] = p['en_r'], p['en_l']
        result = analyze_anatomy.check(p)
        self.assertEqual(result['status'], 'BLOCKED')

    def test_nasal_width_drift_blocks(self):
        p = synthetic_3d()
        changed = copy.deepcopy(p)
        changed['al_l'][0] += 0.018
        result = analyze_anatomy.check(changed, p)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn('nasal_width', result['reference_comparison'])

    def test_json_validation_rejects_null_templates(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'a.json'
            path.write_text(json.dumps({
                'coordinate_system': 'blender_local_z_up_front_minus_y',
                'units': 'meters', 'landmarks': {'n': None}
            }))
            with self.assertRaises(ValueError):
                analyze_anatomy.load_landmarks(path)


class PhotoFitTests(unittest.TestCase):
    def setUp(self):
        self.ref = {
            'en_l': [530, 310], 'en_r': [480, 310],
            'ex_l': [585, 310], 'ex_r': [425, 310],
            'n': [505, 324], 'prn': [505, 442], 'sn': [505, 458],
            'sto': [505, 514], 'gn': [505, 622],
            'al_l': [532, 450], 'al_r': [478, 450],
            'ch_l': [545, 515], 'ch_r': [465, 515],
        }

    def make_files(self, td, render_points, view='front'):
        ref_path = Path(td) / 'reference.json'
        render_path = Path(td) / 'render.json'
        ref_path.write_text(json.dumps(record(self.ref, view=view)))
        render_path.write_text(json.dumps(record(render_points, 1400, 1400, view=view)))
        return ref_path, render_path

    def test_uniform_scale_translation_is_ignored(self):
        render = {name: [v[0] * 1.18 + 15, v[1] * 1.18 + 11]
                  for name, v in self.ref.items()}
        with tempfile.TemporaryDirectory() as td:
            a, b = self.make_files(td, render)
            result = compare_photo_landmarks.compare(a, b)
            self.assertEqual(result['status'], 'PASS_PHOTO_FIT_ONLY')
            self.assertLess(result['rms_normalized'], 0.00001)
            try:
                from PIL import Image
            except ImportError:
                return
            preview = Path(td) / 'overlay.png'
            compare_photo_landmarks.save_overlay(preview, result)
            self.assertTrue(preview.is_file())
            with Image.open(preview) as image:
                self.assertEqual(image.size, (1024, 1024))

    def test_nose_tip_offset_triggers_review(self):
        render = {name: [v[0] * 1.18 + 15, v[1] * 1.18 + 11]
                  for name, v in self.ref.items()}
        render['prn'][1] += 35
        with tempfile.TemporaryDirectory() as td:
            a, b = self.make_files(td, render)
            result = compare_photo_landmarks.compare(a, b)
            self.assertEqual(result['status'], 'REVIEW_REQUIRED')
            self.assertEqual(result['largest_error_landmark'], 'prn')
            self.assertGreater(result['per_region_rms']['nose'], 0.04)

    def test_profile_and_front_cannot_be_compared(self):
        render = {name: [v[0] * 1.18 + 15, v[1] * 1.18 + 11]
                  for name, v in self.ref.items()}
        with tempfile.TemporaryDirectory() as td:
            a, b = self.make_files(td, render)
            doc = json.loads(b.read_text())
            doc['view'] = 'left_profile'
            b.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                compare_photo_landmarks.compare(a, b)


if __name__ == '__main__':
    unittest.main()
