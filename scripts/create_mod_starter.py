#!/usr/bin/env python3
"""Create a non-overwriting starter folder for a common Unciv Mod type."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


STARTER_TYPES = ("civilization-extension", "unit-building", "map-only")
TYPE_LABELS = {
    "civilization-extension": "Civilization extension",
    "unit-building": "Unit and building content",
    "map-only": "Map-only Mod",
}


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _starter_files(starter_type: str) -> dict[str, str]:
    if starter_type == "civilization-extension":
        return {
            "jsons/Nations.json": _json_text([
                {
                    "name": "New Nation",
                    "leaderName": "Leader",
                    "outerColor": [34, 103, 143],
                    "innerColor": [244, 225, 178],
                    "cities": ["Capital"],
                }
            ]),
        }
    if starter_type == "unit-building":
        return {
            "jsons/Units.json": "[]\n",
            "jsons/Buildings.json": "[]\n",
        }
    if starter_type == "map-only":
        return {}
    raise ValueError(f"Unsupported starter type: {starter_type}")


def _checklist(starter_type: str) -> list[str]:
    common = [
        "[ ] Confirm the base ruleset.",
        "[ ] Translate the brief into supported Mod data; record any gameplay or compatibility questions.",
    ]
    if starter_type == "civilization-extension":
        return common + [
            "[ ] Replace the sample Nation, leader, colors, and city values in `jsons/Nations.json`.",
            "[ ] Add unique abilities or replacement content only after checking the matching ruleset and official documentation.",
            "[ ] Run the Mod rules validator, then enable the Mod in a new game to test it.",
        ]
    if starter_type == "unit-building":
        return common + [
            "[ ] Add entries to `jsons/Units.json` and/or `jsons/Buildings.json`; the empty arrays are valid starting files.",
            "[ ] Copy required field patterns and references from the selected base ruleset; do not guess unit types, technologies, or unique strings.",
            "[ ] Run the Mod rules validator and Unciv's in-game Ruleset Validator, then test in a new game.",
        ]
    return common + [
        "[ ] Create and save the map in Unciv's Map Editor, then copy the real saved map file into `maps/`.",
        "[ ] Load the Mod and map in the test environment and check starting locations and ruleset compatibility.",
    ]


def _design_document(mod_name: str, brief: str, starter_type: str, base_ruleset: str) -> str:
    validation_ruleset = base_ruleset if base_ruleset != "To be confirmed" else "RULESET"
    content_files = {
        "civilization-extension": "`jsons/Nations.json`; add Units, Buildings, or Improvements only when the design needs them",
        "unit-building": "`jsons/Units.json` and `jsons/Buildings.json`; keep either array empty when unused",
        "map-only": "a real map exported from Unciv's Map Editor into `maps/`",
    }
    return (
        f"# {mod_name} design task\n\n"
        f"- Starter type: {TYPE_LABELS[starter_type]}\n"
        f"- Base ruleset: {base_ruleset}\n\n"
        f"## Player brief\n\n{brief.strip()}\n\n"
        "## Feature mapping\n\n"
        "| Player-visible result | Exact data or Unique | File and dependencies | Evidence | Acceptance check |\n"
        "|---|---|---|---|---|\n"
        "| Describe the requested result | Fill after checking supported data | Record object names and prerequisites | Link official or bundled evidence | State an observable game result |\n\n"
        f"## Expected content\n\n{content_files[starter_type]}.\n\n"
        "## Validation\n\n"
        "```sh\n"
        f"python3 <skill-directory>/scripts/unciv_mod.py check <mod-folder> --source-only --base-ruleset \"{validation_ruleset}\" --output <report.json>\n"
        "```\n\n"
        "The preflight applies the bundled official Schemas automatically. After static checks, run Unciv's in-game Ruleset Validator and execute each acceptance check. "
        "Record the runtime build when available, observations, and unexercised behavior in `verification.json`; distinguish a load smoke test from observed gameplay behavior.\n"
    )


def create_starter(
    output_dir: Path, mod_name: str, brief: str, starter_type: str, base_ruleset: str = "To be confirmed",
) -> Path:
    """Create a starter under output_dir and return its Mod folder."""
    if starter_type not in STARTER_TYPES:
        raise ValueError(f"starter_type must be one of: {', '.join(STARTER_TYPES)}")
    if not brief.strip():
        raise ValueError("brief must not be empty")

    slug = re.sub(r"[^A-Za-z0-9-]+", "-", mod_name.strip()).strip("-")
    if not slug:
        raise ValueError("mod_name must contain at least one letter or digit")

    mod_dir = Path(output_dir) / slug
    mod_dir.mkdir(parents=True, exist_ok=False)

    checklist = "\n".join(f"- {item}" for item in _checklist(starter_type))
    map_note = (
        "The `maps/` folder is empty until a real map is saved from Unciv's Map Editor and copied into it. "
        "See [the official Mod guide](https://yairm210.github.io/Unciv/Modders/Mods/) for the map workflow.\n\n"
        if starter_type == "map-only" else ""
    )
    readme = (
        f"# {slug} starter\n\n"
        f"Template: {TYPE_LABELS[starter_type]}\n\n"
        f"## Brief\n\n{brief.strip()}\n\n"
        f"## Next steps\n\n{checklist}\n\n"
        + map_note
        + "Use the selected ruleset's data and official Mod documentation for exact fields and supported behavior. "
        + "This folder is a starting point; it does not claim in-game or version compatibility.\n"
    )

    files = {
        "README.md": readme,
        "DESIGN.md": _design_document(slug, brief, starter_type, base_ruleset.strip() or "To be confirmed"),
        **_starter_files(starter_type),
    }
    if starter_type == "map-only":
        (mod_dir / "maps").mkdir()
    for relative_path, content in files.items():
        path = mod_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return mod_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=STARTER_TYPES, required=True, dest="starter_type")
    parser.add_argument("--mod-name", required=True, help="ASCII Mod folder name; spaces and punctuation become dashes")
    parser.add_argument("--brief", required=True, help="short description saved in the generated README")
    parser.add_argument("--base-ruleset", default="To be confirmed", help="base ruleset recorded in DESIGN.md")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd(), help="parent directory for the new Mod folder")
    args = parser.parse_args()

    try:
        mod_dir = create_starter(args.output_dir, args.mod_name, args.brief, args.starter_type, args.base_ruleset)
    except (FileExistsError, ValueError) as error:
        parser.error(str(error))
    print(f"Created Mod starter: {mod_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
