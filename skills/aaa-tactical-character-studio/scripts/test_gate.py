import json
import tempfile
import unittest
from pathlib import Path
from gate import ROLES, run


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "evidence").mkdir()
        for stage, roles in ROLES.items():
            candidate = self.root / f"{stage}.fixture"
            candidate.write_text("synthetic candidate")
            evidence = {}
            for role in roles.split():
                p = self.root / f"{stage}-{role}.fixture"
                p.write_text("synthetic evidence")
                evidence[role] = p.name
            self.write(stage, dict(stage=stage, candidate=candidate.name, author="author", reviewer="reviewer", reviewer_type="AI", decision="PASS", findings="synthetic test only", evidence=evidence))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, stage, data):
        (self.root / "evidence" / f"{stage}.json").write_text(json.dumps(data))

    def read(self, stage):
        return json.loads((self.root / "evidence" / f"{stage}.json").read_text())

    def test_full_chain_and_mutation(self):
        for stage in ROLES:
            run(self.root, stage)
        self.assertEqual(run(self.root), "PASS_EVIDENCE_INTEGRITY_ONLY")
        (self.root / "G2.fixture").write_text("changed")
        with self.assertRaisesRegex(ValueError, "G2: missing/stale"):
            run(self.root)
        run(self.root, "G2")
        with self.assertRaisesRegex(ValueError, "G3: missing/stale"):
            run(self.root)

    def test_final_review_mutation(self):
        for stage in ROLES:
            run(self.root, stage)
        d = self.read("G7")
        d["findings"] = "changed after seal"
        self.write("G7", d)
        with self.assertRaisesRegex(ValueError, "G7: missing/stale"):
            run(self.root)

    def test_no_skip(self):
        with self.assertRaisesRegex(ValueError, "G0: missing/stale"):
            run(self.root, "G1")

    def test_self_review(self):
        d = self.read("G0")
        d["reviewer"] = "AUTHOR"
        self.write("G0", d)
        with self.assertRaisesRegex(ValueError, "reviewer must differ"):
            run(self.root, "G0")

    def test_missing_role(self):
        d = self.read("G0")
        del d["evidence"]["reference"]
        self.write("G0", d)
        with self.assertRaisesRegex(ValueError, "roles missing"):
            run(self.root, "G0")

    def test_path_escape(self):
        d = self.read("G0")
        d["candidate"] = "../outside"
        self.write("G0", d)
        with self.assertRaisesRegex(ValueError, "unsafe artifact"):
            run(self.root, "G0")

    def test_fail_review(self):
        d = self.read("G0")
        d["decision"] = "FAIL"
        self.write("G0", d)
        with self.assertRaisesRegex(ValueError, "missing PASS"):
            run(self.root, "G0")


if __name__ == "__main__":
    unittest.main()
