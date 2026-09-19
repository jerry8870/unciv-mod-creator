import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import render_verification


class VerificationTests(unittest.TestCase):
    def test_checked_in_report_matches_machine_readable_record(self):
        record_path = SKILL_DIR / "examples" / "tested-feature-recipes" / "verification.json"
        report_path = SKILL_DIR / "examples" / "tested-feature-recipes" / "VERIFICATION.md"

        rendered = render_verification.render(render_verification.load_record(record_path))

        self.assertEqual(report_path.read_text(encoding="utf-8"), rendered)

    def test_invalid_record_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "verification.json"
            path.write_text(json.dumps({"schema_version": 2, "checks": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                render_verification.load_record(path)


if __name__ == "__main__":
    unittest.main()
