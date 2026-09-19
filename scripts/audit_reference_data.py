#!/usr/bin/env python3
"""Audit bundled Unciv Schemas, baselines, checksums, and reviewed exceptions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import reference_catalog
import validate_mod_rules as rules


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_manifest(directory: Path, errors: list[str]) -> dict:
    manifest_path = directory / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for relative, expected in manifest["files"].items():
            path = directory / relative
            if not path.is_file():
                errors.append(f"Missing manifest file: {path}")
            elif _sha256(path) != expected:
                errors.append(f"Checksum mismatch: {path}")
        return manifest
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        errors.append(f"Cannot audit manifest {manifest_path}: {error}")
        return {}


def audit(index_path: Path = reference_catalog.DEFAULT_INDEX) -> dict:
    catalog = reference_catalog.load_catalog(index_path)
    errors: list[str] = []
    accepted: list[dict[str, object]] = []
    declared_exception_keys: set[tuple[str, str]] = set()
    used_exception_keys: set[tuple[str, str]] = set()

    for version, version_entry in sorted(catalog["versions"].items()):
        exceptions_path = reference_catalog.PROJECT_ROOT / version_entry["schema_exceptions"]
        exception_data = json.loads(exceptions_path.read_text(encoding="utf-8"))
        exceptions = exception_data["exceptions"]
        exception_file = exceptions_path.resolve().as_posix()
        declared_exception_keys.update((exception_file, entry["id"]) for entry in exceptions)
        schema_dir = reference_catalog.PROJECT_ROOT / version_entry["schema_dir"]
        schema_manifest = _check_manifest(schema_dir, errors)
        findings: list[rules.Finding] = []
        schemas, schema_registry, schema_version = rules._load_schema_bundle(schema_dir, findings)
        errors.extend(f"{finding.path}: {finding.message}" for finding in findings if finding.severity == "ERROR")
        if schema_manifest.get("game_version") != version or schema_version != version:
            errors.append(f"Schema bundle version mismatch for {version}")

        for ruleset, ruleset_entry in sorted(version_entry["rulesets"].items()):
            baseline_path = reference_catalog.PROJECT_ROOT / ruleset_entry["rules"]
            baseline_dir = baseline_path.parent
            manifest = _check_manifest(baseline_dir, errors)
            if manifest.get("game_version") != version or manifest.get("ruleset") != ruleset:
                errors.append(f"Baseline metadata mismatch: {baseline_dir}")
            try:
                baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
                errors.append(f"Cannot read baseline {baseline_path}: {error}")
                continue
            from jsonschema.validators import validator_for
            for kind, data in sorted(baseline.items()):
                schema = schemas.get(kind)
                if schema is None:
                    errors.append(f"No official {version} Schema for baseline file {kind}.json")
                    continue
                validator = validator_for(schema)(schema, registry=schema_registry)
                for error in validator.iter_errors(data):
                    matching = [
                        entry for entry in exceptions
                        if entry.get("ruleset") == ruleset
                        and rules._is_schema_exception(kind, version, error, [entry], ruleset)
                    ]
                    if matching:
                        used_exception_keys.add((exception_file, matching[0]["id"]))
                        accepted.append({
                            "exception": matching[0]["id"],
                            "ruleset": ruleset,
                            "file": f"{kind}.json",
                            "path": rules._schema_location(error.absolute_path),
                        })
                    else:
                        errors.append(
                            f"{ruleset}/{kind}.json {rules._schema_location(error.absolute_path)}: {error.message}"
                        )

    for _, stale in sorted(declared_exception_keys - used_exception_keys):
        errors.append(f"Reviewed Schema exception was not exercised: {stale}")
    return {
        "schema_version": 1,
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "accepted_exceptions": accepted,
        "summary": {
            "versions": len(catalog["versions"]),
            "rulesets": sum(len(entry["rulesets"]) for entry in catalog["versions"].values()),
            "accepted_exception_instances": len(accepted),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=reference_catalog.DEFAULT_INDEX)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = audit(args.index)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['status']}: {result['summary']['versions']} reference revision(s), "
        f"{result['summary']['rulesets']} ruleset(s), {len(result['errors'])} error(s)"
    )
    for error in result["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
