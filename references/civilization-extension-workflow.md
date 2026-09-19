# Civilization extension workflow

Use this guide when a request asks for a playable civilization with more than the basic name, leader, color, and city list. Use [feature-design-workflow.md](feature-design-workflow.md) to map requested behavior to supported game data before composing the civilization. Keep the result inside an existing base ruleset; a Mod can combine implemented game data and documented unique effects, but it cannot add a new engine mechanic.

## Design brief

Before writing JSON, establish:

- The base ruleset and whether the civilization is historical, fictional, or adapted from another setting.
- Its identity, intended playstyle, and one or two mechanics that express that identity.
- Whether the request includes a unique unit, building, improvement, art, Civilopedia text, or translation.
- Any constraints on power level, complexity, or similarity to existing civilizations.

Select the base ruleset before validation. The bundled rules and official Schemas retain their source-version metadata for provenance; they are structural references rather than a declared game-version requirement. Record the actual game build when runtime testing is performed.

## Build the civilization package

1. **Identity:** define the nation and leader names, RGB colors, city list, spy names when relevant, preferred victory type when relevant, and short diplomatic lines. Keep names and flavor text consistent with the concept.
2. **Core ability:** choose a small number of exact, documented Unciv unique patterns. Explain the effect in plain language and check how it combines with the chosen base ruleset. Do not invent a unique string; if the engine has no matching effect, offer the closest supported data-only design and state the gap.
3. **Unique content:** when useful, add a unit, building, or improvement with `uniqueTo` set to the civilization name and `replaces` set to the exact base object. Keep its era, cost, prerequisite, stats, and effect comparable to the replaced object. A replacement is optional when the design calls for a new object instead.
4. **Flavour and localization:** add concise Civilopedia text and any requested translations. Separate display text from gameplay: descriptive text does not implement an effect.
5. **Art plan:** list each needed icon or portrait, its exact object name, destination under `Images/`, and an image brief. The official tutorial specifies 100x100 Nation icons and 200x200 Unit and Building icons; those common sizes are checked by `validate_mod_assets.py`. If the user requests artwork and the `imagegen` skill is available, use it to create high-contrast icons with transparent backgrounds and no text, then verify their dimensions and filenames. Read the official icon and image guidance before preparing files; then use the bundled atlas packer and asset validator.

For field names and the official starter pattern, use the [new civilization tutorial](https://yairm210.github.io/Unciv/Modders/Making-a-new-Civilization/), [civilization JSON reference](https://yairm210.github.io/Unciv/Modders/Mod-file-structure/2-Civilization-related-JSON-files/), and [unique effects reference](https://yairm210.github.io/Unciv/Modders/uniques/).

## Balance review

For each ability or replacement, record its trigger, benefit, timing, cost, and a likely counterplay. Compare it with the nearest civilization or object in the selected ruleset. Check that bonuses do not compound across a whole empire unless that is intentional. Treat this as a design review, not a mathematical balance guarantee.

## Validation and play test

Run the combined source-stage preflight before asset work:

```sh
python3 <skill-directory>/scripts/unciv_mod.py check <mod-folder> --source-only \
  --base-ruleset "Civ V - Gods & Kings" \
  --output <report.json>
```

The version catalog resolves the matching Schema, reviewed exceptions, mechanics registry, and complete base snapshot. The unified command uses strict base-reference checks by default. When the Mod references expansion-only content it can detect the matching ruleset; shared references remain ambiguous and require an explicit `--base-ruleset`.

The checker applies the pinned official Schemas and catches duplicate object keys and local names, malformed RGB colors, repeated city names, and detectable references to base or Mod objects. Parameterized mechanic matching confirms the registered shape and owner category without inheriting exact-example runtime evidence. It does not prove that two effects are balanced or that a game will load the rules. Resolve remaining findings with official documentation and the in-game Ruleset Validator.

For art, run `validate_mod_assets.py --source-only`, pack images with `pack_mod_images.py`, and run full asset validation. Then test in Unciv when a game session is available:

- Run the built-in Ruleset Validator / “Locate mod errors” check.
- Start a new game with the intended base ruleset and extension enabled; confirm the civilization appears and can be selected.
- Check the opening text and city name, then reach or otherwise verify the unique unit/building and test the core ability's trigger.
- Record each check, observation, unexercised behavior, and base ruleset with `unciv_mod.py evidence`. Record the observed game build when available, then finalize the Markdown report. A recorded build describes the test; it is not a Skill version requirement.

See [the richer civilization sample](../examples/rich-civilization-extension/README.md) for a compact Nation + unique unit + unique building package.
