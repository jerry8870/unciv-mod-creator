import hashlib
import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import update_unciv_reference_data as updater
import audit_reference_data
import reference_catalog


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReferenceDataTests(unittest.TestCase):
    def test_baseline_is_complete_and_matches_manifest(self):
        root = SKILL_DIR / "references" / "snapshots" / "gk-baseline"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        rules = json.loads((root / "rules.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["game_version"], "4.22.0")
        self.assertEqual(set(rules), set(updater.BASE_FILES))
        self.assertIn("Sword", {item["name"] for item in rules["UnitTypes"]})
        for relative_path, expected_hash in manifest["files"].items():
            self.assertEqual(sha256(root / relative_path), expected_hash)

    def test_schema_bundle_matches_manifest(self):
        root = SKILL_DIR / "references" / "schemas" / "unciv-4.22.0"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["game_version"], "4.22.0")
        self.assertEqual(len(manifest["files"]), 32)
        for relative_path, expected_hash in manifest["files"].items():
            self.assertEqual(sha256(root / relative_path), expected_hash)

    def test_reference_catalog_selects_both_rulesets(self):
        gk = reference_catalog.resolve_bundle("Civ V - Gods & Kings")
        vanilla = reference_catalog.resolve_bundle("Civ V - Vanilla")

        self.assertTrue(gk["base_rules_data"].is_file())
        self.assertTrue(vanilla["base_rules_data"].is_file())
        self.assertNotEqual(gk["base_rules_data"], vanilla["base_rules_data"])

    def test_reference_audit_accepts_only_reviewed_schema_drift(self):
        result = audit_reference_data.audit()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["summary"]["rulesets"], 2)
        self.assertEqual(result["summary"]["accepted_exception_instances"], 42)

    def test_upstream_json_normalizer_preserves_strings(self):
        source = b'[// comment\n{"url":"https://example.test/a//b","values":[1,2,],},]'
        self.assertEqual(
            updater.parse_upstream_json(source, "test.json"),
            [{"url": "https://example.test/a//b", "values": [1, 2]}],
        )


if __name__ == "__main__":
    unittest.main()
