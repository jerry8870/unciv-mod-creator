#!/usr/bin/env python3
"""Refresh the pinned Unciv ruleset baseline and official JSON Schemas."""

from __future__ import annotations

import hashlib
import json
import argparse
import ssl
from datetime import date
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


GAME_VERSION = "4.22.0"
GAME_BUILD = 1297
SOURCE_COMMIT = "518daddf0a06b273f16b481a0464626889307df7"
RULESETS = {
    "Civ V - Gods & Kings": {
        "directory": "gk-baseline",
        "files": (
            "Beliefs", "Buildings", "CityStateTypes", "Difficulties", "Eras", "Events",
            "GlobalUniques", "ModOptions", "Nations", "Personalities", "Policies", "Quests",
            "Religions", "Ruins", "Specialists", "Speeds", "Techs", "Terrains",
            "TileImprovements", "TileResources", "UnitNameGroups", "UnitPromotions",
            "UnitTypes", "Units", "VictoryTypes",
        ),
    },
    "Civ V - Vanilla": {
        "directory": "vanilla-baseline",
        "files": (
            "Buildings", "CityStateTypes", "Difficulties", "Eras", "GlobalUniques",
            "ModOptions", "Nations", "Policies", "Quests", "Ruins", "Specialists", "Speeds",
            "Techs", "Terrains", "TileImprovements", "TileResources", "UnitPromotions",
            "UnitTypes", "Units", "VictoryTypes",
        ),
    },
}
BASE_FILES = (
    "Beliefs", "Buildings", "CityStateTypes", "Difficulties", "Eras", "Events",
    "GlobalUniques", "ModOptions", "Nations", "Personalities", "Policies", "Quests",
    "Religions", "Ruins", "Specialists", "Speeds", "Techs", "Terrains",
    "TileImprovements", "TileResources", "UnitNameGroups", "UnitPromotions",
    "UnitTypes", "Units", "VictoryTypes",
)
SCHEMA_FILES = BASE_FILES + ("TileSetConfig", "Tutorials")
SCHEMA_REFS = ("CivilopediaText", "Color", "Priorities", "Stats", "Uniques")
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPOSITORY_ROOT / "references" / "schemas" / f"unciv-{GAME_VERSION}"
RAW_ROOT = f"https://raw.githubusercontent.com/yairm210/Unciv/{GAME_VERSION}"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _ssl_context() -> ssl.SSLContext:
    candidates = (
        ssl.get_default_verify_paths().cafile,
        "/etc/ssl/cert.pem",
        "/etc/pki/tls/certs/ca-bundle.crt",
    )
    certificate = next((path for path in candidates if path and Path(path).is_file()), None)
    return ssl.create_default_context(cafile=certificate)


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "unciv-mod-creator"})
    with urlopen(request, timeout=30, context=_ssl_context()) as response:
        return response.read()


def strip_json_comments(source: str) -> str:
    """Remove // and /* */ comments without changing string contents."""
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(source):
        char = source[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if source.startswith("//", index):
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            output.extend("\n" for char in source[index:end + 2] if char == "\n")
            index = end + 2
            continue
        output.append(char)
        index += 1
    return "".join(output)


def strip_trailing_commas(source: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(source):
        char = source[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < len(source) and source[lookahead].isspace():
                lookahead += 1
            if lookahead < len(source) and source[lookahead] in "]}":
                index += 1
                continue
        output.append(char)
        index += 1
    return "".join(output)


def parse_upstream_json(content: bytes, source_name: str):
    try:
        normalized = strip_trailing_commas(strip_json_comments(content.decode("utf-8")))
        return json.loads(normalized)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"Cannot parse upstream {source_name}: {error}") from error


def parse_translation(content: bytes) -> dict[str, str]:
    translations: dict[str, str] = {}
    for line_number, raw_line in enumerate(content.decode("utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if " = " not in raw_line:
            continue
        key, value = raw_line.split(" = ", 1)
        if key in translations:
            raise ValueError(f"Duplicate translation key on line {line_number}: {key!r}")
        if value:
            translations[key] = value
    return translations


def update_baseline(ruleset: str) -> None:
    config = RULESETS[ruleset]
    baseline_dir = REPOSITORY_ROOT / "references" / "snapshots" / config["directory"]
    baseline_dir.mkdir(parents=True, exist_ok=True)
    rules: dict[str, object] = {}
    sources: dict[str, dict[str, str]] = {}
    encoded_ruleset = quote(ruleset, safe="")
    for name in config["files"]:
        source_path = f"android/assets/jsons/{ruleset}/{name}.json"
        url = f"{RAW_ROOT}/android/assets/jsons/{encoded_ruleset}/{name}.json"
        content = download(url)
        rules[name] = parse_upstream_json(content, source_path)
        sources[source_path] = {"url": url, "sha256": sha256_bytes(content)}

    translation_path = "android/assets/jsons/translations/Simplified_Chinese.properties"
    translation_url = f"{RAW_ROOT}/{translation_path}"
    translation_content = download(translation_url)
    translations = parse_translation(translation_content)
    sources[translation_path] = {"url": translation_url, "sha256": sha256_bytes(translation_content)}

    rules_path = baseline_dir / "rules.json"
    translations_path = baseline_dir / "zh.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    translations_path.write_text(json.dumps(translations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": 2,
        "ruleset": ruleset,
        "game_version": GAME_VERSION,
        "game_build": GAME_BUILD,
        "source_commit": SOURCE_COMMIT,
        "reviewed_at": date.today().isoformat(),
        "sources": sources,
        "files": {
            "rules.json": sha256_file(rules_path),
            "zh.json": sha256_file(translations_path),
        },
    }
    (baseline_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def update_schemas() -> None:
    refs_dir = SCHEMA_DIR / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    sources: dict[str, dict[str, str]] = {}
    local_files: dict[str, str] = {}
    for name in SCHEMA_FILES:
        relative = f"{name}.schema.json"
        source_path = f"docs/Modders/schemas/{relative}"
        url = f"{RAW_ROOT}/{source_path}"
        content = download(url)
        parse_upstream_json(content, source_path)
        destination = SCHEMA_DIR / relative
        destination.write_bytes(content)
        sources[source_path] = {"url": url, "sha256": sha256_bytes(content)}
        local_files[relative] = sha256_file(destination)
    for name in SCHEMA_REFS:
        relative = f"refs/{name}.schema.json"
        source_path = f"docs/Modders/schemas/{relative}"
        url = f"{RAW_ROOT}/{source_path}"
        content = download(url)
        parse_upstream_json(content, source_path)
        destination = SCHEMA_DIR / relative
        destination.write_bytes(content)
        sources[source_path] = {"url": url, "sha256": sha256_bytes(content)}
        local_files[relative] = sha256_file(destination)
    manifest = {
        "schema_version": 1,
        "game_version": GAME_VERSION,
        "game_build": GAME_BUILD,
        "source_commit": SOURCE_COMMIT,
        "reviewed_at": date.today().isoformat(),
        "sources": sources,
        "files": local_files,
    }
    (SCHEMA_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruleset", choices=tuple(RULESETS), action="append", help="ruleset to refresh; defaults to all")
    parser.add_argument("--skip-schemas", action="store_true")
    args = parser.parse_args()
    selected = args.ruleset or list(RULESETS)
    for ruleset in selected:
        update_baseline(ruleset)
    if not args.skip_schemas:
        update_schemas()
    print(f"Updated {', '.join(selected)} baseline data for Unciv {GAME_VERSION}")


if __name__ == "__main__":
    main()
