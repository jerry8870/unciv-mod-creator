#!/usr/bin/env python3
"""Run structural, reference, translation, and known-mechanic checks on an Unciv Mod."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import reference_catalog


ARRAY_RULE_FILES = {
    "Nations", "Units", "Buildings", "Techs", "Policies", "TileImprovements",
    "TileResources", "UnitPromotions", "UnitTypes",
}
OBJECT_RULE_FILES = {"ModOptions", "GlobalUniques"}
SCHEMA_RULE_FILES = {
    "Beliefs", "Buildings", "CityStateTypes", "Difficulties", "Eras", "Events",
    "GlobalUniques", "ModOptions", "Nations", "Personalities", "Policies", "Quests",
    "Religions", "Ruins", "Specialists", "Speeds", "Techs", "Terrains",
    "TileImprovements", "TileResources", "TileSetConfig", "Tutorials", "UnitNameGroups",
    "UnitPromotions", "UnitTypes", "Units", "VictoryTypes",
}
KNOWN_RULE_FILES = ARRAY_RULE_FILES | OBJECT_RULE_FILES | SCHEMA_RULE_FILES
BASE_TYPES = (
    "Beliefs", "Buildings", "CityStateTypes", "Difficulties", "Eras", "Events",
    "Nations", "Personalities", "Policies", "Quests", "Religions", "Ruins",
    "Specialists", "Speeds", "Techs", "Terrains", "TileImprovements",
    "TileResources", "UnitNameGroups", "UnitPromotions", "UnitTypes", "Units",
    "VictoryTypes",
)
REFERENCE_FIELDS = {
    "Units": {
        "uniqueTo": "Nations", "replaces": "Units", "upgradesTo": "Units",
        "requiredTech": "Techs", "obsoleteTech": "Techs", "requiredResource": "TileResources",
        "unitType": "UnitTypes", "promotions": "UnitPromotions",
    },
    "Buildings": {
        "uniqueTo": "Nations", "replaces": "Buildings", "requiredTech": "Techs",
        "requiredBuilding": "Buildings", "requiredResource": "TileResources",
        "requiredNearbyImprovedResources": "TileResources",
    },
    "TileImprovements": {
        "terrainsCanBeBuiltOn": "Terrains", "techRequired": "Techs",
        "replaces": "TileImprovements", "uniqueTo": "Nations",
    },
    "TileResources": {
        "terrainsCanBeFoundOn": "Terrains", "improvement": "TileImprovements",
        "improvedBy": "TileImprovements", "revealedBy": "Techs",
    },
    "UnitPromotions": {"prerequisites": "UnitPromotions", "unitTypes": "UnitTypes"},
    "Policies": {"era": "Eras"},
    "Nations": {
        "cityStateType": "CityStateTypes", "favoredReligion": "Religions",
        "personality": "Personalities",
    },
    "Ruins": {"excludedDifficulties": "Difficulties"},
    "Eras": {
        "startingSettlerUnit": "Units", "startingWorkerUnit": "Units",
        "startingMilitaryUnit": "Units", "settlerBuildings": "Buildings",
        "startingObsoleteWonders": "Buildings",
    },
    "Difficulties": {"aiFreeTechs": "Techs"},
    "VictoryTypes": {"requiredSpaceshipParts": "Units"},
    "Quests": {},
}
OWNER_TYPES = {
    "Nations": "Nation", "Units": "Unit", "Buildings": "Building", "Techs": "Technology",
    "Policies": "Policy", "TileImprovements": "Improvement", "TileResources": "Resource",
    "UnitPromotions": "UnitPromotion", "UnitTypes": "UnitType",
    "GlobalUniques": "Global", "ModOptions": "ModOptions",
}
GLOBAL_UNIQUE_OWNERS = {
    "Global", "Nation", "Era", "Technology", "Policy", "Building",
    "FounderBelief", "Resource",
}
UNIT_UNIQUE_OWNERS = {"Unit", "UnitPromotion", "UnitType"}
DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "references" / "mechanics_registry.json"
DEFAULT_SCHEMA_DIR = Path(__file__).resolve().parents[1] / "references" / "schemas" / "unciv-4.22.0"
DEFAULT_SCHEMA_EXCEPTIONS = Path(__file__).resolve().parents[1] / "references" / "schema_exceptions.json"
PLACEHOLDER_RE = re.compile(r"\[[^\[\]]+\]")
TEMPLATE_PARAMETER_RE = re.compile(r"\{([A-Za-z][A-Za-z0-9_]*)\}")
PARAMETER_PATTERNS = {
    "number": r"\d+(?:\.\d+)?",
    "signed-number": r"[+-]?\d+(?:\.\d+)?",
    "text": r"[^\[\]\r\n]+",
    "stats": r"[+-]?\d+(?:\.\d+)? [A-Za-z][^,\[\]\r\n]*(?:, [+-]?\d+(?:\.\d+)? [A-Za-z][^,\[\]\r\n]*)*",
}


@dataclass
class Finding:
    severity: str
    path: Path
    message: str
    code: str = ""
    json_pointer: str | None = None
    suggestion: str | None = None
    value: Any = None

    def __post_init__(self) -> None:
        if not self.code:
            self.code = _diagnostic_code(self.message)


def _diagnostic_code(message: str) -> str:
    """Map human messages to stable categories without changing legacy callers."""
    if message.startswith("Official Unciv") and " Schema at " in message:
        return "SCHEMA_VALIDATION_ERROR"
    if message.startswith("Passed official Unciv"):
        return "SCHEMA_VALIDATION_PASS"
    if "duplicate object key" in message:
        return "JSON_DUPLICATE_KEY"
    if message.startswith("Cannot parse JSON"):
        return "JSON_PARSE_ERROR"
    if "references" in message and ("not found" in message or "supply base data" in message):
        return "REFERENCE_NOT_FOUND"
    if "registry applicability" in message:
        return "UNIQUE_APPLICABILITY_ERROR"
    if "uses an unregistered unique" in message:
        return "UNIQUE_UNREGISTERED"
    if "matches parameterized mechanic" in message:
        return "UNIQUE_PARAMETERIZED_MATCH"
    if "matches mechanic" in message:
        return "UNIQUE_EXACT_MATCH"
    if "square-bracket placeholders" in message:
        return "TRANSLATION_PLACEHOLDER_MISMATCH"
    if "duplicates translation key" in message:
        return "TRANSLATION_DUPLICATE_KEY"
    if "also exists in supplied base data" in message:
        return "BASE_OBJECT_OVERRIDE"
    if "No rules JSON files" in message:
        return "RULES_NOT_PRESENT"
    return "RULE_VALIDATION"


def _parts_to_json_pointer(parts: Iterable[Any]) -> str:
    encoded = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(encoded) if encoded else ""


def _reference_json_pointer(location: str) -> str | None:
    match = re.match(r"^[^.\[]+(.*)$", location)
    if not match:
        return None
    suffix = match.group(1)
    parts = re.findall(r"\.([^\.\[]+)|\[(\d+)\]", suffix)
    flattened = [field or index for field, index in parts]
    return _parts_to_json_pointer(flattened)


class DuplicateKeyError(ValueError):
    pass


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_without_duplicate_keys)


def _load_schema_bundle(schema_dir: Path, findings: list[Finding]):
    try:
        from jsonschema.validators import validator_for
        from referencing import Registry, Resource
    except ImportError as error:
        findings.append(Finding("ERROR", schema_dir, f"Official Schema validation requires the dependencies in requirements.txt: {error}"))
        return {}, None, None
    manifest_path = schema_dir / "manifest.json"
    try:
        manifest = _read_json(manifest_path)
        expected_files = manifest["files"]
        version = manifest["game_version"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, KeyError, TypeError) as error:
        findings.append(Finding("ERROR", manifest_path, f"Cannot read official Schema manifest: {error}"))
        return {}, None, None
    registry = Registry()
    schemas: dict[str, Any] = {}
    try:
        for relative_path in sorted(expected_files):
            if not relative_path.endswith(".schema.json"):
                continue
            schema_path = schema_dir / relative_path
            schema = _read_json(schema_path)
            validator_for(schema).check_schema(schema)
            resource = Resource.from_contents(schema)
            schema_id = schema["$id"]
            registry = registry.with_resource(schema_id, resource)
            registry = registry.with_resource(schema_id.replace("/refs/heads/master/", f"/{version}/"), resource)
            if "/" not in relative_path:
                schemas[relative_path.removesuffix(".schema.json")] = schema
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, KeyError, TypeError, ValueError) as error:
        findings.append(Finding("ERROR", schema_dir, f"Cannot load official Schema bundle: {error}"))
        return {}, None, None
    return schemas, registry, version


def _schema_location(parts: Iterable[Any]) -> str:
    location = "$"
    for part in parts:
        location += f"[{part}]" if isinstance(part, int) else f".{part}"
    return location


def _check_official_schema(
    path: Path,
    kind: str,
    data: Any,
    schemas: dict[str, Any],
    schema_registry: Any,
    schema_version: str | None,
    schema_exceptions: list[dict[str, Any]],
    base_ruleset: str | None,
    findings: list[Finding],
) -> None:
    schema = schemas.get(kind)
    if schema is None:
        findings.append(Finding("INFO", path, f"No bundled official Schema for {path.name}; structural checks are limited"))
        return
    from jsonschema.validators import validator_for

    validator = validator_for(schema)(schema, registry=schema_registry)
    errors = sorted(validator.iter_errors(data), key=lambda error: [str(part) for part in error.absolute_path])
    errors = [
        error for error in errors
        if not _is_schema_exception(kind, schema_version, error, schema_exceptions, base_ruleset)
    ]
    for error in errors:
        findings.append(Finding(
            "ERROR", path,
            f"Official Unciv {schema_version} Schema at {_schema_location(error.absolute_path)}: {error.message}",
            code="SCHEMA_VALIDATION_ERROR",
            json_pointer=_parts_to_json_pointer(error.absolute_path),
            suggestion="Match the bundled official Schema for this file and field.",
        ))
    if not errors:
        findings.append(Finding("INFO", path, f"Passed official Unciv {schema_version} {kind}.schema.json"))


def _load_schema_exceptions(path: Path | None, findings: list[Finding]) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        data = _read_json(path)
        exceptions = data["exceptions"]
        if not isinstance(exceptions, list):
            raise TypeError("exceptions must be an array")
        return exceptions
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, KeyError, TypeError) as error:
        findings.append(Finding("ERROR", path, f"Cannot read Schema exceptions: {error}"))
        return []


def _is_schema_exception(
    kind: str,
    version: str | None,
    error: Any,
    exceptions: list[dict[str, Any]],
    base_ruleset: str | None = None,
) -> bool:
    unexpected = None
    if error.validator == "additionalProperties":
        match = re.search(r"\('([^']+)' was unexpected\)", error.message)
        unexpected = match.group(1) if match else None
    return any(
        entry.get("game_version") == version
        and (entry.get("ruleset") is None or entry.get("ruleset") == base_ruleset)
        and entry.get("file") == f"{kind}.json"
        and entry.get("validator") == error.validator
        and entry.get("unexpected_property") == unexpected
        for entry in exceptions
    )


def _walk_named_objects(value: Any):
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and name.strip():
            yield name
        for child in value.values():
            yield from _walk_named_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_named_objects(child)


def _load_base_names(base_path: Path, findings: list[Finding]) -> dict[str, set[str]]:
    names: dict[str, set[str]] = {}
    if base_path.is_dir():
        for kind in BASE_TYPES:
            candidates = (base_path / f"{kind}.json", base_path / "jsons" / f"{kind}.json")
            file_path = next((candidate for candidate in candidates if candidate.is_file()), None)
            if file_path is None:
                continue
            try:
                names[kind] = set(_walk_named_objects(_read_json(file_path)))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as error:
                findings.append(Finding("ERROR", file_path, f"Cannot read base rules data: {error}"))
    elif base_path.is_file():
        try:
            data = _read_json(base_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as error:
            findings.append(Finding("ERROR", base_path, f"Cannot read base rules data: {error}"))
            return names
        if not isinstance(data, dict):
            findings.append(Finding("ERROR", base_path, "Consolidated base rules data must be an object keyed by JSON type"))
            return names
        for kind in BASE_TYPES:
            if kind in data:
                names[kind] = set(_walk_named_objects(data[kind]))
    else:
        findings.append(Finding("ERROR", base_path, "Base rules data path does not exist"))
    return names


def _check_string_list(value: Any, path: Path, field: str, findings: list[Finding], unique: bool = False) -> None:
    if not isinstance(value, list):
        findings.append(Finding("ERROR", path, f"{field} must be an array of strings"))
        return
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            findings.append(Finding("ERROR", path, f"{field}[{index}] must be a non-empty string"))
        elif unique and item in seen:
            findings.append(Finding("ERROR", path, f"{field} contains duplicate value {item!r}"))
        elif isinstance(item, str):
            seen.add(item)


def _check_string_field(item: dict[str, Any], key: str, path: Path, findings: list[Finding], required: bool = False) -> None:
    if key not in item:
        if required:
            findings.append(Finding("ERROR", path, f"Missing required field {key!r}"))
        return
    if not isinstance(item[key], str) or not item[key].strip():
        findings.append(Finding("ERROR", path, f"{key!r} must be a non-empty string"))


def _check_integer_field(
    item: dict[str, Any], key: str, path: Path, findings: list[Finding], required: bool = False, minimum: int | None = None,
) -> None:
    if key not in item:
        if required:
            findings.append(Finding("ERROR", path, f"Missing required field {key!r}"))
        return
    value = item[key]
    if not isinstance(value, int) or isinstance(value, bool) or (minimum is not None and value < minimum):
        suffix = f" greater than or equal to {minimum}" if minimum is not None else ""
        findings.append(Finding("ERROR", path, f"{key!r} must be an integer{suffix}"))


def _check_color(item: dict[str, Any], key: str, path: Path, findings: list[Finding], required: bool = False) -> None:
    if key not in item:
        if required:
            findings.append(Finding("ERROR", path, f"Missing required field {key!r}"))
        return
    color = item[key]
    if (
        not isinstance(color, list) or len(color) != 3
        or any(not isinstance(channel, int) or isinstance(channel, bool) or not 0 <= channel <= 255 for channel in color)
    ):
        findings.append(Finding("ERROR", path, f"{key!r} must be an RGB array of three integers from 0 to 255"))


def _validate_named_array(kind: str, path: Path, data: Any, findings: list[Finding]) -> None:
    if not isinstance(data, list):
        findings.append(Finding("ERROR", path, f"{kind}.json must contain a JSON array"))
        return
    seen_names: set[str] = set()
    for index, item in enumerate(data):
        location = path.parent / f"{path.name}#{index}"
        if not isinstance(item, dict):
            findings.append(Finding("ERROR", location, "Each definition must be a JSON object"))
            continue
        _check_string_field(item, "name", location, findings, required=True)
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            if name in seen_names:
                findings.append(Finding("ERROR", location, f"Duplicate {kind} name {name!r}"))
            seen_names.add(name)
        if "uniques" in item:
            _check_string_list(item["uniques"], location, "uniques", findings)

        if kind == "Nations":
            _check_color(item, "outerColor", location, findings, required=True)
            _check_color(item, "innerColor", location, findings)
            if "cities" in item:
                _check_string_list(item["cities"], location, "cities", findings, unique=True)
        elif kind == "Units":
            _check_string_field(item, "unitType", location, findings, required=True)
            for field in ("uniqueTo", "replaces", "upgradesTo", "requiredTech", "obsoleteTech", "requiredResource"):
                _check_string_field(item, field, location, findings)
            if "promotions" in item:
                _check_string_list(item["promotions"], location, "promotions", findings, unique=True)
        elif kind == "Buildings":
            for field in ("uniqueTo", "replaces", "requiredTech", "requiredBuilding", "requiredResource"):
                _check_string_field(item, field, location, findings)
        elif kind == "TileImprovements":
            for field in ("techRequired", "replaces", "uniqueTo"):
                _check_string_field(item, field, location, findings)
            if "terrainsCanBeBuiltOn" in item:
                _check_string_list(item["terrainsCanBeBuiltOn"], location, "terrainsCanBeBuiltOn", findings, unique=True)
        elif kind == "TileResources":
            if item.get("resourceType") not in (None, "Strategic", "Luxury", "Bonus"):
                findings.append(Finding("ERROR", location, "resourceType must be Strategic, Luxury, or Bonus"))
            for field in ("improvement", "revealedBy"):
                _check_string_field(item, field, location, findings)
            for field in ("terrainsCanBeFoundOn", "improvedBy"):
                if field in item:
                    _check_string_list(item[field], location, field, findings, unique=True)
        elif kind == "UnitPromotions":
            for field in ("prerequisites", "unitTypes"):
                if field in item:
                    _check_string_list(item[field], location, field, findings, unique=True)
            _check_color(item, "outerColor", location, findings)
            _check_color(item, "innerColor", location, findings)
        elif kind == "UnitTypes":
            _check_string_field(item, "movementType", location, findings, required=True)
            if item.get("movementType") not in (None, "Land", "Water", "Air"):
                findings.append(Finding("ERROR", location, "movementType must be Land, Water, or Air"))
        elif kind == "Policies":
            _check_string_field(item, "era", location, findings, required=True)
            policies = item.get("policies", [])
            if not isinstance(policies, list):
                findings.append(Finding("ERROR", location, "policies must be an array"))
            else:
                _validate_policy_members(policies, location, findings)


def _validate_policy_members(policies: list[Any], path: Path, findings: list[Finding]) -> None:
    seen: set[str] = set()
    for index, policy in enumerate(policies):
        location = path.parent / f"{path.name}.policies#{index}"
        if not isinstance(policy, dict):
            findings.append(Finding("ERROR", location, "Each policy must be a JSON object"))
            continue
        _check_string_field(policy, "name", location, findings, required=True)
        name = policy.get("name")
        if isinstance(name, str) and name in seen:
            findings.append(Finding("ERROR", location, f"Duplicate policy name {name!r}"))
        elif isinstance(name, str):
            seen.add(name)
        if "requires" in policy:
            _check_string_list(policy["requires"], location, "requires", findings, unique=True)
        if "uniques" in policy:
            _check_string_list(policy["uniques"], location, "uniques", findings)


def _validate_techs(path: Path, data: Any, findings: list[Finding]) -> None:
    if not isinstance(data, list):
        findings.append(Finding("ERROR", path, "Techs.json must contain a JSON array"))
        return
    seen_techs: set[str] = set()
    for column_index, column in enumerate(data):
        location = path.parent / f"{path.name}#{column_index}"
        if not isinstance(column, dict):
            findings.append(Finding("ERROR", location, "Each technology column must be a JSON object"))
            continue
        _check_integer_field(column, "columnNumber", location, findings, required=True, minimum=0)
        _check_string_field(column, "era", location, findings, required=True)
        techs = column.get("techs", [])
        if not isinstance(techs, list):
            findings.append(Finding("ERROR", location, "techs must be an array"))
            continue
        seen_rows: set[int] = set()
        for tech_index, tech in enumerate(techs):
            tech_location = path.parent / f"{path.name}#{column_index}.techs#{tech_index}"
            if not isinstance(tech, dict):
                findings.append(Finding("ERROR", tech_location, "Each technology must be a JSON object"))
                continue
            _check_string_field(tech, "name", tech_location, findings, required=True)
            _check_integer_field(tech, "row", tech_location, findings, required=True, minimum=1)
            name = tech.get("name")
            if isinstance(name, str) and name in seen_techs:
                findings.append(Finding("ERROR", tech_location, f"Duplicate technology name {name!r}"))
            elif isinstance(name, str):
                seen_techs.add(name)
            row = tech.get("row")
            if isinstance(row, int) and not isinstance(row, bool):
                if row in seen_rows:
                    findings.append(Finding("ERROR", tech_location, f"Duplicate technology row {row} in one column"))
                seen_rows.add(row)
            if "prerequisites" in tech:
                _check_string_list(tech["prerequisites"], tech_location, "prerequisites", findings, unique=True)
            if "uniques" in tech:
                _check_string_list(tech["uniques"], tech_location, "uniques", findings)


def _validate_object_file(kind: str, path: Path, data: Any, findings: list[Finding]) -> None:
    if not isinstance(data, dict):
        findings.append(Finding("ERROR", path, f"{kind}.json must contain a JSON object"))
        return
    if kind == "GlobalUniques":
        _check_string_field(data, "name", path, findings, required=True)
        for field in ("uniques", "unitUniques"):
            if field in data:
                _check_string_list(data[field], path, field, findings)
    else:
        if "isBaseRuleset" in data and not isinstance(data["isBaseRuleset"], bool):
            findings.append(Finding("ERROR", path, "isBaseRuleset must be a boolean"))
        for field in (
            "uniques", "techsToRemove", "buildingsToRemove", "unitsToRemove", "nationsToRemove",
            "policyBranchesToRemove", "policiesToRemove", "beliefsToRemove", "religionsToRemove",
        ):
            if field in data:
                _check_string_list(data[field], path, field, findings)
        if "constants" in data and not isinstance(data["constants"], dict):
            findings.append(Finding("ERROR", path, "constants must be a JSON object"))


def _check_translations(mod_dir: Path, findings: list[Finding]) -> None:
    translations_dir = mod_dir / "jsons" / "translations"
    if not translations_dir.is_dir():
        return
    for path in sorted(translations_dir.iterdir()):
        if path.is_dir() or path.name.startswith("."):
            continue
        if path.suffix != ".properties":
            findings.append(Finding("WARNING", path, "Translation files should use the .properties extension"))
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as error:
            findings.append(Finding("ERROR", path, f"Cannot read translation as UTF-8: {error}"))
            continue
        seen_keys: set[str] = set()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if " = " not in line:
                findings.append(Finding("ERROR", path, f"Line {line_number} must separate source and translation with ' = '"))
                continue
            key, value = line.split(" = ", 1)
            if key in seen_keys:
                findings.append(Finding("ERROR", path, f"Line {line_number} duplicates translation key {key!r}"))
            seen_keys.add(key)
            if value and sorted(PLACEHOLDER_RE.findall(key)) != sorted(PLACEHOLDER_RE.findall(value)):
                findings.append(Finding("ERROR", path, f"Line {line_number} must preserve all square-bracket placeholders"))


def _iter_references(kind: str, data: Any) -> Iterable[tuple[str, str, str]]:
    if isinstance(data, list) and kind in REFERENCE_FIELDS:
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue
            for field, target_kind in REFERENCE_FIELDS[kind].items():
                values = item.get(field)
                if values is None:
                    continue
                for value in values if isinstance(values, list) else [values]:
                    if isinstance(value, str):
                        yield f"{kind}[{index}].{field}", target_kind, value
            if kind == "Policies" and isinstance(item.get("policies"), list):
                for policy_index, policy in enumerate(item["policies"]):
                    if isinstance(policy, dict):
                        for value in policy.get("requires", []):
                            if isinstance(value, str):
                                yield f"Policies[{index}].policies[{policy_index}].requires", "Policies", value
            if kind == "Buildings" and isinstance(item.get("specialistSlots"), dict):
                for value in item["specialistSlots"]:
                    yield f"Buildings[{index}].specialistSlots", "Specialists", value
            if kind == "Quests" and isinstance(item.get("weightForCityStateType"), dict):
                for value in item["weightForCityStateType"]:
                    yield f"Quests[{index}].weightForCityStateType", "CityStateTypes", value
            if kind == "Difficulties":
                for field in ("playerBonusStartingUnits", "aiMajorCivBonusStartingUnits", "aiCityStateBonusStartingUnits"):
                    for value in item.get(field, []):
                        if isinstance(value, str) and value != "Era Starting Unit":
                            yield f"Difficulties[{index}].{field}", "Units", value
    if kind == "Techs" and isinstance(data, list):
        for column_index, column in enumerate(data):
            if not isinstance(column, dict):
                continue
            era = column.get("era")
            if isinstance(era, str):
                yield f"Techs[{column_index}].era", "Eras", era
            for tech_index, tech in enumerate(column.get("techs", [])):
                if isinstance(tech, dict):
                    for value in tech.get("prerequisites", []):
                        if isinstance(value, str):
                            yield f"Techs[{column_index}].techs[{tech_index}].prerequisites", "Techs", value


def detect_base_ruleset(
    mod_dir: Path,
    index_path: Path = reference_catalog.DEFAULT_INDEX,
) -> dict[str, Any]:
    """Conservatively infer a bundled base ruleset from semantic references.

    A result is only detected when exactly one bundled ruleset can satisfy every
    external reference. Shared references deliberately remain ambiguous.
    """
    mod_dir = mod_dir.resolve()
    json_dir = mod_dir / "jsons"
    candidates = reference_catalog.available_rulesets(index_path)
    parsed: dict[str, Any] = {}
    local_names: dict[str, set[str]] = {}
    parse_errors: list[str] = []
    for path in sorted(json_dir.glob("*.json")) if json_dir.is_dir() else []:
        kind = next((name for name in KNOWN_RULE_FILES if name.casefold() == path.stem.casefold()), path.stem)
        try:
            data = _read_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as error:
            parse_errors.append(f"{path.name}: {error}")
            continue
        parsed[kind] = data
        local_names.setdefault(kind, set()).update(_walk_named_objects(data))

    references = sorted({
        (target_kind, value)
        for kind, data in parsed.items()
        for _, target_kind, value in _iter_references(kind, data)
        if value not in local_names.get(target_kind, set())
    })
    baselines: dict[str, dict[str, set[str]]] = {}
    for ruleset in candidates:
        bundle = reference_catalog.resolve_bundle(ruleset, index_path)
        findings: list[Finding] = []
        baselines[ruleset] = _load_base_names(bundle["base_rules_data"], findings)
        parse_errors.extend(f"{finding.path}: {finding.message}" for finding in findings if finding.severity == "ERROR")

    missing_by_ruleset = {
        ruleset: [
            {"kind": kind, "value": value}
            for kind, value in references
            if value not in names.get(kind, set())
        ]
        for ruleset, names in baselines.items()
    }
    compatible = [ruleset for ruleset in candidates if not missing_by_ruleset[ruleset]]
    distinctive = [
        {"kind": kind, "value": value, "rulesets": supported}
        for kind, value in references
        if len(supported := [
            ruleset for ruleset, names in baselines.items() if value in names.get(kind, set())
        ]) < len(candidates)
    ]
    if parse_errors:
        status, ruleset = "invalid", None
    elif len(compatible) == 1:
        status, ruleset = "detected", compatible[0]
    elif compatible:
        status, ruleset = "ambiguous", None
    else:
        status, ruleset = "unresolved", None
    return {
        "status": status,
        "ruleset": ruleset,
        "candidates": compatible,
        "available_rulesets": list(candidates),
        "external_reference_count": len(references),
        "distinctive_references": distinctive,
        "missing_by_ruleset": missing_by_ruleset,
        "errors": parse_errors,
    }


def require_base_ruleset(mod_dir: Path) -> tuple[str, dict[str, Any]]:
    detection = detect_base_ruleset(mod_dir)
    if detection["status"] == "detected":
        return detection["ruleset"], detection
    choices = ", ".join(detection["available_rulesets"])
    if detection["status"] == "invalid":
        details = "; ".join(detection["errors"][:3])
        raise ValueError(f"Cannot detect the base ruleset because Mod JSON is invalid: {details}")
    if detection["status"] == "unresolved":
        raise ValueError(
            "No bundled base ruleset satisfies all external references; "
            f"choose --base-ruleset after correcting the references. Available: {choices}"
        )
    raise ValueError(
        "The base ruleset cannot be detected uniquely from this Mod's references; "
        f"choose --base-ruleset. Candidates: {', '.join(detection['candidates']) or choices}"
    )


def _iter_uniques(kind: str, value: Any, location: str = "") -> Iterable[tuple[str, str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}" if location else key
            if key in ("uniques", "unitUniques") and isinstance(child, list):
                if key == "unitUniques":
                    owner = "Unit"
                elif kind == "Beliefs" and isinstance(value.get("type"), str):
                    owner = f"{value['type']}Belief"
                elif kind == "Nations" and value.get("cityStateType"):
                    owner = "CityState"
                else:
                    owner = OWNER_TYPES.get(kind, kind)
                for index, unique in enumerate(child):
                    if isinstance(unique, str):
                        yield owner, unique, f"{child_location}[{index}]"
            else:
                yield from _iter_uniques(kind, child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_uniques(kind, child, f"{location}[{index}]")


def _compile_unique_template(entry: dict[str, Any]) -> re.Pattern[str] | None:
    template = entry.get("template_unique")
    if not isinstance(template, str) or not template:
        return None
    parameter_kinds = entry.get("parameter_kinds", {})
    pieces: list[str] = []
    position = 0
    for match in TEMPLATE_PARAMETER_RE.finditer(template):
        pieces.append(re.escape(template[position:match.start()]))
        kind = parameter_kinds.get(match.group(1), "text")
        pattern = PARAMETER_PATTERNS.get(kind)
        if pattern is None:
            raise ValueError(f"unknown parameter kind {kind!r} in mechanic {entry.get('id')!r}")
        pieces.append(f"(?P<{match.group(1)}>{pattern})")
        position = match.end()
    pieces.append(re.escape(template[position:]))
    return re.compile("^" + "".join(pieces) + "$")


def _check_unique_parameter_references(
    entry: dict[str, Any], match: re.Match[str], path: Path, location: str,
    local_names: dict[str, set[str]], base_names: dict[str, set[str]], strict: bool,
    findings: list[Finding],
) -> None:
    for parameter, target_kind in entry.get("parameter_references", {}).items():
        value = match.groupdict().get(parameter)
        if value is None:
            continue
        known = local_names.get(target_kind, set()) | base_names.get(target_kind, set())
        if value not in known:
            severity = "ERROR" if strict and target_kind in base_names else "WARNING"
            findings.append(Finding(
                severity, path,
                f"{location} parameter {parameter!r} references {value!r}, not found in {target_kind}",
                code="UNIQUE_PARAMETER_REFERENCE_NOT_FOUND",
                json_pointer=_reference_json_pointer(location),
                suggestion=f"Use a {target_kind} name from the Mod or selected base ruleset.",
                value=value,
            ))


def _check_mechanics_registry(
    mod_dir: Path, parsed: dict[Path, Any], registry_path: Path | None,
    local_names: dict[str, set[str]], base_names: dict[str, set[str]], strict: bool,
    findings: list[Finding],
) -> None:
    unique_entries = [
        (path, owner, unique, location)
        for path, data in parsed.items()
        for owner, unique, location in _iter_uniques(path.stem, data)
    ]
    if not unique_entries:
        return
    if registry_path is None:
        findings.append(Finding("INFO", mod_dir, "Unique strings were not checked against a mechanics registry"))
        return
    try:
        registry = _read_json(registry_path)
        by_unique = {entry["exact_unique"]: entry for entry in registry["mechanics"]}
        templates = [(entry, _compile_unique_template(entry)) for entry in registry["mechanics"]]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, KeyError, TypeError, ValueError, re.error) as error:
        findings.append(Finding("ERROR", registry_path, f"Cannot read mechanics registry: {error}"))
        return
    for path, owner, unique, location in unique_entries:
        entry = by_unique.get(unique)
        exact_match = entry is not None
        parameter_match = None
        if entry is None:
            for candidate, pattern in templates:
                if pattern and (match := pattern.fullmatch(unique)):
                    entry, parameter_match = candidate, match
                    break
        if entry is None:
            findings.append(Finding("INFO", path, f"{location} uses an unregistered unique; verify it in official documentation and the in-game Ruleset Validator: {unique!r}"))
            continue
        applicable = entry.get("applicable_to", [])
        applicable_match = (
            owner in applicable
            or "Any" in applicable
            or ("Global" in applicable and owner in GLOBAL_UNIQUE_OWNERS)
            or ("Unit" in applicable and owner in UNIT_UNIQUE_OWNERS)
        )
        if not applicable_match:
            findings.append(Finding(
                "ERROR", path,
                f"{location} uses mechanic {entry.get('id')!r} on {owner}; registry applicability is {applicable}",
                code="UNIQUE_APPLICABILITY_ERROR",
                json_pointer=_reference_json_pointer(location),
                suggestion=f"Move the Unique to an applicable owner: {', '.join(applicable)}.",
                value=unique,
            ))
        elif exact_match:
            findings.append(Finding("INFO", path, f"{location} matches mechanic {entry.get('id')!r} ({entry.get('evidence_status', 'unknown')})"))
        else:
            findings.append(Finding(
                "INFO", path,
                f"{location} matches parameterized mechanic {entry.get('id')!r}; exact parameter values have no recorded test evidence",
            ))
        if parameter_match is not None:
            _check_unique_parameter_references(
                entry, parameter_match, path, location, local_names, base_names, strict, findings,
            )


def inspect_mod_rules(
    mod_dir: Path,
    base_rules_data: Path | None = None,
    strict_base_references: bool = False,
    mechanics_registry: Path | None = DEFAULT_REGISTRY,
    schema_dir: Path | None = DEFAULT_SCHEMA_DIR,
    schema_exceptions_path: Path | None = DEFAULT_SCHEMA_EXCEPTIONS,
    base_ruleset: str | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    if not mod_dir.is_dir():
        return [Finding("ERROR", mod_dir, "Mod folder does not exist or is not a directory")]

    json_dir = mod_dir / "jsons"
    rule_files = sorted(path for path in json_dir.glob("*.json")) if json_dir.is_dir() else []
    if not rule_files:
        findings.append(Finding("INFO", mod_dir, "No rules JSON files found directly under jsons/"))
        _check_translations(mod_dir, findings)
        return findings

    parsed: dict[Path, Any] = {}
    local_names: dict[str, set[str]] = {}
    schemas: dict[str, Any] = {}
    schema_registry = None
    schema_version = None
    schema_exceptions = _load_schema_exceptions(schema_exceptions_path, findings) if schema_dir is not None else []
    if schema_dir is not None:
        schemas, schema_registry, schema_version = _load_schema_bundle(schema_dir, findings)
    for path in rule_files:
        kind = path.stem
        canonical = next((name for name in KNOWN_RULE_FILES if name.casefold() == kind.casefold()), None)
        if canonical and path.name != f"{canonical}.json":
            findings.append(Finding("ERROR", path, f"Use the exact filename {canonical}.json"))
            kind = canonical
        try:
            data = _read_json(path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as error:
            findings.append(Finding("ERROR", path, f"Cannot parse JSON: {error}"))
            continue
        parsed[path] = data
        local_names.setdefault(kind, set()).update(_walk_named_objects(data))
        if schema_dir is not None and schema_registry is not None:
            _check_official_schema(
                path, kind, data, schemas, schema_registry, schema_version,
                schema_exceptions, base_ruleset, findings,
            )
        if kind == "Techs":
            _validate_techs(path, data, findings)
        elif kind in ARRAY_RULE_FILES:
            _validate_named_array(kind, path, data, findings)
        elif kind in OBJECT_RULE_FILES:
            _validate_object_file(kind, path, data, findings)

    base_names = _load_base_names(base_rules_data, findings) if base_rules_data else {}
    for kind, names in local_names.items():
        if kind in base_names:
            for name in sorted(names & base_names[kind]):
                findings.append(Finding("WARNING", json_dir / f"{kind}.json", f"{name!r} also exists in supplied base data; confirm an override is intentional"))

    for path, data in parsed.items():
        kind = next((name for name in KNOWN_RULE_FILES if name.casefold() == path.stem.casefold()), path.stem)
        for location, target_kind, value in _iter_references(kind, data):
            local_target_names = local_names.get(target_kind, set())
            if target_kind in base_names:
                if value not in local_target_names | base_names[target_kind]:
                    severity = "ERROR" if strict_base_references else "WARNING"
                    findings.append(Finding(
                        severity, path,
                        f"{location} references {value!r}, not found in local or supplied {target_kind} data",
                        code="REFERENCE_NOT_FOUND",
                        json_pointer=_reference_json_pointer(location),
                        suggestion=f"Use a {target_kind} name from the Mod or selected base ruleset.",
                        value=value,
                    ))
            elif value not in local_target_names:
                findings.append(Finding(
                    "WARNING", path,
                    f"{location} references {value!r}; supply base data including {target_kind} to verify it",
                    code="REFERENCE_BASELINE_REQUIRED",
                    json_pointer=_reference_json_pointer(location),
                    suggestion="Select a bundled base ruleset or provide matching base rules data.",
                    value=value,
                ))

    _check_translations(mod_dir, findings)
    _check_mechanics_registry(mod_dir, parsed, mechanics_registry, local_names, base_names, strict_base_references, findings)
    return findings


def _format_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mod_dir", type=Path, help="Mod folder containing jsons/")
    parser.add_argument("--base-rules-data", type=Path, help="matching consolidated rules JSON or ruleset directory")
    parser.add_argument("--strict-base-references", action="store_true", help="make unresolved references errors when the target category is supplied")
    parser.add_argument("--mechanics-registry", type=Path, default=DEFAULT_REGISTRY, help="versioned exact and parameterized Unique registry")
    parser.add_argument("--no-mechanics-registry", action="store_true", help="skip bundled mechanics-registry matching")
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR, help="versioned official Unciv Schema bundle")
    parser.add_argument("--no-schema-validation", action="store_true", help="skip bundled official Schema validation")
    parser.add_argument("--schema-exceptions", type=Path, default=DEFAULT_SCHEMA_EXCEPTIONS, help="reviewed official Schema exceptions")
    parser.add_argument("--base-ruleset", help="select a bundled base ruleset")
    args = parser.parse_args()

    mod_dir = args.mod_dir.resolve()
    try:
        detected_ruleset = None
        if args.base_ruleset is None and args.base_rules_data is None:
            detected_ruleset, _ = require_base_ruleset(mod_dir)
        selected = reference_catalog.resolve_bundle(args.base_ruleset or detected_ruleset)
    except ValueError as error:
        parser.error(str(error))
    registry = None if args.no_mechanics_registry else (args.mechanics_registry if args.mechanics_registry != DEFAULT_REGISTRY else selected["mechanics_registry"])
    schema_dir = None if args.no_schema_validation else (args.schema_dir if args.schema_dir != DEFAULT_SCHEMA_DIR else selected["schema_dir"])
    ruleset_selected = args.base_ruleset is not None or detected_ruleset is not None
    base_data = args.base_rules_data or (selected["base_rules_data"] if ruleset_selected else None)
    schema_exceptions = args.schema_exceptions if args.schema_exceptions != DEFAULT_SCHEMA_EXCEPTIONS else selected["schema_exceptions"]
    selected_ruleset = selected["base_ruleset"] if ruleset_selected else None
    findings = inspect_mod_rules(
        mod_dir, base_data, args.strict_base_references, registry, schema_dir,
        schema_exceptions, selected_ruleset,
    )
    for finding in findings:
        print(f"{finding.severity}: {_format_path(finding.path, mod_dir)}: {finding.message}")
    counts = {severity: sum(f.severity == severity for f in findings) for severity in ("ERROR", "WARNING", "INFO")}
    print(f"Summary: {counts['ERROR']} error(s), {counts['WARNING']} warning(s), {counts['INFO']} info")
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
