#!/usr/bin/env python3
"""Create and maintain evidence-bound Unciv runtime verification records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import render_verification


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: Path, parent: Path) -> str:
    return Path(os.path.relpath(path.resolve(), parent.resolve())).as_posix()


def _artifact(identifier: str, kind: str, path: Path, record_path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"Artifact does not exist: {path}")
    return {
        "id": identifier,
        "kind": kind,
        "path": _relative(path, record_path.parent),
        "sha256": _sha256(path),
    }


def _write(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_draft(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 3:
        raise ValueError("Evidence editing requires a schema_version 3 record")
    return data


def init_record(
    mod: str,
    base_ruleset: str,
    preflight_path: Path,
    archive_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    if output_path.exists():
        raise ValueError(f"Evidence record already exists: {output_path}")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    if not isinstance(preflight.get("summary"), dict) or preflight.get("status") not in ("PASS", "FAIL"):
        raise ValueError("Preflight artifact must be a JSON report produced by check_mod.py or unciv_mod.py check")
    record = {
        "schema_version": 3,
        "mod": mod,
        "test_environment": {"name": "Unciv"},
        "base_ruleset": base_ruleset,
        "tested_at": date.today().isoformat(),
        "runtime_result": "PARTIAL",
        "static_preflight": {
            "status": preflight["status"],
            "mode": preflight.get("mode", "unknown"),
            "errors": preflight["summary"].get("errors", 0),
            "warnings": preflight["summary"].get("warnings", 0),
            "report": _relative(preflight_path, output_path.parent),
        },
        "artifacts": [
            _artifact("preflight", "report", preflight_path, output_path),
            _artifact("installed-zip", "package", archive_path, output_path),
        ],
        "checks": [],
        "evidence_boundary": [
            "The bound artifacts identify the exact static preflight and install package used by this record.",
            "Only checks with recorded observations count as runtime evidence; unrecorded behavior remains unverified.",
        ],
    }
    _write(record, output_path)
    return record


def add_artifact(record_path: Path, identifier: str, kind: str, artifact_path: Path) -> dict[str, Any]:
    record = _load_draft(record_path)
    if any(item.get("id") == identifier for item in record.get("artifacts", [])):
        raise ValueError(f"Artifact id already exists: {identifier}")
    record.setdefault("artifacts", []).append(_artifact(identifier, kind, artifact_path, record_path))
    _write(record, record_path)
    return record


def add_check(
    record_path: Path,
    identifier: str,
    status: str,
    observation: str,
    artifact_ids: list[str],
) -> dict[str, Any]:
    record = _load_draft(record_path)
    if any(item.get("id") == identifier for item in record.get("checks", [])):
        raise ValueError(f"Check id already exists: {identifier}")
    known = {item.get("id") for item in record.get("artifacts", [])}
    unknown = sorted(set(artifact_ids) - known)
    if unknown:
        raise ValueError(f"Unknown artifact id(s): {', '.join(unknown)}")
    if not observation.strip():
        raise ValueError("Observation must not be empty")
    record.setdefault("checks", []).append({
        "id": identifier,
        "status": status,
        "observation": observation.strip(),
        **({"artifacts": artifact_ids} if artifact_ids else {}),
    })
    _write(record, record_path)
    return record


def finalize_record(record_path: Path, output_path: Path, runtime_result: str | None = None) -> str:
    record = _load_draft(record_path)
    if runtime_result is not None:
        record["runtime_result"] = runtime_result
        _write(record, record_path)
    rendered = render_verification.render(render_verification.load_record(record_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="bind a preflight JSON report and installed ZIP")
    init.add_argument("--mod", required=True)
    init.add_argument("--base-ruleset", required=True)
    init.add_argument("--preflight", type=Path, required=True)
    init.add_argument("--zip", type=Path, required=True, dest="archive")
    init.add_argument("--output", type=Path, required=True)
    artifact = subparsers.add_parser("add-artifact", help="hash and bind a runtime artifact")
    artifact.add_argument("record", type=Path)
    artifact.add_argument("path", type=Path)
    artifact.add_argument("--id", required=True)
    artifact.add_argument("--kind", required=True)
    check = subparsers.add_parser("add-check", help="append one observed runtime check")
    check.add_argument("record", type=Path)
    check.add_argument("--id", required=True)
    check.add_argument("--status", choices=("passed", "failed", "not-exercised"), required=True)
    check.add_argument("--observation", required=True)
    check.add_argument("--artifact", action="append", default=[])
    finalize = subparsers.add_parser("finalize", help="validate hashes and render Markdown")
    finalize.add_argument("record", type=Path)
    finalize.add_argument("--output", type=Path, required=True)
    finalize.add_argument("--runtime-result", choices=("PASS", "PARTIAL", "FAIL"))
    args = parser.parse_args()
    try:
        if args.command == "init":
            init_record(args.mod, args.base_ruleset, args.preflight, args.archive, args.output)
            print(f"Created evidence record: {args.output.resolve()}")
        elif args.command == "add-artifact":
            add_artifact(args.record, args.id, args.kind, args.path)
            print(f"Added artifact {args.id!r} to {args.record.resolve()}")
        elif args.command == "add-check":
            add_check(args.record, args.id, args.status, args.observation, args.artifact)
            print(f"Added check {args.id!r} to {args.record.resolve()}")
        else:
            finalize_record(args.record, args.output, args.runtime_result)
            print(f"Wrote verification report: {args.output.resolve()}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
