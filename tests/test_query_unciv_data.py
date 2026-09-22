import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import query_unciv_data


class QueryUncivDataTests(unittest.TestCase):
    def test_list_types_exposes_rules_and_source_urls(self):
        result = query_unciv_data.list_types("Civ V - Gods & Kings")
        types = {item["type"]: item for item in result["types"]}
        self.assertIn("Techs", types)
        self.assertIn("UnitPromotions", types)
        self.assertGreater(types["Techs"]["named_entries"], 0)
        self.assertTrue(types["Techs"]["source_url"].endswith("/Techs.json"))

    def test_exact_lookup_includes_nested_technology_and_translation(self):
        result = query_unciv_data.query(
            "Civ V - Gods & Kings", kind="Techs", name="Agriculture", language="zh",
        )
        self.assertEqual(result["reference_version"], "4.22.0")
        self.assertEqual(result["matches"][0]["path"], "$[0].techs[0]")
        self.assertEqual(result["matches"][0]["translation"], "农业")
        self.assertIn("Techs.json", result["source_url"])

    def test_type_alias_and_global_search(self):
        result = query_unciv_data.query("Civ V - Vanilla", kind="technology", name="Agriculture")
        self.assertEqual(result["type"], "Techs")
        self.assertEqual(len(result["matches"]), 1)

        religion = query_unciv_data.query("Civ V - Gods & Kings", kind="Religions", name="Buddhism")
        self.assertEqual(religion["matches"][0]["name"], "Buddhism")
        self.assertIn("Religions.json", religion["matches"][0]["source_url"])

        tutorial = query_unciv_data.query("Civ V - Gods & Kings", kind="tutorials", search="Move unit")
        self.assertEqual(tutorial["type"], "Events")
        self.assertTrue(tutorial["matches"])

        global_result = query_unciv_data.query("Civ V - Gods & Kings", search="barbarian")
        self.assertTrue(global_result["matches"])
        self.assertTrue(any(item["type"] == "Difficulties" for item in global_result["matches"]))
        self.assertTrue(all(item["source_url"] for item in global_result["matches"]))

    def test_query_requires_a_selector_and_name_requires_type(self):
        with self.assertRaisesRegex(ValueError, "provide --name or --search"):
            query_unciv_data.query("Civ V - Gods & Kings", kind="Techs")
        with self.assertRaisesRegex(ValueError, "requires --type"):
            query_unciv_data.query("Civ V - Gods & Kings", name="Agriculture")

    def test_unknown_type_reports_available_choices(self):
        with self.assertRaisesRegex(ValueError, "Unknown data type"):
            query_unciv_data.query("Civ V - Gods & Kings", kind="NotAType", search="x")


if __name__ == "__main__":
    unittest.main()
