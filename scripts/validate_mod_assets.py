#!/usr/bin/env python3
"""Check Unciv Mod image paths, source files, and packed atlas outputs."""

from __future__ import annotations

import argparse
import json
import os
import struct
from dataclasses import dataclass
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
KNOWN_IMAGE_TYPES = {
    name.casefold(): name
    for name in (
        "BuildingIcons", "BuildingPortraits", "CityStateIcons", "ConstructionIcons", "EmojiIcons",
        "ImprovementIcons", "ImprovementPortraits", "LeaderIcons", "MayaCalendar",
        "NationIcons", "NationPortraits", "OtherIcons", "PolicyBranchIcons", "PolicyIcons", "ReligionIcons",
        "ReligionPortraits", "ResourceIcons", "ResourcePortraits", "Skins",
        "StatIcons", "TechIcons", "TechPortraits", "TileIcons", "UnitActionPortraits",
        "UnitIcons", "UnitPortraits", "UnitPromotionIcons", "UnitPromotionPortraits",
        "UnitTypeIcons", "UniquePortraits", "VictoryIllustrations", "WonderImages", "TileSets",
    )
}
NESTED_IMAGE_TYPES = {"skins", "tilesets", "uniticons", "victoryillustrations"}
ICON_SIZES = {"nationicons": (100, 100), "uniticons": (200, 200), "buildingicons": (200, 200)}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass
class ImageRoot:
    path: Path
    atlas_name: str
    images: list[Path]


@dataclass
class Finding:
    severity: str
    path: Path
    message: str
    code: str = ""
    suggestion: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            self.code = _asset_diagnostic_code(self.message)


def _asset_diagnostic_code(message: str) -> str:
    if "No Images" in message or "No packable image" in message:
        return "ASSET_NOT_PRESENT"
    if "PNG" in message:
        return "ASSET_PNG_INVALID"
    if "case-sensitive" in message or "differs only by letter case" in message or "directory case" in message:
        return "ASSET_PATH_CASE_ERROR"
    if "atlas" in message.casefold() or "Packed regions" in message:
        return "ASSET_ATLAS_INVALID"
    if "symlink" in message:
        return "ASSET_SYMLINK_FORBIDDEN"
    return "ASSET_VALIDATION"


def inspect_mod_assets(mod_dir: Path, require_packed: bool = True) -> tuple[list[ImageRoot], list[Finding]]:
    findings: list[Finding] = []
    if not mod_dir.is_dir():
        return [], [Finding("ERROR", mod_dir, "Mod folder does not exist or is not a directory")]

    roots: list[ImageRoot] = []
    atlas_names: dict[str, ImageRoot] = {}
    for entry in sorted(mod_dir.iterdir(), key=lambda path: path.name.casefold()):
        folded = entry.name.casefold()
        if folded != "images" and not folded.startswith("images."):
            continue
        if entry.name != "Images" and not entry.name.startswith("Images."):
            findings.append(Finding("ERROR", entry, "Use the case-sensitive folder name Images or Images.<AtlasName>"))
            continue
        if entry.is_symlink() or not entry.is_dir():
            findings.append(Finding("ERROR", entry, "Image root must be a real directory, not a symlink"))
            continue

        atlas_name = "game" if entry.name == "Images" else entry.name[len("Images."):]
        if not atlas_name or "." in atlas_name or "/" in atlas_name or "\\" in atlas_name or not atlas_name.isascii():
            findings.append(Finding("ERROR", entry, "Atlas name must be one non-empty ASCII path name without dots or separators"))
        folded_atlas = atlas_name.casefold()
        if folded_atlas in atlas_names:
            findings.append(Finding("ERROR", entry, f"Atlas name conflicts with {atlas_names[folded_atlas].path.name}"))
        else:
            atlas_names[folded_atlas] = ImageRoot(entry, atlas_name, [])

        root = ImageRoot(entry, atlas_name, [])
        roots.append(root)
        _scan_image_root(root, findings)

    if not roots:
        findings.append(Finding("INFO", mod_dir, "No Images or Images.<AtlasName> folders found"))
    elif not any(root.images for root in roots):
        findings.append(Finding("INFO", mod_dir, "No packable image files found"))

    if require_packed:
        _validate_packed_outputs(mod_dir, roots, findings)
    return roots, findings


