import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_mod
import evidence_record
import reference_catalog
import unciv_mod
import validate_mod_assets as assets
import validate_mod_rules as rules


class WorkflowOptimizationTests(unittest.TestCase):
    def test_detects_gods_and_kings_from_distinctive_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Expansion-Reference"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "Units.json").write_text(json.dumps([{
                "name": "Detection Unit",
                "unitType": "Melee",
                "upgradesTo": "Composite Bowman",
            }]), encoding="utf-8")
            result = rules.detect_base_ruleset(mod_dir)
        self.assertEqual("detected", result["status"])
        self.assertEqual("Civ V - Gods & Kings", result["ruleset"])

    def test_shared_references_remain_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Shared-Reference"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "Units.json").write_text(json.dumps([{
                "name": "Detection Unit",
                "unitType": "Melee",
                "upgradesTo": "Swordsman",
            }]), encoding="utf-8")
            result = rules.detect_base_ruleset(mod_dir)
        self.assertEqual("ambiguous", result["status"])
        self.assertEqual(set(reference_catalog.available_rulesets()), set(result["candidates"]))

    def test_unified_check_uses_detected_ruleset(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Detected-Mod"
            output = root / "preflight.json"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "Buildings.json").write_text(json.dumps([{
                "name": "Detection Building",
                "requiredBuilding": "Cathedral",
            }]), encoding="utf-8")
            with patch.object(sys, "argv", [
                "unciv_mod.py", "check", str(mod_dir), "--source-only", "--output", str(output),
            ]):
                result = unciv_mod.main()
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(0, result)
        self.assertEqual("auto-detected", report["ruleset_selection"]["source"])
        self.assertEqual("Civ V - Gods & Kings", report["ruleset_selection"]["ruleset"])

    def test_preflight_findings_have_stable_structured_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Broken-Reference"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "Units.json").write_text(json.dumps([{
                "name": "Broken Unit",
                "unitType": "Melee",
                "upgradesTo": "Missing Unit",
            }]), encoding="utf-8")
            report = check_mod.run_preflight(
                mod_dir,
                source_only=True,
                strict_base_references=True,
                base_ruleset="Civ V - Gods & Kings",
            )
        diagnostic = next(item for item in report["checks"]["rules"] if item["code"] == "REFERENCE_NOT_FOUND")
        self.assertEqual("/0/upgradesTo", diagnostic["json_pointer"])
        self.assertEqual("Missing Unit", diagnostic["value"])
        self.assertIn("suggestion", diagnostic)

    def test_duplicate_json_key_has_specific_diagnostic_code(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Duplicate-Key"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "ModOptions.json").write_text(
                '{"isBaseRuleset": false, "isBaseRuleset": true}', encoding="utf-8",
            )
            findings = rules.inspect_mod_rules(mod_dir)
        self.assertIn("JSON_DUPLICATE_KEY", {item.code for item in findings})

    def test_absent_images_are_informational(self):
        finding = assets.Finding("INFO", Path("Fixture"), "No Images or Images.<AtlasName> folders found")
        self.assertEqual("ASSET_NOT_PRESENT", finding.code)

    def test_validation_coverage_matches_implementation(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "references" / "validation_coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(rules.SCHEMA_RULE_FILES), sorted(manifest["official_schema_files"]))
        expected_fields = {
            kind: sorted(fields)
            for kind, fields in {
                **{kind: list(mapping) for kind, mapping in rules.REFERENCE_FIELDS.items()},
                "Buildings": [*rules.REFERENCE_FIELDS["Buildings"], "specialistSlots"],
                "Difficulties": [
                    *rules.REFERENCE_FIELDS["Difficulties"], "playerBonusStartingUnits",
                    "aiMajorCivBonusStartingUnits", "aiCityStateBonusStartingUnits",
                ],
                "Policies": [*rules.REFERENCE_FIELDS["Policies"], "policies.requires"],
                "Quests": ["weightForCityStateType"],
                "Techs": ["era", "techs.prerequisites"],
            }.items()
        }
        declared_fields = {kind: sorted(fields) for kind, fields in manifest["semantic_reference_fields"].items()}
        self.assertEqual(expected_fields, declared_fields)
        for scenario in manifest["integration_scenarios"]:
            self.assertTrue((root / scenario["source"]).exists(), scenario["id"])

    def test_evidence_record_lifecycle_without_target_version(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            preflight = root / "preflight.json"
            archive = root / "mod.zip"
            record = root / "verification.json"
            report = root / "VERIFICATION.md"
            preflight.write_text(json.dumps({
                "status": "PASS", "mode": "source-only", "summary": {"errors": 0, "warnings": 0}
            }), encoding="utf-8")
            archive.write_bytes(b"fixture")
            evidence_record.init_record("Fixture", "Civ V - Vanilla", preflight, archive, record)
            evidence_record.add_check(record, "load-smoke", "passed", "A new game loaded.", ["installed-zip"])
            evidence_record.finalize_record(record, report, "PASS")
            data = json.loads(record.read_text(encoding="utf-8"))
            rendered = report.read_text(encoding="utf-8")
        self.assertEqual({"name": "Unciv"}, data["test_environment"])
        self.assertIn("Test environment: Unciv with the Civ V - Vanilla base ruleset.", rendered)


if __name__ == "__main__":
    unittest.main()
