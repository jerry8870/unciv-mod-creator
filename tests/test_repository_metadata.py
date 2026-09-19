import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class RepositoryMetadataTests(unittest.TestCase):
    def test_skill_frontmatter_has_required_fields(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---\n", 2)[1]
        self.assertIn("name: unciv-mod-creator", frontmatter)
        self.assertIn("description:", frontmatter)

    def test_readmes_link_to_each_other(self):
        english = (SKILL_DIR / "README.md").read_text(encoding="utf-8")
        chinese = (SKILL_DIR / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("](README.zh-CN.md)", english)
        self.assertIn("](README.md)", chinese)
        self.assertNotIn("codex", english.casefold())
        self.assertNotIn("codex", chinese.casefold())
        self.assertNotIn("--game-version", english)
        self.assertNotIn("--game-version", chinese)
        self.assertIn("## What This Skill Can Do", english)
        self.assertIn("## 这个 Skill 能做什么", chinese)


if __name__ == "__main__":
    unittest.main()
