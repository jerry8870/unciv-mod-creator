import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import check_mod


class CheckModTests(unittest.TestCase):
    def test_preflight_passes_and_writes_bounded_reports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Example"
            json_dir = mod_dir / "jsons"
            json_dir.mkdir(parents=True)
            (json_dir / "Nations.json").write_text(json.dumps([{
                "name": "Example", "outerColor": [10, 20, 30], "cities": ["Example City"],
            }]), encoding="utf-8")
            markdown_path = root / "report.md"
            json_path = root / "report.json"

            report = check_mod.run_preflight(mod_dir, source_only=True)
            check_mod.write_report(report, markdown_path)
            check_mod.write_report(report, json_path)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["checks"]["packaging"]["status"], "PASS")
            self.assertEqual(report["validation_inputs"]["schema_bundle"]["game_version"], "4.22.0")
            self.assertTrue(report["validation_inputs"]["schema_exceptions"].endswith("references/schema_exceptions.json"))
            self.assertIn("does not prove gameplay behavior", markdown_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["status"], "PASS")

    def test_preflight_fails_for_invalid_rules(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Broken"
            json_dir = mod_dir / "jsons"
            json_dir.mkdir(parents=True)
            (json_dir / "Nations.json").write_text('[{"name":"Broken","outerColor":[999]}]', encoding="utf-8")

            report = check_mod.run_preflight(mod_dir, source_only=True)

            self.assertEqual(report["status"], "FAIL")
            self.assertGreater(report["summary"]["errors"], 0)

    def test_recipe_lab_passes_strict_preflight_without_warnings(self):
        mod_dir = SKILL_DIR / "examples" / "tested-feature-recipes" / "Recipe-Lab"
        base_data = SKILL_DIR / "references" / "snapshots" / "gk-baseline" / "rules.json"

        report = check_mod.run_preflight(
            mod_dir,
            base_rules_data=base_data,
            strict_base_references=True,
            source_only=True,
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["summary"], {"errors": 0, "warnings": 0})

    def test_selects_ruleset_reference_bundle_from_catalog(self):
        mod_dir = SKILL_DIR / "examples" / "tested-feature-recipes" / "Recipe-Lab"

        report = check_mod.run_preflight(
            mod_dir,
            strict_base_references=True,
            source_only=True,
            base_ruleset="Civ V - Gods & Kings",
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            report["validation_inputs"]["reference_bundle"]["base_ruleset"],
            "Civ V - Gods & Kings",
        )
        self.assertRegex(report["checks"]["packaging"]["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
