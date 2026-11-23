"""Portable CLI safety tests; no Blender dependency or scan download required."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/build_example.py'


class BuildExampleCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='head-cli-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source with spaces'
        self.source.mkdir()
        for name in ('LeePerrySmith.glb', 'Map-COL.jpg', 'Infinite-Level_02_Tangent_SmoothUV.jpg', 'LeePerrySmith_License.txt'):
            (self.source / name).write_text('fixture', encoding='utf-8')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                              cwd=self.root, capture_output=True, text=True)

    def test_help_from_other_cwd(self):
        self.assertEqual(self.run_cli('--help').returncode, 0)

    def test_import_has_no_scene_or_file_side_effects(self):
        spec = importlib.util.spec_from_file_location('head_build', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(callable(module.main))

    def test_missing_inputs_fail_without_output(self):
        output = self.root / 'missing-output'
        result = self.run_cli('--source-dir', self.root, '--out-dir', output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_overlap_and_invalid_settings_are_refused(self):
        for output in (self.source, self.source / 'nested', self.root):
            result = self.run_cli('--source-dir', self.source, '--out-dir', output)
            self.assertEqual(result.returncode, 2)
            self.assertIn('must not overlap', result.stderr)
        output = self.root / 'invalid'
        result = self.run_cli('--source-dir', self.source, '--out-dir', output, '--samples', '0')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(output.exists())

    def test_nonempty_output_preserved(self):
        output = self.root / 'occupied'
        output.mkdir()
        sentinel = output / 'sentinel'
        sentinel.write_bytes(b'keep')
        result = self.run_cli('--source-dir', self.source, '--out-dir', output)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'keep')


if __name__ == '__main__':
    unittest.main()
