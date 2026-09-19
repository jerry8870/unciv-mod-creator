# Curated Unciv Mod examples

These repositories illustrate different Mod shapes. Read them as examples of structure and design choices, then verify supported fields and unique strings against official Mod documentation. Test release-sensitive behavior in the target game when needed. These repositories are not compatibility authorities.

## Starting structure

- [Unciv-mod-example](https://github.com/yairm210/Unciv-mod-example) is the upstream template for a new civilization. Its root `jsons/` and `Images/` folders, `Atlases.json`, and GitHub workflow make it a compact starting point for an extension Mod. It is a template repository and is not included in the `unciv-mod` topic snapshot.

## Gameplay and rulesets

- [RekMOD](https://github.com/ravignir/RekMOD) is a large ruleset Mod with new and rebalanced civilizations, buildings, units, and mechanics. Use its `jsons/` and `Images/` as examples of organizing a broad data-driven ruleset. Its default branch and snapshot metadata are in `mod_catalog.json`.
- [Civ6-mod](https://github.com/EmperorPinguin/Civ6-mod) is a base ruleset that aims to recreate Civilization VI inside Unciv. Its `docs/`, `scripts/`, and README discuss implementation approximations and validation. The project describes itself as a work in progress; use it to study choices and limits, not as proof that a mechanic works in every game build.

## Maps and graphics

- [Community-Maps](https://github.com/Caballero-Arepa/Community-Maps) is a map-only Mod. Its `maps/` folder and README show a compact distribution shape; the README also documents a post-load resource-spreading workflow.
- [UnTile-Civ6-Tileset](https://github.com/Malwen/UnTile-Civ6-Tileset) is a visual Mod. Its `Images/TileSets/UnTile`, `jsons/TileSets`, `Atlases.json`, and packed atlas files show how a tileset is registered and packaged.
