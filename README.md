# unciv-mod-creator

**English** | [简体中文](README.zh-CN.md)

A vendor-neutral Agent Skill for designing, creating, validating, packaging, installing, and testing data-driven Unciv Mods. It combines bundled game references, repeatable validators, deterministic packaging, and bounded runtime evidence in one reusable workflow.

## What This Skill Can Do

| Capability | What you get |
|---|---|
| Design supported gameplay | Converts a player-facing idea into Unciv objects, fields, Unique strings, dependencies, and observable acceptance checks. It identifies data-only approximations and mechanics that require engine changes. |
| Create Mod starters | Generates non-overwriting starters for civilization extensions, unit/building extensions, and map-only Mods, with a design worksheet and type-specific checklist. |
| Validate against a base ruleset | Resolves the selected base ruleset to bundled official Schemas, reviewed Schema exceptions, mechanics data, and complete base-rule snapshots. Unsupported rulesets fail clearly. |
| Check rules and translations | Detects malformed JSON, duplicate keys and names, invalid object shapes, detectable broken cross-file references, registered Unique parameter or applicability errors, and translation placeholder mistakes. |
| Prepare and validate artwork | Checks image paths, case, PNG headers, common icon dimensions, atlas names, atlas pages, source freshness, and packed regions. It can build LibGDX texture atlases with checksum-verified dependencies. |
| Produce one preflight report | Combines rules, translations, assets, atlases, and ZIP integrity into a Markdown or JSON report with selected validation inputs and a SHA-256 for the temporary deterministic package. |
| Package and deliver a Mod | Creates a reproducible ZIP with stable timestamps, ordering, permissions, and metadata filtering. It can stop after packaging or upload the new archive to Unciv's iOS Receive Mod endpoint. |
| Record runtime verification | Guides the in-game Ruleset Validator, new-game smoke tests, and feature-specific checks. Results can be stored in `verification.json`, bound to reports, ZIPs, and screenshots by SHA-256, then rendered as Markdown. |
| Query the built-in encyclopedia data | Searches bundled ruleset snapshots by category, exact name, or text; returns Simplified Chinese translations when available and the direct upstream source URL for each JSON category. |
| Maintain the reference bundle | Audits official Schema files, base rulesets, manifests, checksums, and reviewed exceptions. The repository includes automated tests and cross-platform CI. |
| Automate the full workflow | Provides one `unciv_mod.py` entry point for starter creation, preflight, packaging, upload, reference audit, report rendering, and evidence recording while keeping the focused scripts available. |

## Supported Scope

- **Bundled base rulesets:** `Civ V - Gods & Kings` and `Civ V - Vanilla`.
- **Common Mod types:** civilization extensions, unit/building extensions, map-only Mods, and hand-authored data or visual Mods that follow Unciv's documented format.
- **Outputs:** Mod folders, design worksheets, preflight reports, packed atlases, deterministic ZIPs, upload results, and evidence-bound verification reports.
- **Runtime testing:** available when the Agent host can control an iOS Simulator or when a tester follows the same checks on a physical device.

A data Mod can combine objects and Unique effects already supported by Unciv. It cannot introduce new engine behavior. Static validation does not prove gameplay behavior, balance, or compatibility with every game build. Bundled references retain their source-version metadata for auditability without requiring a user-selected game version.

## Quick Start

### 1. Install

From this repository's root directory:

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)" ~/.agents/skills/unciv-mod-creator
```

Reload the Agent host after installation.

### 2. Ask for a complete workflow

```text
$unciv-mod-creator Create a Civ V - Gods & Kings civilization Mod with a unique melee unit and culture building. Validate it, package it, and produce a verification plan.
```

You can also ask it to inspect an existing Mod:

```text
$unciv-mod-creator Audit /absolute/path/to/My-Mod, fix the confirmed problems, and generate a strict preflight report for Civ V - Gods & Kings.
```

### 3. Run the preflight directly

```bash
python3 -m pip install -r requirements.txt
python3 scripts/unciv_mod.py check /absolute/path/to/My-Mod \
  --source-only \
  --output /absolute/path/to/My-Mod-preflight.json
