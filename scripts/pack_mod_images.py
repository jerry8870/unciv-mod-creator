#!/usr/bin/env python3
"""Pack Unciv Mod image folders into LibGDX texture atlases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from validate_mod_assets import Finding, has_errors, inspect_mod_assets, print_findings


GDX_VERSION = "1.14.2"
ARTIFACTS = {
    "gdx-tools": "b47593a5a5329d7db7b9c218fc45f744cbcb7a2d256dba362c40546d3b9905af",
    "gdx": "a835710bb135c2c687723b9474d5620f8158af90a96e07ce492f6169d7eee8cc",
}
MAVEN_BASE = "https://repo.maven.apache.org/maven2/com/badlogicgames/gdx"
IMAGE_PACKER_CLASS = "com.badlogic.gdx.tools.texturepacker.TexturePacker"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified(path: Path, artifact: str) -> bool:
    try:
        return sha256(path) == ARTIFACTS[artifact]
    except OSError:
        return False


def find_gradle_jar(artifact: str) -> Path | None:
    pattern = (
        Path.home()
        / ".gradle/caches/modules-2/files-2.1/com.badlogicgames.gdx"
        / artifact
        / GDX_VERSION
    )
    for candidate in pattern.glob(f"*/{artifact}-{GDX_VERSION}.jar"):
        if _verified(candidate, artifact):
            return candidate
    return None


def dependency_jar(artifact: str) -> Path:
    cached = find_gradle_jar(artifact)
    if cached:
        return cached

    cache_dir = Path.home() / ".cache/unciv-mod-creator/libgdx" / GDX_VERSION
    jar_path = cache_dir / f"{artifact}-{GDX_VERSION}.jar"
    if _verified(jar_path, artifact):
        return jar_path

    cache_dir.mkdir(parents=True, exist_ok=True)
    url = f"{MAVEN_BASE}/{artifact}/{GDX_VERSION}/{artifact}-{GDX_VERSION}.jar"
    temporary_path = jar_path.with_suffix(".jar.part")
    try:
        with urlopen(url, timeout=30) as response, temporary_path.open("wb") as output:
            shutil.copyfileobj(response, output)
    except (OSError, URLError) as error:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"Could not download {artifact} {GDX_VERSION} from Maven Central: {error}") from error
    if not _verified(temporary_path, artifact):
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"SHA-256 check failed for {artifact} {GDX_VERSION}")
    temporary_path.replace(jar_path)
    return jar_path


def pack_mod_images(mod_dir: Path, tools_jar: Path, gdx_jar: Path) -> list[Finding]:
    mod_dir = mod_dir.resolve()
    roots, findings = inspect_mod_assets(mod_dir, require_packed=False)
    if has_errors(findings):
        raise ValueError("Source image validation failed; fix the reported paths or image files first")
    populated_roots = [root for root in roots if root.images]
    if not populated_roots:
        raise ValueError("No packable images found under Images or Images.<AtlasName>")
    atlas_names = sorted({root.atlas_name for root in populated_roots})
    for atlas_name in atlas_names:
        for other_name in atlas_names:
            folded_other = other_name.casefold()
            folded_atlas = atlas_name.casefold()
            suffix = folded_other[len(folded_atlas):] if folded_other.startswith(folded_atlas) else ""
            if suffix.isdigit() and suffix == suffix.lstrip("0") and (len(suffix) > 1 or suffix >= "2"):
                raise ValueError(f"Atlas {other_name} could collide with an overflow page from atlas {atlas_name}; rename one Images folder")

    classpath = os.pathsep.join((str(tools_jar.resolve()), str(gdx_jar.resolve())))
    with tempfile.TemporaryDirectory(prefix="unciv-atlas-settings-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for index, root in enumerate(populated_roots):
            settings_file = root.path / "TexturePacker.settings"
            if not settings_file.is_file():
                settings_file = temporary_root / f"settings-{index}.json"
                settings = {
                    "pot": True,
                    "maxWidth": 2048,
                    "maxHeight": 2048,
                    "combineSubdirectories": True,
                    "fast": True,
                    "paddingX": 8,
                    "paddingY": 8,
                    "duplicatePadding": True,
                    "filterMin": "MipMapLinearLinear",
                    "filterMag": "Linear" if root.atlas_name.endswith("Icons") else "MipMapLinearLinear",
                }
                settings_file.write_text(json.dumps(settings), encoding="utf-8")

            command = [
                "java", "-cp", classpath, IMAGE_PACKER_CLASS,
                str(root.path.resolve()), str(mod_dir), root.atlas_name, str(settings_file.resolve()),
            ]
            result = subprocess.run(command, check=False)
            if result.returncode:
                raise RuntimeError(f"LibGDX TexturePacker failed for {root.path.name} (exit {result.returncode})")

    (mod_dir / "Atlases.json").write_text(json.dumps(atlas_names, separators=(",", ":")), encoding="utf-8")
    _, findings = inspect_mod_assets(mod_dir, require_packed=True)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mod_dir", type=Path, help="path to the Mod folder")
    args = parser.parse_args()
    mod_dir = args.mod_dir.expanduser().resolve()

    roots, source_findings = inspect_mod_assets(mod_dir, require_packed=False)
    atlas_names = sorted({root.atlas_name for root in roots if root.images})
    if source_findings:
        print_findings(mod_dir, source_findings)
    if has_errors(source_findings):
        return 1

    try:
        if shutil.which("java") is None:
            raise RuntimeError("Java is required to run the LibGDX texture packer")
        findings = pack_mod_images(mod_dir, dependency_jar("gdx-tools"), dependency_jar("gdx"))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print_findings(mod_dir, findings)
    if has_errors(findings):
        return 1
    print("Generated atlas files: " + ", ".join(atlas_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
