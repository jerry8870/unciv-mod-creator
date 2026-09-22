#!/usr/bin/env python3
"""Query the bundled Unciv Civilopedia-style rules data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import reference_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# These aliases make the command convenient for common Civilopedia wording while
# keeping the canonical names equal to the JSON rule-file names.
TYPE_ALIASES = {
    "belief": "Beliefs",
    "beliefs": "Beliefs",
    "building": "Buildings",
    "buildings": "Buildings",
    "difficulty": "Difficulties",
    "difficulties": "Difficulties",
    "game difficulty": "Difficulties",
    "era": "Eras",
    "eras": "Eras",
    "event": "Events",
    "events": "Events",
    "tutorial": "Events",
    "tutorials": "Events",
    "improvement": "TileImprovements",
    "improvements": "TileImprovements",
    "civilization": "Nations",
    "civilizations": "Nations",
    "nations": "Nations",
    "nation": "Nations",
    "personality": "Personalities",
    "personalities": "Personalities",
    "policy": "Policies",
    "policies": "Policies",
    "promotion": "UnitPromotions",
    "promotions": "UnitPromotions",
    "quest": "Quests",
    "quests": "Quests",
    "religion": "Religions",
    "religions": "Religions",
    "resource": "TileResources",
    "resources": "TileResources",
    "ruin": "Ruins",
    "ruins": "Ruins",
    "specialist": "Specialists",
    "specialists": "Specialists",
    "speed": "Speeds",
    "speeds": "Speeds",
    "technology": "Techs",
    "technologies": "Techs",
    "tech": "Techs",
    "techs": "Techs",
    "terrain": "Terrains",
    "terrains": "Terrains",
    "unit": "Units",
    "units": "Units",
    "unit name groups": "UnitNameGroups",
    "unitnamegroups": "UnitNameGroups",
    "unit names": "UnitNameGroups",
    "ways to win": "VictoryTypes",
    "victory method": "VictoryTypes",
    "unit types": "UnitTypes",
    "unittypes": "UnitTypes",
    "victory": "VictoryTypes",
    "victories": "VictoryTypes",
    "victory types": "VictoryTypes",
    "victorytypes": "VictoryTypes",
}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read bundled reference {path}: {error}") from error


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def _normalise_type(value: str, available: tuple[str, ...]) -> str:
    by_lower = {name.casefold(): name for name in available}
    key = " ".join(value.strip().casefold().split())
    canonical = by_lower.get(key) or TYPE_ALIASES.get(key)
    if canonical not in available:
        choices = ", ".join(available)
        raise ValueError(f"Unknown data type {value!r}; choose one of: {choices}")
    return canonical


def _iter_named(value: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[tuple[Any, ...], dict[str, Any]]]:
    """Yield every named object, including nested Tech and Policy entries."""
    if isinstance(value, dict):
        if isinstance(value.get("name"), str):
            yield path, value
        for key, child in value.items():
            yield from _iter_named(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_named(child, path + (index,))


def _iter_records(
    value: Any,
    path: tuple[Any, ...] = (),
    nested: bool = False,
) -> Iterator[tuple[tuple[Any, ...], Any, str | None]]:
    """Yield named objects and primitive entries such as the Religions list."""
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str):
            yield path, value, name
        elif path == ():
            # Categories such as ModOptions are a single unnamed object.
            yield path, value, None
        for key, child in value.items():
            if isinstance(child, (dict, list)):
                yield from _iter_records(child, path + (key,), True)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if isinstance(child, (dict, list)):
                yield from _iter_records(child, path + (index,), nested)
            elif not nested:
                yield path + (index,), child, str(child) if isinstance(child, str) else None
    elif not nested:
        yield path, value, str(value) if isinstance(value, str) else None


def _path_text(path: tuple[Any, ...]) -> str:
    result = "$"
    for part in path:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def _contains_text(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_text(key, needle) or _contains_text(child, needle) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_text(child, needle) for child in value)
    return needle in str(value).casefold()


def _translation(translations: dict[str, Any], name: str, language: str) -> str | None:
    if language == "en":
        return name
    value = translations.get(name)
    return value if isinstance(value, str) and value else None


def _source_for_type(manifest: dict[str, Any], kind: str) -> str | None:
    for relative, metadata in manifest.get("sources", {}).items():
        if relative.endswith(f"/{kind}.json") and isinstance(metadata, dict):
            url = metadata.get("url")
            if isinstance(url, str):
                return url
    return None


def load_bundle(base_ruleset: str | None = None) -> dict[str, Any]:
    """Load a ruleset snapshot and its provenance metadata."""
    bundle = reference_catalog.resolve_bundle(base_ruleset)
    rules = _read_json(bundle["base_rules_data"])
    manifest = _read_json(bundle["baseline_manifest"])
    if not isinstance(rules, dict) or not isinstance(manifest, dict):
        raise ValueError(f"Invalid bundled reference for {bundle['base_ruleset']!r}")
    translations_path = bundle["base_rules_data"].with_name("zh.json")
    translations = _read_json(translations_path) if translations_path.is_file() else {}
    if not isinstance(translations, dict):
        raise ValueError(f"Invalid translation snapshot {translations_path}")
    return {
        **bundle,
        "rules": rules,
        "manifest": manifest,
        "translations": translations,
        "translations_path": translations_path,
    }


def list_types(base_ruleset: str | None = None) -> dict[str, Any]:
    bundle = load_bundle(base_ruleset)
    types = []
    for kind in sorted(bundle["rules"]):
        value = bundle["rules"][kind]
        named_count = sum(1 for _path, _record in _iter_named(value))
        entry_count = sum(1 for _path, _record, _name in _iter_records(value))
        types.append({
            "type": kind,
            "records": len(value) if isinstance(value, list) else None,
            "entries": entry_count,
            "named_entries": named_count,
            "source_url": _source_for_type(bundle["manifest"], kind),
        })
    return {
        "ruleset": bundle["base_ruleset"],
        "reference_version": bundle["reference_version"],
        "reference_build": bundle.get("reference_build"),
        "types": types,
    }


def query(
    base_ruleset: str | None = None,
    *,
    kind: str | None = None,
    name: str | None = None,
    search: str | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Return matching named entries and their source metadata."""
    if language not in {"en", "zh"}:
        raise ValueError("language must be 'en' or 'zh'")
    if name and search:
        raise ValueError("--name and --search are mutually exclusive")
    if name is not None and not name.strip():
        raise ValueError("--name cannot be blank")
    if search is not None and not search.strip():
        raise ValueError("--search cannot be blank")
    if not name and not search:
        raise ValueError("provide --name or --search (or use --list-types)")
    if name and not kind:
        raise ValueError("--name requires --type so the lookup is unambiguous")

    bundle = load_bundle(base_ruleset)
    canonical_kind = _normalise_type(kind, tuple(bundle["rules"])) if kind else None
    candidates = [(canonical_kind, bundle["rules"][canonical_kind])] if canonical_kind else list(bundle["rules"].items())
    matches = []
    for candidate_kind, value in candidates:
        source_url = _source_for_type(bundle["manifest"], candidate_kind)
        for path, record, record_name in _iter_records(value):
            if name and (not record_name or record_name.casefold() != name.strip().casefold()):
                continue
            if search and not _contains_text(record, search.strip().casefold()):
                continue
            matches.append({
                "type": candidate_kind,
                "path": _path_text(path),
                "name": record_name,
                "translation": _translation(bundle["translations"], record_name, language) if record_name else None,
                "source_url": source_url,
                "record": record,
            })

    return {
        "ruleset": bundle["base_ruleset"],
        "reference_version": bundle["reference_version"],
        "reference_build": bundle.get("reference_build"),
        "language": language,
        "type": canonical_kind,
        "query": {"name": name, "search": search},
        "local_snapshot": _relative_path(bundle["base_rules_data"]),
        "translation_snapshot": _relative_path(bundle["translations_path"]),
        "source_url": _source_for_type(bundle["manifest"], canonical_kind) if canonical_kind else None,
        "source_commit": bundle["manifest"].get("source_commit"),
        "matches": matches,
    }


