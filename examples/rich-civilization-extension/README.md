# Tideward civilization extension

This worked example demonstrates a richer extension Mod: a playable civilization, a core trade ability, one replacement unit, and one replacement building. Its unique strings reuse effects present in the bundled Civ V - Gods & Kings baseline; the example has not been play-tested and does not include custom art or translations.

Run the static checks from the Skill directory:

```sh
python3 scripts/validate_mod_rules.py examples/rich-civilization-extension/Tideward \
  --base-ruleset "Civ V - Gods & Kings" --strict-base-references
python3 scripts/validate_mod_assets.py examples/rich-civilization-extension/Tideward --source-only
```

Add Nation, Unit, and Building icons when the design calls for custom art. Follow [the civilization workflow](../../references/civilization-extension-workflow.md) for art, balance review, localization, and in-game testing.
