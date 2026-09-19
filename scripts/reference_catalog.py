#!/usr/bin/env python3
"""Resolve the current bundled Unciv validation data by base ruleset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = PROJECT_ROOT / "references" / "versions" / "index.json"


def load_catalog(index_path: Path = DEFAULT_INDEX) -> dict[str, Any]:
    try:
        catalog = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read reference version index {index_path}: {error}") from error
    if (
        catalog.get("schema_version") != 1
        or not isinstance(catalog.get("versions"), dict)
        or not isinstance(catalog.get("current_reference_version"), str)
    ):
        raise ValueError(f"Unsupported reference version index: {index_path}")
    return catalog


def _project_path(value: str) -> Path:
    return PROJECT_ROOT / value


def available_rulesets(index_path: Path = DEFAULT_INDEX) -> tuple[str, ...]:
    """Return the rulesets available in the current reference bundle."""
    catalog = load_catalog(index_path)
    version = catalog["current_reference_version"]
    try:
        rulesets = catalog["versions"][version]["rulesets"]
    except KeyError as error:
        raise ValueError(f"Current reference version {version!r} is unavailable") from error
    return tuple(sorted(rulesets))


def resolve_bundle(
    base_ruleset: str | None = None,
    index_path: Path = DEFAULT_INDEX,
) -> dict[str, Any]:
    catalog = load_catalog(index_path)
    version = catalog.get("current_reference_version")
    versions = catalog["versions"]
    if version not in versions:
        available = ", ".join(sorted(versions))
        raise ValueError(f"Current reference version {version!r} is unavailable; available provenance: {available}")
    version_entry = versions[version]
    rulesets = version_entry.get("rulesets", {})
    ruleset = base_ruleset or version_entry.get("default_ruleset")
    if ruleset not in rulesets:
        available = ", ".join(sorted(rulesets))
        raise ValueError(f"No bundled {version} baseline for {ruleset!r}; available: {available}")
    return {
        "reference_version": version,
        "reference_build": version_entry.get("game_build"),
        "base_ruleset": ruleset,
        "schema_dir": _project_path(version_entry["schema_dir"]),
        "base_rules_data": _project_path(rulesets[ruleset]["rules"]),
        "baseline_manifest": _project_path(rulesets[ruleset]["manifest"]),
        "mechanics_registry": _project_path(version_entry["mechanics_registry"]),
        "schema_exceptions": _project_path(version_entry["schema_exceptions"]),
        "index_path": index_path,
    }
