#!/usr/bin/env python3
"""Render and check a Markdown verification report from a JSON evidence record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    schema_version = data.get("schema_version")
    if schema_version not in (2, 3):
        raise ValueError(f"Unsupported verification schema_version: {schema_version!r}")
    environment_field = "target_game" if schema_version == 2 else "test_environment"
    required = (
        "schema_version", "mod", environment_field, "base_ruleset", "tested_at",
        "runtime_result", "static_preflight", "checks", "evidence_boundary",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Missing verification fields: {', '.join(missing)}")
    if data["runtime_result"] not in ("PASS", "PARTIAL", "FAIL"):
        raise ValueError("runtime_result must be PASS, PARTIAL, or FAIL")
    if not isinstance(data.get("artifacts"), list) or not data["artifacts"]:
        raise ValueError("artifacts must be a non-empty array")
    artifact_ids: set[str] = set()
    for index, artifact in enumerate(data["artifacts"]):
        for field in ("id", "kind", "path", "sha256"):
            if not isinstance(artifact.get(field), str) or not artifact[field].strip():
                raise ValueError(f"artifacts[{index}].{field} must be a non-empty string")
        if artifact["id"] in artifact_ids:
            raise ValueError(f"Duplicate artifact id: {artifact['id']}")
        artifact_ids.add(artifact["id"])
        if not re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]):
            raise ValueError(f"artifacts[{index}].sha256 must be a lowercase SHA-256 digest")
        artifact_path = path.parent / artifact["path"]
        if not artifact_path.is_file():
            raise ValueError(f"artifacts[{index}] file does not exist: {artifact_path}")
        actual = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if actual != artifact["sha256"]:
            raise ValueError(f"artifacts[{index}] SHA-256 mismatch: {artifact_path}")
    if not isinstance(data["checks"], list) or not data["checks"]:
        raise ValueError("checks must be a non-empty array")
    for index, check in enumerate(data["checks"]):
        for field in ("id", "status", "observation"):
            if not isinstance(check.get(field), str) or not check[field].strip():
                raise ValueError(f"checks[{index}].{field} must be a non-empty string")
        if check["status"] not in ("passed", "failed", "not-exercised"):
            raise ValueError(f"checks[{index}].status has unsupported value {check['status']!r}")
        for artifact_id in check.get("artifacts", []):
            if artifact_id not in artifact_ids:
                raise ValueError(f"checks[{index}] references unknown artifact {artifact_id!r}")
    return data


def render(record: dict[str, Any]) -> str:
    game = record.get("test_environment", record.get("target_game", {}))
    preflight = record["static_preflight"]
    target = game.get("name", "Unciv")
    if game.get("version") is not None:
        target += f" {game['version']}"
    if game.get("build") is not None:
        target += f" build {game['build']}"
    if record["schema_version"] == 2:
        target_line = f"Target: {game['name']} {game['version']} build {game['build']} with the {record['base_ruleset']} base ruleset."
        runtime_heading = "## Simulator evidence"
    else:
        target_line = f"Test environment: {target} with the {record['base_ruleset']} base ruleset."
        runtime_heading = "## Runtime evidence"
    lines = [
        f"# {record['mod']} verification", "",
        target_line, "",
        "## Static evidence", "",
        (
            f"[`{preflight['report']}`]({preflight['report']}) records **{preflight['status']}** in "
            f"{preflight['mode']} mode with {preflight['errors']} errors and {preflight['warnings']} warnings. "
            "The preflight covers official Schema validation, cross-file references, registered mechanics, translations, assets, and temporary ZIP integrity."
        ), "",
        "## Bound artifacts", "",
    ]
    for artifact in record["artifacts"]:
        lines.append(f"- **{artifact['id']}** ({artifact['kind']}): [`{artifact['path']}`]({artifact['path']}) — `{artifact['sha256']}`")
    lines.extend(("",
        runtime_heading, "",
        f"Result: **{record['runtime_result']}** for the bounded smoke test on {record['tested_at']}.", "",
    ))
    for check in record["checks"]:
        label = {
            "passed": "PASS",
            "failed": "FAIL",
            "not-exercised": "NOT EXERCISED",
        }[check["status"]]
        evidence = ", ".join(check.get("artifacts", []))
        suffix = f" Evidence: {evidence}." if evidence else ""
        lines.append(f"- **{label} — {check['id']}:** {check['observation']}{suffix}")
    lines.extend(("", "## Evidence boundary", ""))
    lines.extend(f"- {item}" for item in record["evidence_boundary"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="fail if the output does not match the rendered record")
    args = parser.parse_args()
    try:
        rendered = render(load_record(args.record))
        if args.check:
            current = args.output.read_text(encoding="utf-8")
            if current != rendered:
                print(f"Verification report is stale: {args.output}", file=sys.stderr)
                return 1
            print(f"Verification report is current: {args.output}")
            return 0
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote verification report: {args.output}")
        return 0
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
