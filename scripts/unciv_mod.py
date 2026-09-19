#!/usr/bin/env python3
"""Unified command line interface for the Unciv Mod Creator Skill."""

from __future__ import annotations

import argparse
import json
import sys
from http.client import HTTPException
from pathlib import Path

import audit_reference_data
import check_mod
import create_mod_starter
import evidence_record
import package_and_upload_mod
import render_verification
import validate_mod_rules


def _select_ruleset(mod_dir: Path, explicit: str | None) -> tuple[str, dict]:
    if explicit:
        return explicit, {"source": "explicit", "status": "selected", "ruleset": explicit}
    ruleset, detection = validate_mod_rules.require_base_ruleset(mod_dir)
    return ruleset, {"source": "auto-detected", **detection}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    create = commands.add_parser("create", help="create a non-overwriting Mod starter")
    create.add_argument("--type", choices=create_mod_starter.STARTER_TYPES, required=True, dest="starter_type")
    create.add_argument("--mod-name", required=True)
    create.add_argument("--brief", required=True)
    create.add_argument("--base-ruleset", default="To be confirmed")
    create.add_argument("--output-dir", type=Path, default=Path.cwd())

    check = commands.add_parser("check", help="run strict combined preflight checks")
    check.add_argument("mod_dir", type=Path)
    check.add_argument("--base-ruleset")
    check.add_argument("--source-only", action="store_true")
    check.add_argument("--allow-unresolved-base-references", action="store_true")
    check.add_argument("--output", type=Path)

    pack = commands.add_parser("pack", help="create a deterministic ZIP")
    pack.add_argument("mod_dir", type=Path)
    pack.add_argument("--output", type=Path)

    upload = commands.add_parser("upload", help="package and upload to the iOS receiver")
    upload.add_argument("mod_dir", type=Path)
    upload.add_argument("--receiver-url", required=True)
    upload.add_argument("--access-code", required=True)
    upload.add_argument("--output", type=Path)

    verify = commands.add_parser("verify", help="validate an evidence record and render Markdown")
    verify.add_argument("record", type=Path)
    verify.add_argument("--output", type=Path, required=True)
    verify.add_argument("--check", action="store_true")

    audit = commands.add_parser("audit", help="audit bundled reference data")
    audit.add_argument("--output", type=Path)

    evidence = commands.add_parser("evidence", help="create and update runtime evidence")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)
    init = evidence_sub.add_parser("init")
    init.add_argument("--mod", required=True)
    init.add_argument("--base-ruleset", required=True)
    init.add_argument("--preflight", type=Path, required=True)
    init.add_argument("--zip", type=Path, required=True, dest="archive")
    init.add_argument("--output", type=Path, required=True)
    artifact = evidence_sub.add_parser("add-artifact")
    artifact.add_argument("record", type=Path)
    artifact.add_argument("path", type=Path)
    artifact.add_argument("--id", required=True)
    artifact.add_argument("--kind", required=True)
    item = evidence_sub.add_parser("add-check")
    item.add_argument("record", type=Path)
    item.add_argument("--id", required=True)
    item.add_argument("--status", choices=("passed", "failed", "not-exercised"), required=True)
    item.add_argument("--observation", required=True)
    item.add_argument("--artifact", action="append", default=[])
    finalize = evidence_sub.add_parser("finalize")
    finalize.add_argument("record", type=Path)
    finalize.add_argument("--output", type=Path, required=True)
    finalize.add_argument("--runtime-result", choices=("PASS", "PARTIAL", "FAIL"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "create":
            mod_dir = create_mod_starter.create_starter(
                args.output_dir, args.mod_name, args.brief, args.starter_type, args.base_ruleset,
            )
            print(f"Created Mod starter: {mod_dir.resolve()}")
            return 0
        if args.command == "check":
            ruleset, selection = _select_ruleset(args.mod_dir, args.base_ruleset)
            output = args.output or args.mod_dir.parent / f"{args.mod_dir.name}-preflight.json"
            report = check_mod.run_preflight(
                args.mod_dir,
                strict_base_references=not args.allow_unresolved_base_references,
                source_only=args.source_only,
                base_ruleset=ruleset,
                ruleset_selection=selection,
            )
            check_mod.write_report(report, output)
            print(f"{report['status']}: {report['summary']['errors']} error(s), {report['summary']['warnings']} warning(s)")
            print(f"Report: {output.resolve()}")
            return 1 if report["status"] == "FAIL" else 0
        if args.command in ("pack", "upload"):
            output = args.output or args.mod_dir.parent / f"{args.mod_dir.name}.zip"
            package_and_upload_mod.package_mod(args.mod_dir, output)
            print(f"Packaged Mod: {output.resolve()}")
            print(f"SHA-256: {package_and_upload_mod.sha256_file(output)}")
            if args.command == "upload":
                status, body = package_and_upload_mod.upload_mod(output, args.receiver_url, args.access_code)
                print(f"Receiver response ({status}): {body.strip()}")
                return 0 if status == 200 else 1
            return 0
        if args.command == "verify":
            rendered = render_verification.render(render_verification.load_record(args.record))
            if args.check:
                if args.output.read_text(encoding="utf-8") != rendered:
                    print(f"Verification report is stale: {args.output}", file=sys.stderr)
                    return 1
                print(f"Verification report is current: {args.output}")
            else:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
                print(f"Wrote verification report: {args.output.resolve()}")
            return 0
        if args.command == "audit":
            result = audit_reference_data.audit()
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"{result['status']}: {len(result['errors'])} error(s)")
            return 1 if result["errors"] else 0
        if args.evidence_command == "init":
            evidence_record.init_record(args.mod, args.base_ruleset, args.preflight, args.archive, args.output)
            print(f"Created evidence record: {args.output.resolve()}")
        elif args.evidence_command == "add-artifact":
            evidence_record.add_artifact(args.record, args.id, args.kind, args.path)
            print(f"Added artifact {args.id!r}")
        elif args.evidence_command == "add-check":
            evidence_record.add_check(args.record, args.id, args.status, args.observation, args.artifact)
            print(f"Added check {args.id!r}")
        else:
            evidence_record.finalize_record(args.record, args.output, args.runtime_result)
            print(f"Wrote verification report: {args.output.resolve()}")
        return 0
    except (HTTPException, OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    raise SystemExit(main())
