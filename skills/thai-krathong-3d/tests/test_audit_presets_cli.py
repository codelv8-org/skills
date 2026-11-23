"""Portable audit preflight tests; run with standard Python, not Blender."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/audit_presets.py'


class AuditPresetsCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='preset-cli-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'presets'
        self.source.mkdir()
        (self.source / 'ref-test.json').write_text('{}')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *map(str, args)],
                              cwd=self.root, capture_output=True, text=True)

    def test_help_other_cwd(self):
        self.assertEqual(self.run_cli('--help').returncode, 0)

    def test_missing_empty_pattern_and_escaping_pattern(self):
        for pattern in ('missing*.json', '../*.json', '**/*.json', ''):
            output = self.root / 'absent'
            result = self.run_cli('--presets-dir', self.source, '--pattern', pattern, '--out-dir', output)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())

    def test_nonempty_output_preserved(self):
        output = self.root / 'occupied'
        output.mkdir()
        sentinel = output / 'sentinel'
        sentinel.write_bytes(b'keep')
        result = self.run_cli('--presets-dir', self.source, '--out-dir', output)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(sentinel.read_bytes(), b'keep')
        self.assertEqual(list(output.iterdir()), [sentinel])

    def test_overlapping_paths_refused(self):
        for output in (self.source, self.source / 'nested', self.root):
            result = self.run_cli('--presets-dir', self.source, '--out-dir', output)
            self.assertEqual(result.returncode, 2)
            self.assertIn('must not overlap', result.stderr)


if __name__ == '__main__':
    unittest.main()