def _scan_image_root(root: ImageRoot, findings: list[Finding]) -> None:
    seen_paths: dict[str, str] = {}
    for current, directories, filenames in os.walk(root.path, topdown=True, followlinks=False):
        current_path = Path(current)
        for directory in list(directories):
            entry = current_path / directory
            if directory.startswith("."):
                directories.remove(directory)
                continue
            if directory.casefold() == "texturepacker.settings":
                findings.append(Finding("ERROR", entry, "TexturePacker.settings must be a file at the Images folder root"))
            if entry.is_symlink():
                findings.append(Finding("ERROR", entry, "Image folders cannot be symlinks"))
                directories.remove(directory)
                continue
            _check_relative_path(root, entry.relative_to(root.path), seen_paths, findings)

        for filename in filenames:
            path = current_path / filename
            relative = path.relative_to(root.path)
            if filename.startswith("."):
                continue
            if path.is_symlink():
                findings.append(Finding("ERROR", path, "Image files cannot be symlinks"))
                continue
            _check_relative_path(root, relative, seen_paths, findings)

            if filename.casefold() == "texturepacker.settings":
                if filename != "TexturePacker.settings" or path.parent != root.path:
                    findings.append(Finding("ERROR", path, "Use the exact filename TexturePacker.settings at the Images folder root"))
                continue
            suffix = path.suffix
            if suffix.lower() not in IMAGE_SUFFIXES:
                findings.append(Finding("WARNING", path, "Non-image file under Images; move it outside the atlas source folder"))
                continue
            if suffix != suffix.lower():
                findings.append(Finding("ERROR", path, "Use a lowercase image extension such as .png"))
                continue
            if len(relative.parts) < 2:
                findings.append(Finding("ERROR", path, "Expected <ImageType>/<ObjectName>.png under the Images folder"))
            image_type = relative.parts[0]
            expected_type = KNOWN_IMAGE_TYPES.get(image_type.casefold())
            if expected_type and image_type != expected_type:
                findings.append(Finding("ERROR", path, f"Image type directory case must be {expected_type}"))
            elif expected_type and expected_type.casefold() not in NESTED_IMAGE_TYPES and len(relative.parts) != 2:
                findings.append(Finding("ERROR", path, f"Expected {expected_type}/<ObjectName>.png under the Images folder"))
            elif not expected_type:
                findings.append(Finding("INFO", path, "Confirm this image type directory against the official guide; it is not in the bundled common-type list"))
            if suffix == ".png":
                _check_png_header(path, findings, ICON_SIZES.get(image_type.casefold()))
            else:
                findings.append(Finding("WARNING", path, "Unciv's documented object-image convention uses .png; LibGDX can pack JPEG files"))
            root.images.append(path)


def _check_relative_path(root: ImageRoot, relative: Path, seen_paths: dict[str, str], findings: list[Finding]) -> None:
    value = relative.as_posix()
    if not value.isascii():
        findings.append(Finding("ERROR", root.path / relative, "Atlas image paths and names must use ASCII characters"))
    if "\\" in value:
        findings.append(Finding("ERROR", root.path / relative, "Do not use backslashes in atlas paths"))
    folded = value.casefold()
    if folded in seen_paths and seen_paths[folded] != value:
        findings.append(Finding("ERROR", root.path / relative, f"Path differs only by letter case from {seen_paths[folded]}"))
    else:
        seen_paths[folded] = value


def _check_png_header(path: Path, findings: list[Finding], expected_size: tuple[int, int] | None = None) -> None:
    try:
        with path.open("rb") as image:
            header = image.read(24)
    except OSError as error:
        findings.append(Finding("ERROR", path, f"Cannot read image: {error}"))
        return
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        findings.append(Finding("ERROR", path, "File extension is .png but the PNG header is invalid"))
        return
    width, height = struct.unpack(">II", header[16:24])
    if width == 0 or height == 0:
        findings.append(Finding("ERROR", path, "PNG width and height must be greater than zero"))
    elif expected_size and (width, height) != expected_size:
        findings.append(Finding("ERROR", path, f"Expected a {expected_size[0]}x{expected_size[1]} PNG, found {width}x{height}"))