```

The command detects the base ruleset only when the Mod contains a reference that distinguishes one bundled ruleset. If the references are shared by multiple rulesets, it stops and lists the valid `--base-ruleset` choices instead of guessing. `check` uses strict base-reference validation by default. Use `--source-only` while artwork is unpacked, then run it again without that option after atlas packing.

## Unified Command

```text
python3 scripts/unciv_mod.py {create,check,query,pack,upload,verify,audit,evidence} ...
```

- `create` creates a non-overwriting starter.
- `check` selects or detects a base ruleset and writes a strict Markdown or JSON preflight.
- `query` searches the bundled Civilopedia-style data and prints the matching local record and upstream source URL.
- `pack` creates a deterministic ZIP; `upload` creates the ZIP and sends it to the iOS receiver.
- `verify` validates artifact hashes and renders a verification report.
- `audit` checks the bundled reference manifests, Schemas, baselines, and reviewed exceptions.
- `evidence` initializes a record, binds hashed artifacts, records runtime checks, and finalizes Markdown evidence.

Focused scripts remain available for callers that need only one operation.

## Installation Options

### Global installation

A global installation makes the Skill discoverable from every project.

Link an existing clone:

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/unciv-mod-creator ~/.agents/skills/unciv-mod-creator
```

Or clone it directly:

```bash
git clone <repository-url> ~/.agents/skills/unciv-mod-creator
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
git clone <repository-url> "$HOME\.agents\skills\unciv-mod-creator"
```

### Install for one project

From the target project's root directory:

```bash
mkdir -p .agents/skills
ln -s /absolute/path/to/unciv-mod-creator .agents/skills/unciv-mod-creator
```

Or place a clone directly in the project:

```bash
git clone <repository-url> .agents/skills/unciv-mod-creator
```

Tools that support the Agent Skills format can import the whole directory. Other tools can use [SKILL.md](SKILL.md) as workflow instructions and call the Python scripts directly.

## Typical Workflows

### Create a starter

```bash
python3 scripts/unciv_mod.py create \
  --type civilization-extension \
  --mod-name "My-Civilization" \
  --brief "A civilization with a unique unit and building" \
  --base-ruleset "Civ V - Gods & Kings" \
  --output-dir ./output
```

Supported starter types are `civilization-extension`, `unit-building`, and `map-only`. The starter is a structured beginning; complete its `DESIGN.md` before treating it as implemented gameplay.

### Validate rules only

```bash
python3 scripts/unciv_mod.py check /absolute/path/to/My-Mod \
  --base-ruleset "Civ V - Gods & Kings"
```

JSON reports provide stable diagnostic `code` values. Findings can also include `json_pointer`, `value`, and a concrete `suggestion`, which makes editor, CI, and other tool integrations deterministic.

### Query encyclopedia data

The bundled snapshots cover the rules JSON behind the game's Civilopedia-style
categories, including technologies, units, buildings, promotions, policies,
resources, terrain, difficulties, victory types, unit names, and more. The
command works offline and includes a direct upstream source link in its output:

```bash
python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --type Techs \
  --name Agriculture

python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --type Units \
  --search "barbarian" \
  --language zh \
  --json
```

Use `--list-types` to see all available categories and their source links. See
[references/encyclopedia.md](references/encyclopedia.md) for the category map
and the boundary between bundled rules data and source-only tutorial or UI
pages. The printed reference version is provenance metadata; users do not need
to select a game version.

### Validate and pack artwork

```bash
python3 scripts/validate_mod_assets.py /absolute/path/to/My-Mod --source-only
python3 scripts/pack_mod_images.py /absolute/path/to/My-Mod
python3 scripts/validate_mod_assets.py /absolute/path/to/My-Mod
```

