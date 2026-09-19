import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import pack_mod_images as packer
import validate_mod_assets as assets


def write_png(path: Path, width: int = 16, height: int = 16) -> None:
    def chunk(name: bytes, content: bytes) -> bytes:
        return (
            struct.pack(">I", len(content))
            + name
            + content
            + struct.pack(">I", zlib.crc32(name + content) & 0xFFFFFFFF)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = (b"\x00" + b"\x20\x40\x80\xff" * width) * height
    content = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(content)


class ModAssetTests(unittest.TestCase):
    def test_source_checks_case_and_png_header(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            wrong_root_mod = base / "WrongRoot"
            write_png(wrong_root_mod / "images" / "NationIcons" / "LowercaseRoot.png")
            _, root_findings = assets.inspect_mod_assets(wrong_root_mod, require_packed=False)

            mod_dir = base / "TypeCase"
            bad_image = mod_dir / "Images" / "Nationicons" / "Egypt.png"
            bad_image.parent.mkdir(parents=True, exist_ok=True)
            bad_image.write_bytes(b"not a png")
            (bad_image.parent / "WrongExtension.PNG").write_bytes(b"not a png")

            _, findings = assets.inspect_mod_assets(mod_dir, require_packed=False)
            errors = [finding.message for finding in root_findings + findings if finding.severity == "ERROR"]

            self.assertTrue(any("case-sensitive folder name" in message for message in errors))
            self.assertTrue(any("Image type directory case" in message for message in errors))
            self.assertTrue(any("lowercase image extension" in message for message in errors))
            self.assertTrue(any("PNG header is invalid" in message for message in errors))

            nested_mod = base / "TooDeep"
            write_png(nested_mod / "Images" / "NationIcons" / "Nested" / "Egypt.png")
            _, findings = assets.inspect_mod_assets(nested_mod, require_packed=False)
            self.assertTrue(any("Expected NationIcons/<ObjectName>.png" in finding.message for finding in findings))

            tileset_mod = base / "Tileset"
            write_png(tileset_mod / "Images" / "TileSets" / "Example" / "Units" / "Warrior.png")
            _, findings = assets.inspect_mod_assets(tileset_mod, require_packed=False)
            self.assertFalse(assets.has_errors(findings), [finding.message for finding in findings])

    def test_full_validation_requires_packed_atlas(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Example"
            write_png(mod_dir / "Images" / "NationIcons" / "Egypt.png")

            _, findings = assets.inspect_mod_assets(mod_dir)

            self.assertTrue(any("game.atlas" in str(finding.path) for finding in findings if finding.severity == "ERROR"))

    def test_checks_civilization_icon_dimensions(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Example"
            write_png(mod_dir / "Images" / "NationIcons" / "Tideward.png", width=90, height=100)
            write_png(mod_dir / "Images" / "UnitIcons" / "Tidewarder.png")
            write_png(mod_dir / "Images" / "BuildingIcons" / "Harbor Exchange.png")

            _, findings = assets.inspect_mod_assets(mod_dir, require_packed=False)
            errors = [finding.message for finding in findings if finding.severity == "ERROR"]

            self.assertTrue(any("Expected a 100x100 PNG" in message for message in errors))
            self.assertEqual(sum("Expected a 200x200 PNG" in message for message in errors), 2)

    def test_rejects_atlas_name_that_can_collide_with_overflow_page(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Example"
            write_png(mod_dir / "Images" / "NationIcons" / "Egypt.png", width=100, height=100)
            write_png(mod_dir / "Images.game2" / "OtherIcons" / "Link.png")

            with self.assertRaisesRegex(ValueError, "overflow page"):
                packer.pack_mod_images(mod_dir, Path("missing-tools.jar"), Path("missing-gdx.jar"))

            self.assertFalse((mod_dir / "game.atlas").exists())

    def test_packs_and_validates_default_and_named_atlases(self):
        tools_jar = packer.find_gradle_jar("gdx-tools")
        gdx_jar = packer.find_gradle_jar("gdx")
        if not tools_jar or not gdx_jar:
            self.skipTest("LibGDX jars are not in the local Gradle cache")

        with tempfile.TemporaryDirectory() as temporary_directory:
            mod_dir = Path(temporary_directory) / "Example"
            write_png(mod_dir / "Images" / "NationIcons" / "New Nation.png", width=100, height=100)
            write_png(mod_dir / "Images.UI" / "OtherIcons" / "Link.png")
            write_png(mod_dir / "Images.UI" / "OtherIcons" / "More.png", width=15)
            settings = {"filterMag": "Linear", "maxWidth": 32, "maxHeight": 32, "paddingX": 8, "paddingY": 8}
            (mod_dir / "Images.UI" / "TexturePacker.settings").write_text(json.dumps(settings))

            findings = packer.pack_mod_images(mod_dir, tools_jar, gdx_jar)

            self.assertFalse(assets.has_errors(findings), [finding.message for finding in findings])
            self.assertEqual(json.loads((mod_dir / "Atlases.json").read_text()), ["UI", "game"])
            _, regions = assets._read_atlas(mod_dir / "game.atlas", [])
            self.assertIn("NationIcons/New Nation", regions)
            pages, regions = assets._read_atlas(mod_dir / "UI.atlas", [])
            self.assertIn("OtherIcons/Link", regions)
            self.assertIn("OtherIcons/More", regions)
            self.assertIn("UI2.png", pages)
            self.assertTrue((mod_dir / "UI2.png").is_file())
            self.assertIn("filter: Nearest, Linear", (mod_dir / "UI.atlas").read_text())

            source = mod_dir / "Images" / "NationIcons" / "New Nation.png"
            newer_time = (mod_dir / "game.atlas").stat().st_mtime_ns + 2_000_000_000
            os.utime(source, ns=(newer_time, newer_time))
            _, findings = assets.inspect_mod_assets(mod_dir)
            self.assertTrue(any("Sources newer than this atlas" in finding.message for finding in findings))

            (mod_dir / "Atlases.json").write_text('["wrong"]')
            _, findings = assets.inspect_mod_assets(mod_dir)
            self.assertTrue(any("Atlas names must be exactly" in finding.message for finding in findings))


if __name__ == "__main__":
    unittest.main()
