#!/usr/bin/env python3
"""Run the bundled Unciv Mod checks and write one evidence-bound preflight report."""

from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import package_and_upload_mod as packaging
import reference_catalog
import validate_mod_assets as assets
import validate_mod_rules as rules


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _portable_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _serialize_finding(finding: Any, root: Path) -> dict[str, Any]:
    item: dict[str, Any] = {
        "severity": finding.severity,
        "code": getattr(finding, "code", "VALIDATION_FINDING"),
        "path": _relative(finding.path, root),
        "message": finding.message,
    }
    for field in ("json_pointer", "suggestion", "value"):
        value = getattr(finding, field, None)
        if value is not None:
            item[field] = value
    return item


def _validation_inputs(
    base_rules_data: Path | None,
    mechanics_registry: Path | None,
    schema_dir: Path | None,
    schema_exceptions_path: Path | None,
    selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "base_rules_data": None if base_rules_data is None else _portable_path(base_rules_data),
        "mechanics_registry": None,
        "schema_bundle": None,
        "schema_exceptions": None if schema_exceptions_path is None else _portable_path(schema_exceptions_path),
        "reference_bundle": None,
    }
    if mechanics_registry is not None:
        registry_path = mechanics_registry.resolve()
        metadata: dict[str, Any] = {"path": _portable_path(registry_path)}
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            metadata["game_version"] = registry.get("target_game", {}).get("version")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
        result["mechanics_registry"] = metadata
    if schema_dir is not None:
        schema_path = schema_dir.resolve()
        metadata = {"path": _portable_path(schema_path)}
        try:
            manifest = json.loads((schema_path / "manifest.json").read_text(encoding="utf-8"))
            metadata["game_version"] = manifest.get("game_version")
            metadata["source_commit"] = manifest.get("source_commit")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
        result["schema_bundle"] = metadata
    if selection:
        result["reference_bundle"] = {
            "reference_version": selection["reference_version"],
            "reference_build": selection["reference_build"],
            "base_ruleset": selection["base_ruleset"],
            "index": _portable_path(selection["index_path"]),
        }
    return result


