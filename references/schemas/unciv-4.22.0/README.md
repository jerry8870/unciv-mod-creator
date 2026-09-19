# Unciv 4.22.0 official Schemas

This directory contains the official JSON Schemas from the Unciv `4.22.0` tag. `manifest.json` records the source commit, source URLs, and SHA-256 checksums. Runtime validation is local and does not download files.

Refresh the baseline and Schema bundle together with:

```sh
python3 scripts/update_unciv_reference_data.py
```

The upstream `Personalities.schema.json` in this tag does not declare the `denounceWillingness` field used by the same tag's bundled G&K personalities. The files here remain byte-for-byte upstream copies, so that upstream mismatch is preserved rather than silently patched. Treat a Schema result as structural evidence and use the in-game Ruleset Validator as the engine authority.

The reviewed mismatch is recorded in `references/schema_exceptions.json`. `scripts/unciv_mod.py audit` validates both bundled rulesets against these official files, requires each mismatch to match an explicit exception, and fails when a declared exception becomes stale.
