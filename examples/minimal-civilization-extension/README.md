# Minimal civilization extension

Target: Unciv 4.22.0, app build 1297, using the Civ V - Gods & Kings base ruleset.

`Northshore/` is the installable Mod folder. It adds one major civilization with a leader, colors, and city names. It has no custom images or unique abilities; this sample tests the basic civilization extension path.

## Verification

- Parsed `Nations.json` and ran the Mod Creator asset check in source-only mode. It reported no errors; its only informational note was that this sample has no image folders, as expected.
- Verified `Northshore.zip` integrity and confirmed it contains only `Northshore/jsons/Nations.json` under the `Northshore/` folder.
- Packaged `Northshore.zip` with the Mod Creator transfer helper. The iOS Simulator receiver returned HTTP 200 and confirmed `Mod installed`.
- On iOS Simulator, with Unciv 4.22.0 build 1297, selected Civ V - Gods & Kings plus Northshore, started a new game, and founded the first city. The game displayed `Northport`, confirming the extension loaded and its city list was used.

This smoke test covers the basic nation-loading and new-game path in that simulator build. It does not test custom art, unique abilities, or other Unciv versions.
