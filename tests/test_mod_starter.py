import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import create_mod_starter as starter
import validate_mod_rules as rules


class ModStarterTests(unittest.TestCase):
    def test_civilization_starter_contains_a_valid_sample_and_brief(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = starter.create_starter(
                Path(temporary_directory), "Northshore Mod", "A coastal trading civilization", "civilization-extension"
            )

            nations = json.loads((mod_dir / "jsons" / "Nations.json").read_text(encoding="utf-8"))
            self.assertEqual(mod_dir.name, "Northshore-Mod")
            self.assertEqual(nations[0]["name"], "New Nation")
            self.assertEqual(nations[0]["cities"], ["Capital"])
            self.assertIn("A coastal trading civilization", (mod_dir / "README.md").read_text(encoding="utf-8"))
            design = (mod_dir / "DESIGN.md").read_text(encoding="utf-8")
            self.assertIn("Feature mapping", design)
            self.assertIn("unciv_mod.py check", design)
            self.assertFalse([finding for finding in rules.inspect_mod_rules(mod_dir) if finding.severity == "ERROR"])

    def test_unit_building_starter_has_empty_valid_rule_arrays(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = starter.create_starter(Path(temporary_directory), "Harbor-Tools", "A naval content pack", "unit-building")

            self.assertEqual(json.loads((mod_dir / "jsons" / "Units.json").read_text(encoding="utf-8")), [])
            self.assertEqual(json.loads((mod_dir / "jsons" / "Buildings.json").read_text(encoding="utf-8")), [])
            self.assertFalse([finding for finding in rules.inspect_mod_rules(mod_dir) if finding.severity == "ERROR"])

    def test_map_starter_explains_how_to_add_a_real_map(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = starter.create_starter(Path(temporary_directory), "Small-Isles", "A compact archipelago", "map-only")

            self.assertTrue((mod_dir / "maps").is_dir())
            self.assertFalse((mod_dir / "jsons").exists())
            self.assertIn("Map Editor", (mod_dir / "README.md").read_text(encoding="utf-8"))

    def test_refuses_to_overwrite_an_existing_mod_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Keep-Me"
            mod_dir.mkdir()
            readme = mod_dir / "README.md"
            readme.write_text("user file", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                starter.create_starter(Path(temporary_directory), "Keep Me", "A brief", "map-only")

            self.assertEqual(readme.read_text(encoding="utf-8"), "user file")

    def test_rejects_a_blank_brief_without_creating_a_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(ValueError, "brief must not be empty"):
                starter.create_starter(Path(temporary_directory), "New Mod", "  ", "map-only")

            self.assertEqual(list(Path(temporary_directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
