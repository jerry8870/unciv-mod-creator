# Preflight: Recipe-Lab

- Status: **PASS**
- Mode: source-only
- Checked at: 2026-09-19T08:25:58+00:00
- Errors: 0
- Warnings: 0

## Validation inputs

- Base ruleset selection: explicit — `Civ V - Gods & Kings`
- Official Schema provenance: Unciv 4.22.0
- Mechanics registry provenance: Unciv 4.22.0
- Reviewed Schema exceptions: `references/schema_exceptions.json`
- Base rules data: `references/snapshots/gk-baseline/rules.json`
- Reference bundle provenance: Unciv 4.22.0 build 1297, Civ V - Gods & Kings

## Rules and translations

- INFO [SCHEMA_VALIDATION_PASS]: `jsons/Buildings.json` — Passed official Unciv 4.22.0 Buildings.schema.json
- INFO [SCHEMA_VALIDATION_PASS]: `jsons/Difficulties.json` — Passed official Unciv 4.22.0 Difficulties.schema.json
- INFO [SCHEMA_VALIDATION_PASS]: `jsons/Nations.json` — Passed official Unciv 4.22.0 Nations.schema.json
- INFO [SCHEMA_VALIDATION_PASS]: `jsons/Units.json` — Passed official Unciv 4.22.0 Units.schema.json
- INFO [UNIQUE_EXACT_MATCH]: `jsons/Nations.json` — [0].uniques[0] matches mechanic 'global-trade-route-yield' (ruleset-validator-passed)
- INFO [UNIQUE_EXACT_MATCH]: `jsons/Units.json` — [0].uniques[0] matches mechanic 'unit-strength-percent' (ruleset-validator-passed)

## Assets and atlases

- INFO [ASSET_NOT_PRESENT]: `.` — No Images or Images.<AtlasName> folders found

## Packaging

- PASS [PACKAGE_INTEGRITY_PASS]: Created and integrity-checked a temporary ZIP with 5 member(s)

- Temporary ZIP SHA-256: `afbd9edaaaf9276b0d4bbad908a495f8a9fa249f8eade934e0760ec1644a7744`

## Evidence boundary

This report covers bundled official Schema, cross-file reference, registered-mechanic, translation, asset, atlas, and ZIP checks. It does not prove gameplay behavior, balance, or compatibility with an untested game build.