def format_human(result: dict[str, Any]) -> str:
    lines = [
        f"Ruleset: {result['ruleset']}",
        f"Reference: {result['reference_version']} (provenance)",
    ]
    if "types" in result:
        lines.append("Types:")
        for item in result["types"]:
            count = item["entries"]
            source = item["source_url"] or "source URL unavailable"
            lines.append(f"- {item['type']}: {count} entries | {source}")
        return "\n".join(lines)

    lines.extend([
        f"Type: {result['type'] or 'all types'}",
        f"Local snapshot: {result['local_snapshot']}",
        f"Translation snapshot: {result['translation_snapshot']}",
        f"Source: {result['source_url'] or 'use the category source tree'}",
        f"Matches: {len(result['matches'])}",
    ])
    for match in result["matches"]:
        label = match["name"] or "(unnamed entry)"
        lines.append(f"\n- {label} ({match['type']}, {match['path']})")
        if not result["type"] and match["source_url"]:
            lines.append(f"  Source: {match['source_url']}")
        if result["language"] == "zh":
            lines.append(f"  Translation: {match['translation'] or '未找到中文翻译'}")
        lines.append("  Data:")
        data = json.dumps(match["record"], ensure_ascii=False, indent=2)
        lines.extend(f"  {line}" for line in data.splitlines())
    return "\n".join(lines)


def run_cli(
    *,
    base_ruleset: str | None = None,
    kind: str | None = None,
    name: str | None = None,
    search: str | None = None,
    language: str = "en",
    show_types: bool = False,
    as_json: bool = False,
) -> int:
    result = list_types(base_ruleset) if show_types else query(
        base_ruleset, kind=kind, name=name, search=search, language=language,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2) if as_json else format_human(result))
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ruleset")
    parser.add_argument("--type", dest="kind")
    parser.add_argument("--name")
    parser.add_argument("--search")
    parser.add_argument("--language", choices=("en", "zh"), default="en")
    parser.add_argument("--list-types", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    raise SystemExit(run_cli(**vars(args)))
