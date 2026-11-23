"""Behavior tests for durable briefs and hash-bound previews, not NLP claims."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import studio_project as studio

SKILL = Path(__file__).resolve().parents[1]
GLB = SKILL / 'assets/examples/character_blockout.glb'


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = self.base / 'project'

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, changes, text='สร้างจากภาพนี้', intent='update'):
        path = self.base / 'request.json'
        studio.write(path, {'raw_text': text, 'intent': intent, 'changes': changes})
        return path

    def initialize(self, changes=None):
        return studio.initialize_project(self.project, self.request(changes or {}, intent='create'))

    def test_continue_preserves_project_preferences_and_stops_at_head(self):
        self.initialize({'device': 'MOBILE', 'actor_count': 30, 'rig': 'DEFORMABLE_SKINNED', 'clips': ['Walk']})
        result = studio.update(self.project, self.request({}, 'ใช้เดิม ทำต่อ', 'continue'))
        self.assertEqual(result['brief']['actor_count'], 30)
        self.assertEqual(result['brief']['clips'], ['Walk'])
        self.assertEqual(result['next_allowed_stage'], 'HEAD')
        self.assertEqual(result['next_action'], 'G0_REFERENCE_INTAKE')
        self.assertEqual(result['production_status'], 'NOT_APPROVED_BY_THIS_HELPER')

    def test_thai_numbers_and_target_change_do_not_revoke_shape(self):
        self.initialize()
        brief, state = studio.load(self.project)
        state['invalidated_domains'] = []
        studio.write(self.project / 'studio_state.json', state)
        result = studio.update(self.project, self.request({'device': 'มือถือ', 'actor_count': '๕๐'}, 'ใช้บนมือถือ ๕๐ ตัว'))
        self.assertEqual(result['brief']['actor_count'], 50)
        self.assertEqual(result['brief']['device'], 'MOBILE')
        self.assertEqual(result['invalidated_domains'], ['browser', 'runtime'])
        self.assertFalse(studio.load(self.project)[1]['shape_brief_changed'])
        self.assertEqual(result['runtime_status'], 'NOT_TESTED')

    def test_empty_clips_preserves_rig_for_future_animation(self):
        self.initialize({'rig': 'DEFORMABLE_SKINNED', 'clips': ['Idle', 'Walk']})
        result = studio.update(self.project, self.request({'clips': []}, 'ไม่ต้องทำ animation แต่เตรียม rig ไว้'))
        self.assertEqual(result['brief']['clips'], [])
        self.assertEqual(result['brief']['rig'], 'DEFORMABLE_SKINNED')
        self.assertEqual(result['clip_qa'], 'NOT_APPLICABLE')
        self.assertEqual(result['deformation_qa'], 'REQUIRED')

    def test_invalid_request_is_atomic_and_does_not_guess_negation(self):
        self.initialize({'device': 'MOBILE'})
        old = (self.project / 'studio_brief.json').read_bytes()
        with self.assertRaises(ValueError):
            studio.update(self.project, self.request({'actor_count': '๓.๕'}))
        self.assertEqual((self.project / 'studio_brief.json').read_bytes(), old)
        result = studio.update(self.project, self.request({'device': 'DESKTOP'}, 'ยังไม่ต้องใช้บนมือถือ เอา desktop ก่อน'))
        self.assertEqual(result['brief']['device'], 'DESKTOP')

    def test_restart_retains_intent_but_drops_approvals(self):
        self.initialize({'actor_count': 50, 'rig': 'DEFORMABLE_SKINNED', 'clips': ['Walk']})
        _, state = studio.load(self.project)
        stage = Path(state['stage_project']) / 'stages/01_head/gate.json'
        studio.write(stage, {'status': 'PASS', 'part': 'HEAD', 'marker': 'old'})
        out = self.base / 'restarted'
        result = studio.restart(self.project, out)
        self.assertEqual(result['brief']['actor_count'], 50)
        self.assertEqual(result['brief']['clips'], ['Walk'])
        self.assertIsNone(studio.load(out)[1]['current'])
        self.assertEqual(result['stage_status']['HEAD']['status'], 'NOT_TESTED')
        self.assertTrue(stage.is_file())

    def test_restart_preserves_assumptions_and_explicit_provenance(self):
        self.initialize({'actor_count': 50})
        before, _ = studio.load(self.project)
        request = self.request({'constraints': ['ไม่มีกระเป๋า'], 'source_files': []}, 'เริ่มใหม่ ใช้ภาพเดิม ไม่ต้องมีกระเป๋า', 'restart')
        payload = studio.read(request)
        payload['provenance'] = {'source_files': 'PROJECT'}
        studio.write(request, payload)
        out = self.base / 'new-run'
        result = studio.restart(self.project, out, request)
        after, _ = studio.load(out)
        self.assertIn('height_m', result['assumed_fields'])
        self.assertEqual(after['provenance']['height_m']['source'], 'ASSUMED')
        self.assertEqual(after['provenance']['actor_count']['source'], before['provenance']['actor_count']['source'])
        self.assertEqual(after['provenance']['source_files']['source'], 'PROJECT')
        self.assertEqual(after['provenance']['constraints']['source'], 'USER')
        self.assertIn('inherited_from', after['provenance']['height_m'])

    def test_intake_binds_source_and_no_assumed_four_panels(self):
        source = self.base / 'front.png'
        from PIL import Image
        Image.new('RGB', (64, 128), 'white').save(source)
        self.initialize({'source_files': [str(source)]})
        manifest = self.base / 'intake.json'
        studio.write(manifest, {'source_sha256': [studio.sha(source)], 'layout_notes': 'ภาพด้านหน้าภาพเดียว',
            'proportion_notes': 'ยังไม่ยืนยันความลึก', 'camera_notes': 'UNKNOWN',
            'views': [{'name': 'front', 'basis': 'OBSERVED', 'notes': 'เต็มตัว', 'crop_px': [0, 0, 64, 128]}]})
        result = studio.intake(self.project, manifest)
        self.assertEqual(result['next_action'], 'HEAD')
        self.assertEqual(result['stage_status']['HEAD']['status'], 'NOT_TESTED')
        source.write_bytes(source.read_bytes() + b'changed')
        result = studio.plan(self.project)
        self.assertEqual(result['next_action'], 'G0_REFERENCE_INTAKE')
        self.assertEqual(result['stale_source_files'], [str(source)])

    def test_reference_change_invalidates_intake_and_shape(self):
        self.initialize()
        result = studio.update(self.project, self.request({'must_match': ['คางเหลี่ยม แก้มไม่ป่อง']}, 'แก้ให้เหมือน'))
        self.assertIn('intake', result['invalidated_domains'])
        self.assertTrue(studio.load(self.project)[1]['shape_brief_changed'])
        self.assertEqual(result['next_allowed_stage'], 'HEAD')

    def test_checkpoint_rejects_wrong_hash_and_skipped_stage(self):
        self.initialize()
        renders = self.base / 'renders'; renders.mkdir()
        qa = self.base / 'qa.json'
        studio.write(qa, {'model_sha256': 'not-this-model'})
        with self.assertRaisesRegex(ValueError, 'QA must bind'):
            studio.checkpoint(self.project, GLB, 'HEAD', renders, qa=qa)
        studio.write(qa, {'model_sha256': studio.sha(GLB)})
        with self.assertRaisesRegex(ValueError, 'ห้ามข้าม'):
            studio.checkpoint(self.project, GLB, 'TORSO', renders, qa=qa)
        self.assertIsNone(studio.load(self.project)[1]['current'])

    def test_checkpoint_builds_actual_model_preview_and_is_not_art_approval(self):
        self.initialize()
        from PIL import Image
        renders = self.base / 'renders'; renders.mkdir()
        Image.new('RGB', (64, 64), 'gray').save(renders / 'front.png')
        qa = self.base / 'qa.json'
        studio.write(qa, {'model_sha256': studio.sha(GLB), 'fidelity_status': 'NOT_TESTED'})
        result = studio.checkpoint(self.project, GLB, 'HEAD', renders, qa=qa)
        copied = self.project / 'preview/head.glb'
        self.assertEqual(studio.sha(copied), studio.sha(GLB))
        config = studio.read(self.project / 'preview/review-config.json')
        self.assertEqual(config['status'], 'REVIEW_REQUIRED')
        self.assertEqual(result['next_allowed_stage'], 'HEAD')
        self.assertEqual(result['runtime_status'], 'NOT_TESTED')
        studio.checkpoint(self.project, GLB, 'HEAD', renders, qa=qa)
        state = studio.load(self.project)[1]
        self.assertEqual(len(state['checkpoints']), 1)
        self.assertIsNone(state['previous'])


if __name__ == '__main__':
    unittest.main()