def _validate_packed_outputs(mod_dir: Path, roots: list[ImageRoot], findings: list[Finding]) -> None:
    packed_roots = [root for root in roots if root.images]
    if not packed_roots:
        return

    expected_atlases = sorted({root.atlas_name for root in packed_roots})
    for root in packed_roots:
        atlas_path = mod_dir / f"{root.atlas_name}.atlas"
        if not atlas_path.is_file() or atlas_path.stat().st_size == 0:
            findings.append(Finding("ERROR", atlas_path, "Packed atlas is missing or empty; run pack_mod_images.py"))
            continue
        atlas_mtime = atlas_path.stat().st_mtime_ns
        source_files = list(root.images)
        settings_file = root.path / "TexturePacker.settings"
        if settings_file.is_file():
            source_files.append(settings_file)
        newer_files = []
        for source in source_files:
            try:
                if source.stat().st_mtime_ns > atlas_mtime:
                    newer_files.append(source.relative_to(mod_dir).as_posix())
            except OSError as error:
                findings.append(Finding("ERROR", source, f"Cannot check source timestamp: {error}"))
        if newer_files:
            findings.append(Finding("ERROR", atlas_path, "Sources newer than this atlas; repack: " + ", ".join(newer_files[:5])))
        pages, regions = _read_atlas(atlas_path, findings)
        if not regions:
            findings.append(Finding("ERROR", atlas_path, "Atlas contains no image regions"))
        for page in pages:
            if Path(page).name != page or not (mod_dir / page).is_file():
                findings.append(Finding("ERROR", atlas_path, f"Atlas page image is missing or has an invalid path: {page}"))

        expected_regions: set[str] = set()
        has_nine_patch = False
        for image in root.images:
            name = image.relative_to(root.path).with_suffix("").as_posix()
            if name.endswith(".9"):
                has_nine_patch = True
                continue
            expected_regions.add(name)
        actual_regions = set(regions)
        missing = sorted(expected_regions - actual_regions)
        extra = sorted(actual_regions - expected_regions) if not has_nine_patch else []
        if missing or extra:
            details = []
            if missing:
                details.append("missing regions: " + ", ".join(missing[:5]))
            if extra:
                details.append("unexpected regions: " + ", ".join(extra[:5]))
            findings.append(Finding("ERROR", atlas_path, "Packed regions do not match source image paths (" + "; ".join(details) + ")"))

    control_files = [path for path in mod_dir.iterdir() if path.name.casefold() == "atlases.json"]
    for path in control_files:
        if path.name != "Atlases.json":
            findings.append(Finding("ERROR", path, "Control file name is case-sensitive: use Atlases.json"))
        if path.is_symlink():
            findings.append(Finding("ERROR", path, "Atlases.json cannot be a symlink"))

    control_file = mod_dir / "Atlases.json"
    must_list_atlases = len(expected_atlases) > 1 or expected_atlases != ["game"]
    if not control_file.exists():
        if must_list_atlases:
            findings.append(Finding("ERROR", control_file, "Required for non-default or multiple atlases"))
        return
    try:
        content = control_file.read_bytes()
        if content.startswith(b"\xef\xbb\xbf"):
            raise ValueError("UTF-8 byte order mark is not supported")
        names = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        findings.append(Finding("ERROR", control_file, f"Invalid Atlases.json: {error}"))
        return
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        findings.append(Finding("ERROR", control_file, "Expected a JSON array of atlas-name strings"))
    elif len(names) != len(set(names)) or sorted(names) != expected_atlases:
        findings.append(Finding("ERROR", control_file, f"Atlas names must be exactly {json.dumps(expected_atlases)}"))


def _read_atlas(path: Path, findings: list[Finding]) -> tuple[list[str], list[str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        findings.append(Finding("ERROR", path, f"Cannot read atlas as UTF-8: {error}"))
        return [], []

    pages: list[str] = []
    regions: list[str] = []
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if not line or line.startswith((" ", "\t")):
            continue
        if line.endswith(".png") and index + 1 < len(lines) and lines[index + 1].startswith("size:"):
            pages.append(line)
        elif line.partition(":")[0] not in {"size", "format", "filter", "repeat"}:
            regions.append(line)
    return pages, regions


def has_errors(findings: list[Finding]) -> bool:
    return any(finding.severity == "ERROR" for finding in findings)


def print_findings(mod_dir: Path, findings: list[Finding]) -> None:
    if not findings:
        print("Asset validation passed.")
        return
    for finding in findings:
        try:
            location = finding.path.relative_to(mod_dir).as_posix()
        except ValueError:
            location = str(finding.path)
        print(f"[{finding.severity}] {location}: {finding.message}")
    if not has_errors(findings):
        print("Asset validation passed with warnings or informational notes.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mod_dir", type=Path, help="path to the Mod folder")
    parser.add_argument("--source-only", action="store_true", help="check source paths without requiring packed atlases")
    args = parser.parse_args()
    mod_dir = args.mod_dir.expanduser().resolve()
    _, findings = inspect_mod_assets(mod_dir, require_packed=not args.source_only)
    print_findings(mod_dir, findings)
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