Atlas packing requires Java and may download checksum-verified LibGDX 1.14.2 jars from Maven Central when they are not already cached.

### Package without uploading

```bash
python3 scripts/unciv_mod.py pack /absolute/path/to/My-Mod \
  --output /absolute/path/to/My-Mod.zip
```

The script never overwrites an existing ZIP. The archive must be outside the Mod folder, and archives above the receiver's 256 MiB limit are rejected.

### Package and upload to Unciv iOS

Open **Mods → Receive Mod** in Unciv, then run:

```bash
python3 scripts/unciv_mod.py upload /absolute/path/to/My-Mod \
  --receiver-url http://192.168.x.x:port/ \
  --access-code 123456 \
  --output /absolute/path/to/My-Mod-upload.zip
```

The receiver must use the displayed localhost or private-network IPv4 address. HTTP 200 confirms transfer; it does not prove the Mod loads or its gameplay works.

### Record and render runtime evidence

```bash
python3 scripts/unciv_mod.py evidence init \
  --mod My-Mod \
  --base-ruleset "Civ V - Gods & Kings" \
  --preflight /absolute/path/to/My-Mod-preflight.json \
  --zip /absolute/path/to/My-Mod.zip \
  --output /absolute/path/to/verification.json

python3 scripts/unciv_mod.py evidence add-check /absolute/path/to/verification.json \
  --id ruleset-validator \
  --status passed \
  --observation "The in-game Ruleset Validator reported no problems."

python3 scripts/unciv_mod.py evidence finalize /absolute/path/to/verification.json \
  --runtime-result PASS \
  --output /absolute/path/to/VERIFICATION.md
```

The workflow does not require a target game version. A tester may add an observed version or build to `test_environment` when useful. The record distinguishes passed, failed, and unexercised checks and verifies the SHA-256 of every bound artifact.

### Audit the Skill and run its tests

```bash
python3 scripts/unciv_mod.py audit
python3 -m unittest discover -s tests -v
```

The machine-readable validation surface is declared in [references/validation_coverage.json](references/validation_coverage.json). It maps official Schema coverage, semantic references, additional checks, integration scenarios, and runtime evidence boundaries.

## Requirements

- Python 3.10 or later.
- Install Python dependencies with `python3 -m pip install -r requirements.txt`.
- Java is required only for image-atlas packing.
- Automated game UI testing requires access to an iOS Simulator with Unciv installed. The same runtime checks can be performed manually on a physical device.

## Examples and Key Files

- [SKILL.md](SKILL.md): the complete Agent workflow and evidence rules.
- [references/knowledge-index.md](references/knowledge-index.md): entry point for versioned references and authoring guidance.
- [references/encyclopedia.md](references/encyclopedia.md): Civilopedia category map, query examples, source links, and data/runtime boundaries.
- [references/versions/index.json](references/versions/index.json): bundled reference provenance and base-ruleset catalog.
- [references/mechanics_registry.json](references/mechanics_registry.json): reviewed Unique examples, templates, applicability, and test evidence.
- [scripts/unciv_mod.py](scripts/unciv_mod.py): unified workflow command.
- [scripts/check_mod.py](scripts/check_mod.py): focused combined-preflight command and library.
- [references/validation_coverage.json](references/validation_coverage.json): machine-readable validation coverage and boundaries.
- [examples/minimal-civilization-extension/](examples/minimal-civilization-extension/): simulator-tested minimal civilization.
- [examples/rich-civilization-extension/](examples/rich-civilization-extension/): richer static example with a Nation, unit, and building.
- [examples/tested-feature-recipes/](examples/tested-feature-recipes/): evidence-bound simulator recipe with passed, failed, and unexercised checks.
- [examples/survivor-camp-mvp/](examples/survivor-camp-mvp/): bilingual, installable turn-based survival example with a mechanism matrix and partial simulator evidence.
