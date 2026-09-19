# Unciv Mod authoring reference

This short reference is bundled with the Skill so basic Mod work does not depend on an Unciv source checkout. For exact fields and version-specific behavior, consult the official documentation linked in [official-docs.md](official-docs.md).

## Mod types

- **Extension Mod** adds content to an existing ruleset. Prefer it for a new civilization, unit, building, or other focused addition.
- **Base ruleset Mod** replaces the ruleset and needs a complete, internally consistent set of game definitions.
- **Ruleset-agnostic Mod** supplies content such as maps, images, audio, fonts, tilesets, or UI skins without changing ruleset definitions.

## Common structure

- `jsons/` contains ruleset data. Definitions are JSON objects grouped into files by object type; exact filenames and fields are documented in the official JSON reference.
- `Images/` contains supported game images and visual assets. Asset names and locations must match how the game references them.
- `maps/` can contain maps distributed with the Mod.
- `fonts/` can contain font files; consult the official guide for extension and loading requirements.
- A Mod archive should contain the Mod folder as its single top-level directory when using the bundled iOS transfer helper.

## Starter generator

Create a non-overwriting folder for one of the supported common Mod types:

```sh
python3 scripts/unciv_mod.py create --type civilization-extension --mod-name "Northshore" --brief "A coastal trading civilization" --output-dir ./mods
```

Use `unit-building` for empty `Units.json` and `Buildings.json` arrays, or `map-only` for a `maps/` folder with instructions. The civilization template includes sample Nation data. The generator records the brief and adds a type-specific checklist; it does not turn the brief into completed gameplay data. Finish the definitions using the selected ruleset, then run static and in-game checks.

The unit/building arrays are intentionally empty: copy the needed fields and object references from the selected base ruleset instead of guessing a universal unit type, technology, or unique. Complete the generated `DESIGN.md` mapping first. The static checker covers selected structural rules and detectable references; the in-game Ruleset Validator checks engine-level compatibility.

Run one source-stage preflight while creating the Mod:

```sh
python3 scripts/unciv_mod.py check <mod-folder> --source-only \
  --base-ruleset "Civ V - Gods & Kings" --output <report.md>
```

After packing any images, rerun without `--source-only`. The report combines bundled official Schema validation, cross-file references, translations, exact and parameterized mechanic-registry matches, assets, atlases, and temporary ZIP integrity while preserving the runtime evidence boundary.

For a map-only Mod, create and save a map in Unciv's Map Editor, then copy the saved file from the game's `maps` folder into the Mod's `maps/` folder. See [the official Mod guide](https://yairm210.github.io/Unciv/Modders/Mods/) for the source workflow.

## Rules and compatibility limits

- A Mod can add or change data definitions the game already understands. It cannot implement a new engine behavior or add a new unique effect on its own.
- Unique strings must match a documented supported pattern, including capitalization and parameter structure. A template match does not transfer runtime evidence from a different parameter value. Do not invent unique names based only on their English wording.
- Official Schema validation checks supported JSON shape from the recorded reference source, but it does not prove that object names, references, or unique strings behave correctly at runtime.
- Use official documentation to verify supported fields and unique patterns. Avoid making a release-wide compatibility claim based only on bundled references, examples, or a smoke test.

## Assets

- Use images, sounds, and fonts in technical formats supported by Unciv.
- Unciv loads packed image atlases. Put source images in `Images/<Type>/<ObjectName>.png`; use `Images.<AtlasName>/...` for additional atlases. The image type directory and untranslated object name must match the target ruleset, including capitalization. `TileSets`, skins, and several illustration types have deeper documented layouts.
- A populated `Images` folder packs to `game.atlas` and `game.png`. Each populated `Images.<AtlasName>` folder packs to `<AtlasName>.atlas` and `<AtlasName>.png`. `Atlases.json` belongs at the Mod root and lists the atlas names without extensions. Do not use both `Images` and `Images.game`, because they produce the same output names.
- Run `python3 <skill-directory>/scripts/validate_mod_assets.py <mod-folder> --source-only` before packing and the same command without `--source-only` after packing. It checks directory/path case for common image types, standard Nation/Unit/Building icon dimensions, ASCII atlas paths, PNG headers, whether sources or settings are newer than an atlas, atlas page files and region names, and the atlas list. Timestamp checks catch many stale atlases but do not prove file-content identity. The validator cannot prove that every object name exists in the target ruleset; compare names with the Mod JSON or the relevant upstream ruleset when the Mod inherits that object.
- Run `python3 <skill-directory>/scripts/pack_mod_images.py <mod-folder>` after any image change. It uses the LibGDX TexturePacker with Unciv-compatible settings, honors `TexturePacker.settings` in each image root, and regenerates `Atlases.json`. Keep the original images in the Mod alongside the generated atlases.
- The packer requires Java and uses checksum-verified LibGDX 1.14.2 jars. The helper can use an existing Gradle cache or download the pinned jars from Maven Central.
