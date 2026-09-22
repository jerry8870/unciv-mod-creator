# Knowledge index

Use only references relevant to the requested Mod. Select the base ruleset through [versions/index.json](versions/index.json); never substitute another ruleset silently. Source versions in the catalog are provenance metadata and are resolved automatically.

## Bundled game-data baseline

The bundled snapshots are [snapshots/gk-baseline/](snapshots/gk-baseline/) for **Civ V - Gods & Kings** and [snapshots/vanilla-baseline/](snapshots/vanilla-baseline/) for **Civ V - Vanilla**, both from Unciv 4.22.0. Their manifests record the source commit, build, source checksums, and generated-file checksums.

- `rules.json` contains every JSON rule file available in the selected upstream ruleset directory: 25 for Gods & Kings and 20 for Vanilla. It includes UnitTypes, promotions, resources, terrain, eras, policies, beliefs when present, and other base objects. Use it to look up existing objects and baseline values, or to detect likely duplicates when extending that ruleset.
- `zh.json` contains Simplified Chinese strings for this ruleset.
- `manifest.json` records the pinned game version, build, source commit, and checksums.

For Civilopedia-style lookups, use [encyclopedia.md](encyclopedia.md) and
`python3 scripts/unciv_mod.py query`. It maps the in-game concepts shown in the
encyclopedia to bundled JSON categories, returns Simplified Chinese translations
when available, and exposes each category's direct upstream source URL. Tutorial
and other presentation pages that are not standalone rules records are marked as
source-only there.

This is complete for the rules JSON files in the pinned upstream directory, but it is still reference data rather than runtime proof. The matching official Schema bundle is in [schemas/unciv-4.22.0/](schemas/unciv-4.22.0/). When a requested feature depends on engine behavior, test it in the target game before claiming support.

## Choose a reference

| Need | Reference |
|---|---|
| Select matching Schema, mechanics, and base rules | [versions/index.json](versions/index.json); `unciv_mod.py check` detects a unique match or requires `--base-ruleset` |
| Audit official Schema and baseline drift | `scripts/unciv_mod.py audit` and [schema_exceptions.json](schema_exceptions.json) |
| Find documented unique patterns by player-facing intent | [mechanics-index.md](mechanics-index.md) |
| Check exact Unique examples, parameterized templates, applicability, and recorded 4.22.0 evidence | [mechanics_registry.json](mechanics_registry.json); a template match does not extend exact-example test evidence to different parameter values |
| Validate JSON shape against bundled official definitions | [schemas/unciv-4.22.0/](schemas/unciv-4.22.0/); the directory name records source provenance and `unciv_mod.py check` applies the Schemas automatically |
| Turn a requested gameplay effect into supported Unciv data and feature-specific acceptance checks | [feature-design-workflow.md](feature-design-workflow.md) |
| Mod types, folder layout, data-only limits, and image packing | [mod-authoring-reference.md](mod-authoring-reference.md) |
| Start a civilization extension, unit/building Mod, or map-only Mod from a brief | `scripts/unciv_mod.py create`; read the generated `README.md` before filling it |
| Full playable civilization with an ability, replacement unit/building, balance review, and play-test | [civilization-extension-workflow.md](civilization-extension-workflow.md) |
| Exact JSON formats, supported uniques, images, and audio | [official-docs.md](official-docs.md); check release notes when behavior may have changed |
| Repository structures and design choices | [curated-examples.md](curated-examples.md); examples are not compatibility authorities |
| Reuse bounded, simulator-tested economy, unit replacement, and building replacement examples | [tested feature recipes](../examples/tested-feature-recipes/README.md); read `VERIFICATION.md` for the actual test boundary |
| Existing base object names, values, and Chinese strings | The matching ruleset baseline snapshot above; use as reference data, not as compatibility proof |
| Public Mod repository discovery | [mod_catalog.json](mod_catalog.json); check version support separately |
| iOS ZIP transfer workflow | [ios-transfer.md](ios-transfer.md) |

Run `scripts/unciv_mod.py check MOD --base-ruleset RULESET` for the combined strict static preflight report. The report still does not prove gameplay behavior; use `scripts/unciv_mod.py evidence` to bind the installed ZIP, report, and screenshots by SHA-256 and render `verification.json` as Markdown. See [validation_coverage.json](validation_coverage.json) for the machine-readable validation surface.
