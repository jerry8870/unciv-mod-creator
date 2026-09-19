# Civ V - Gods & Kings baseline

`rules.json` combines all 25 rules JSON files from the Unciv 4.22.0 `Civ V - Gods & Kings` directory. `zh.json` contains the non-empty Simplified Chinese translations from the matching tagged translation file. `manifest.json` records the source commit, build, source URLs, and SHA-256 checksums.

Refresh this snapshot and the matching official Schema bundle with:

```sh
python3 scripts/update_unciv_reference_data.py
```

This snapshot supports deterministic name and reference checks. It does not replace the in-game Ruleset Validator or feature-specific gameplay tests.
