import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import validate_mod_rules as rules


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def base_rules_data() -> dict:
    return {
        "Nations": [{"name": "Tideward"}],
        "Units": [{"name": "Trireme"}, {"name": "Caravel"}],
        "Buildings": [{"name": "Market"}],
        "Techs": [{"techs": [{"name": "Sailing"}, {"name": "Astronomy"}, {"name": "Currency"}]}],
        "UnitTypes": [{"name": "Melee Water"}],
        "UnitPromotions": [{"name": "Navigation I"}],
        "TileImprovements": [{"name": "Mine"}],
        "TileResources": [{"name": "Iron"}],
        "Terrains": [{"name": "Plains"}],
        "Eras": [{"name": "Ancient era"}],
        "Policies": [{"name": "Tradition"}, {"name": "Oligarchy"}],
    }


class ModRulesTests(unittest.TestCase):
    def test_cli_base_ruleset_selects_its_baseline(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "VersionOnly"
            write_json(mod_dir / "jsons" / "Nations.json", [])
            captured = {}

            def capture(*args):
                captured["base_rules_data"] = args[1]
                captured["base_ruleset"] = args[6]
                return []

            with patch.object(sys, "argv", [
                "validate_mod_rules.py", str(mod_dir),
                "--base-ruleset", "Civ V - Gods & Kings",
            ]), patch.object(rules, "inspect_mod_rules", side_effect=capture):
                result = rules.main()

            self.assertEqual(result, 0)
            self.assertEqual(captured["base_ruleset"], "Civ V - Gods & Kings")
            self.assertEqual(
                captured["base_rules_data"],
                SKILL_DIR / "references" / "snapshots" / "gk-baseline" / "rules.json",
            )

    def test_checks_rich_civilization_references_against_base_data(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Tideward"
            base_file = root / "rules.json"
            write_json(base_file, base_rules_data())
            write_json(mod_dir / "jsons" / "Nations.json", [{
                "name": "Tideward", "leaderName": "Nerissa", "outerColor": [24, 80, 105],
                "innerColor": [235, 198, 128], "cities": ["Saltport", "Pearl Haven"],
                "uniques": ["[+1 Gold] from each Trade Route"],
            }])
            write_json(mod_dir / "jsons" / "Units.json", [{
                "name": "Tidewarder", "unitType": "Melee Water", "uniqueTo": "Tideward",
                "replaces": "Trireme", "upgradesTo": "Caravel", "requiredTech": "Sailing",
                "obsoleteTech": "Astronomy", "uniques": ["Cannot enter ocean tiles"],
            }])
            write_json(mod_dir / "jsons" / "Buildings.json", [{
                "name": "Harbor Exchange", "uniqueTo": "Tideward", "replaces": "Market",
                "requiredTech": "Currency",
            }])

            findings = rules.inspect_mod_rules(mod_dir, base_file, strict_base_references=True)

            errors = [finding.message for finding in findings if finding.severity == "ERROR"]
            self.assertEqual(errors, [])
            self.assertTrue(any("global-trade-route-yield" in finding.message for finding in findings))
            self.assertTrue(any("unregistered unique" in finding.message for finding in findings))

    def test_rejects_duplicate_json_keys_and_invalid_civilization_shapes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Tideward"
            nation_file = mod_dir / "jsons" / "Nations.json"
            nation_file.parent.mkdir(parents=True)
            nation_file.write_text(
                '[{"name":"Tideward","name":"Tideward","outerColor":[24,80,105]}]',
                encoding="utf-8",
            )
            write_json(mod_dir / "jsons" / "Units.json", [{"name": "Tidewarder"}])

            findings = rules.inspect_mod_rules(mod_dir)
            errors = [finding.message for finding in findings if finding.severity == "ERROR"]

            self.assertTrue(any("duplicate object key" in message for message in errors))
            self.assertTrue(any("unitType" in message for message in errors))

    def test_reports_duplicate_cities_and_strict_unresolved_base_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Tideward"
            base_file = root / "rules.json"
            write_json(base_file, {
                "Nations": [], "Units": [], "Buildings": [], "Techs": [], "UnitTypes": [],
            })
            write_json(mod_dir / "jsons" / "Nations.json", [{
                "name": "Tideward", "outerColor": [24, 80, 105], "cities": ["Saltport", "Saltport"],
            }, {
                "name": "Tideward", "outerColor": [24, 80, 105], "cities": ["Pearl Haven"],
            }])
            write_json(mod_dir / "jsons" / "Units.json", [{
                "name": "Tidewarder", "unitType": "Melee Water", "uniqueTo": "Tideward",
                "replaces": "Missing Ship",
            }])

            findings = rules.inspect_mod_rules(mod_dir, base_file, strict_base_references=True)
            errors = [finding.message for finding in findings if finding.severity == "ERROR"]

            self.assertTrue(any("duplicate value" in message for message in errors))
            self.assertTrue(any("Duplicate Nations name" in message for message in errors))
            self.assertTrue(any("Missing Ship" in message for message in errors))

    def test_checks_extended_rule_types_and_translation_placeholders(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Extended"
            base_file = root / "rules.json"
            write_json(base_file, base_rules_data())
            write_json(mod_dir / "jsons" / "TileImprovements.json", [{
                "name": "Tide Mine", "terrainsCanBeBuiltOn": ["Plains"], "techRequired": "Sailing",
                "replaces": "Mine", "uniqueTo": "Tideward",
            }])
            write_json(mod_dir / "jsons" / "TileResources.json", [{
                "name": "Blue Iron", "resourceType": "Strategic", "improvedBy": ["Tide Mine"],
                "revealedBy": "Sailing", "terrainsCanBeFoundOn": ["Plains"],
            }])
            write_json(mod_dir / "jsons" / "UnitPromotions.json", [{
                "name": "Tide Navigation", "prerequisites": ["Navigation I"], "unitTypes": ["Melee Water"],
            }])
            write_json(mod_dir / "jsons" / "Policies.json", [{
                "name": "Harbor Code", "era": "Ancient era", "policies": [
                    {"name": "Safe Harbors", "row": 1, "column": 1},
                    {"name": "Harbor Code Complete", "requires": ["Safe Harbors"]},
                ],
            }])
            write_json(mod_dir / "jsons" / "Techs.json", [{
                "columnNumber": 1, "era": "Ancient era", "techs": [
                    {"name": "Tidecraft", "row": 1, "prerequisites": ["Sailing"]},
                ],
            }])
            write_json(mod_dir / "jsons" / "ModOptions.json", {"isBaseRuleset": False, "uniques": []})
            write_json(mod_dir / "jsons" / "GlobalUniques.json", {"name": "Global Uniques", "uniques": []})
            translation = mod_dir / "jsons" / "translations" / "Simplified_Chinese.properties"
            translation.parent.mkdir(parents=True)
            translation.write_text("Hello [name] = 你好 [name]\n", encoding="utf-8")

            findings = rules.inspect_mod_rules(mod_dir, base_file, strict_base_references=True)

            self.assertEqual([finding.message for finding in findings if finding.severity == "ERROR"], [])

    def test_rejects_invalid_extended_shapes_and_translation_placeholders(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Broken"
            write_json(mod_dir / "jsons" / "TileResources.json", [{"name": "Bad", "resourceType": "Rare"}])
            write_json(mod_dir / "jsons" / "UnitTypes.json", [{"name": "Bad Type", "movementType": "Space"}])
            write_json(mod_dir / "jsons" / "Techs.json", [{
                "columnNumber": -1, "era": "Ancient era", "techs": [
                    {"name": "Broken Tech", "row": 0}, {"name": "Broken Tech", "row": 0},
                ],
            }])
            translation = mod_dir / "jsons" / "translations" / "Test.properties"
            translation.parent.mkdir(parents=True)
            translation.write_text("Hello [name] = 你好\n", encoding="utf-8")

            findings = rules.inspect_mod_rules(mod_dir)
            errors = [finding.message for finding in findings if finding.severity == "ERROR"]

            self.assertTrue(any("resourceType" in message for message in errors))
            self.assertTrue(any("movementType" in message for message in errors))
            self.assertTrue(any("columnNumber" in message for message in errors))
            self.assertTrue(any("Duplicate technology" in message for message in errors))
            self.assertTrue(any("preserve all square-bracket placeholders" in message for message in errors))

    def test_registry_rejects_known_mechanic_on_wrong_object_type(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "WrongOwner"
            write_json(mod_dir / "jsons" / "TileImprovements.json", [{
                "name": "Wrong Improvement", "uniques": ["[+20]% Strength"],
            }])

            findings = rules.inspect_mod_rules(mod_dir)

            self.assertTrue(any("registry applicability" in finding.message for finding in findings if finding.severity == "ERROR"))

    def test_registry_maps_official_unique_categories_to_valid_owners(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "ValidOwners"
            write_json(mod_dir / "jsons" / "Buildings.json", [{
                "name": "Strength Hall", "uniques": ["[+20]% Strength"],
            }])
            write_json(mod_dir / "jsons" / "Beliefs.json", [{
                "name": "Trade Faith", "type": "Follower",
                "uniques": ["[+2 Science] from each Trade Route"],
            }])
            write_json(mod_dir / "jsons" / "Nations.json", [{
                "name": "Harbor State", "cityStateType": "Cultured",
                "uniques": ["Start bias [Fresh Water]"],
            }])

            findings = rules.inspect_mod_rules(mod_dir)

            self.assertFalse([
                finding for finding in findings
                if finding.severity == "ERROR" and "registry applicability" in finding.message
            ])

    def test_registry_matches_parameterized_unique_without_inheriting_exact_evidence(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Parameterized"
            write_json(mod_dir / "jsons" / "Units.json", [{
                "name": "Stronger Guard", "unitType": "Sword", "uniques": ["[+30]% Strength"],
            }])

            findings = rules.inspect_mod_rules(mod_dir)
            messages = [finding.message for finding in findings]

            self.assertTrue(any("matches parameterized mechanic 'unit-strength-percent'" in message for message in messages))
            self.assertFalse(any("unregistered unique" in message for message in messages))
            self.assertFalse(any(finding.severity == "ERROR" for finding in findings))

    def test_official_schema_rejects_unknown_fields(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "SchemaFailure"
            write_json(mod_dir / "jsons" / "Units.json", [{
                "name": "Broken Unit", "unitType": "Sword", "unsupportedField": True,
            }])

            findings = rules.inspect_mod_rules(mod_dir)

            self.assertTrue(any(
                finding.severity == "ERROR" and "Official Unciv 4.22.0 Schema" in finding.message
                for finding in findings
            ))

    def test_schema_exception_is_limited_to_its_ruleset(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Personality"
            write_json(mod_dir / "jsons" / "Personalities.json", [{
                "name": "Reviewed Personality", "denounceWillingness": 5,
            }])

            gk_findings = rules.inspect_mod_rules(
                mod_dir, base_ruleset="Civ V - Gods & Kings",
            )
            vanilla_findings = rules.inspect_mod_rules(
                mod_dir, base_ruleset="Civ V - Vanilla",
            )

            self.assertFalse([finding for finding in gk_findings if finding.severity == "ERROR"])
            self.assertTrue(any(
                finding.severity == "ERROR" and "denounceWillingness" in finding.message
                for finding in vanilla_findings
            ))

    def test_checks_nested_cross_file_references(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Nested"
            base_file = root / "rules.json"
            write_json(base_file, {"Specialists": [{"name": "Scientist"}], "TileResources": []})
            write_json(mod_dir / "jsons" / "Buildings.json", [{
                "name": "Research Lodge", "specialistSlots": {"Missing Specialist": 1},
            }])

            findings = rules.inspect_mod_rules(mod_dir, base_file, strict_base_references=True)

            self.assertTrue(any(
                finding.severity == "ERROR" and "Missing Specialist" in finding.message
                for finding in findings
            ))

    def test_checks_registered_unique_reference_parameters(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Parameters"
            base_file = root / "rules.json"
            write_json(base_file, {"TileResources": [{"name": "Iron"}]})
            write_json(mod_dir / "jsons" / "Nations.json", [{
                "name": "Parameters", "outerColor": [1, 2, 3],
                "uniques": ["Provides [2] [Missing Resource]"],
            }])

            findings = rules.inspect_mod_rules(mod_dir, base_file, strict_base_references=True)

            self.assertTrue(any(
                finding.severity == "ERROR" and "parameter 'resource'" in finding.message
                for finding in findings
            ))


if __name__ == "__main__":
    unittest.main()