def run_preflight(
    mod_dir: Path,
    base_rules_data: Path | None = None,
    strict_base_references: bool = False,
    source_only: bool = False,
    mechanics_registry: Path | None = rules.DEFAULT_REGISTRY,
    schema_dir: Path | None = rules.DEFAULT_SCHEMA_DIR,
    schema_exceptions_path: Path | None = rules.DEFAULT_SCHEMA_EXCEPTIONS,
    base_ruleset: str | None = None,
    ruleset_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    selection = None
    if base_ruleset is not None:
        selection = reference_catalog.resolve_bundle(base_ruleset)
        base_rules_data = base_rules_data or selection["base_rules_data"]
        if mechanics_registry == rules.DEFAULT_REGISTRY:
            mechanics_registry = selection["mechanics_registry"]
        if schema_dir == rules.DEFAULT_SCHEMA_DIR:
            schema_dir = selection["schema_dir"]
        if schema_exceptions_path == rules.DEFAULT_SCHEMA_EXCEPTIONS:
            schema_exceptions_path = selection["schema_exceptions"]
    mod_dir = mod_dir.resolve()
    rule_findings = rules.inspect_mod_rules(
        mod_dir, base_rules_data, strict_base_references, mechanics_registry, schema_dir,
        schema_exceptions_path, selection["base_ruleset"] if selection else None,
    )
    _, asset_findings = assets.inspect_mod_assets(mod_dir, require_packed=not source_only)
    packaging_result: dict[str, Any]
    try:
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = Path(temporary_directory) / f"{mod_dir.name}.zip"
            packaging.package_mod(mod_dir, archive_path)
            archive_sha256 = packaging.sha256_file(archive_path)
            with zipfile.ZipFile(archive_path) as archive:
                bad_member = archive.testzip()
                members = archive.namelist()
            if bad_member:
                raise ValueError(f"ZIP integrity failed at {bad_member}")
            expected_prefix = f"{mod_dir.name}/"
            if not members or any(not member.startswith(expected_prefix) for member in members):
                raise ValueError("ZIP members must all be inside the single Mod folder")
            packaging_result = {
                "status": "PASS",
                "code": "PACKAGE_INTEGRITY_PASS",
                "message": f"Created and integrity-checked a temporary ZIP with {len(members)} member(s)",
                "sha256": archive_sha256,
            }
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        packaging_result = {"status": "ERROR", "code": "PACKAGE_INTEGRITY_ERROR", "message": str(error)}

    checks = {
        "rules": [
            _serialize_finding(finding, mod_dir) for finding in rule_findings
        ],
        "assets": [
            _serialize_finding(finding, mod_dir) for finding in asset_findings
        ],
        "packaging": packaging_result,
    }
    error_count = sum(
        finding["severity"] == "ERROR"
        for section in (checks["rules"], checks["assets"])
        for finding in section
    ) + (packaging_result["status"] == "ERROR")
    warning_count = sum(
        finding["severity"] == "WARNING"
        for section in (checks["rules"], checks["assets"])
        for finding in section
    )
    return {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mod": mod_dir.as_posix(),
        "mode": "source-only" if source_only else "full",
        "ruleset_selection": ruleset_selection or {
            "source": "explicit" if base_ruleset else "not-selected",
            "ruleset": base_ruleset,
        },
        "validation_inputs": _validation_inputs(
            base_rules_data, mechanics_registry, schema_dir, schema_exceptions_path, selection,
        ),
        "status": "FAIL" if error_count else "PASS",
        "summary": {"errors": error_count, "warnings": warning_count},
        "checks": checks,
        "evidence_boundary": (
            "This report covers bundled official Schema, cross-file reference, registered-mechanic, translation, asset, atlas, and ZIP checks. "
            "It does not prove gameplay behavior, balance, or compatibility with an untested game build."
        ),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Preflight: {Path(report['mod']).name}", "",
        f"- Status: **{report['status']}**",
        f"- Mode: {report['mode']}",
        f"- Checked at: {report['checked_at']}",
        f"- Errors: {report['summary']['errors']}",
        f"- Warnings: {report['summary']['warnings']}", "",
    ]
    inputs = report["validation_inputs"]
    schema = inputs.get("schema_bundle")
    registry = inputs.get("mechanics_registry")
    lines.extend(("## Validation inputs", ""))
    selection = report.get("ruleset_selection", {})
    if selection.get("ruleset"):
        lines.append(f"- Base ruleset selection: {selection.get('source', 'unknown')} — `{selection['ruleset']}`")
    lines.append(f"- Official Schema provenance: Unciv {schema.get('game_version', 'unknown')}" if schema else "- Official Schema bundle: disabled")
    lines.append(f"- Mechanics registry provenance: Unciv {registry.get('game_version', 'unknown')}" if registry else "- Mechanics registry: disabled")
    lines.append(
        f"- Reviewed Schema exceptions: `{inputs['schema_exceptions']}`"
        if inputs.get("schema_exceptions") else "- Reviewed Schema exceptions: disabled"
    )
    lines.append(f"- Base rules data: `{inputs['base_rules_data']}`" if inputs.get("base_rules_data") else "- Base rules data: not supplied")
    if inputs.get("reference_bundle"):
        selected = inputs["reference_bundle"]
        lines.append(
            f"- Reference bundle provenance: Unciv {selected['reference_version']} "
            f"build {selected['reference_build']}, {selected['base_ruleset']}"
        )
    lines.append("")
    for title, key in (("Rules and translations", "rules"), ("Assets and atlases", "assets")):
        lines.extend((f"## {title}", ""))
        findings = report["checks"][key]
        if findings:
            lines.extend(
                f"- {item['severity']} [{item['code']}]: `{item['path']}`"
                + (f" `{item['json_pointer']}`" if item.get("json_pointer") else "")
                + f" — {item['message']}"
                for item in findings
            )
        else:
            lines.append("- No findings.")
        lines.append("")
    package = report["checks"]["packaging"]
    lines.extend(("## Packaging", "", f"- {package['status']} [{package['code']}]: {package['message']}", ""))
    if package.get("sha256"):
        lines.extend((f"- Temporary ZIP SHA-256: `{package['sha256']}`", ""))
    lines.extend(("## Evidence boundary", "", report["evidence_boundary"], ""))
    return "\n".join(lines)


def write_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.casefold() == ".json":
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        output_path.write_text(_markdown(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mod_dir", type=Path)
    parser.add_argument("--base-rules-data", type=Path)
    parser.add_argument("--strict-base-references", action="store_true")
    parser.add_argument("--source-only", action="store_true", help="validate source images without requiring packed atlases")
    parser.add_argument("--mechanics-registry", type=Path, default=rules.DEFAULT_REGISTRY)
    parser.add_argument("--no-mechanics-registry", action="store_true")
    parser.add_argument("--schema-dir", type=Path, default=rules.DEFAULT_SCHEMA_DIR)
    parser.add_argument("--no-schema-validation", action="store_true")
    parser.add_argument("--schema-exceptions", type=Path, default=rules.DEFAULT_SCHEMA_EXCEPTIONS)
    parser.add_argument("--base-ruleset", help="select a bundled base ruleset")
    parser.add_argument("--output", type=Path, required=True, help="Markdown or .json report path")
    args = parser.parse_args()

    registry = None if args.no_mechanics_registry else args.mechanics_registry
    schema_dir = None if args.no_schema_validation else args.schema_dir
    try:
        ruleset_selection = None
        selected_ruleset = args.base_ruleset
        if selected_ruleset is None and args.base_rules_data is None:
            selected_ruleset, detection = rules.require_base_ruleset(args.mod_dir)
            ruleset_selection = {"source": "auto-detected", **detection}
        report = run_preflight(
            args.mod_dir,
            args.base_rules_data,
            args.strict_base_references,
            args.source_only,
            registry,
            schema_dir,
            args.schema_exceptions,
            selected_ruleset,
            ruleset_selection,
        )
    except ValueError as error:
        parser.error(str(error))
    write_report(report, args.output)
    print(f"{report['status']}: {report['summary']['errors']} error(s), {report['summary']['warnings']} warning(s)")
    print(f"Report: {args.output.resolve()}")
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
