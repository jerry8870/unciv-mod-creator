# Survivor Camp MVP

[中文说明](README.zh-CN.md)

A small, installable Unciv extension Mod that adapts a survival loop to the game's data model:

- **Explore:** Trailfinder scouts the random map.
- **Gather:** Gatherer improves Wild Berries, Timber, and Flint.
- **Build:** Campfire, Workbench, and Watchtower create a camp progression.
- **Research:** Campcraft and Shelter Engineering unlock the next survival stage.
- **Defend:** Camp Guard uses Flint and the Camp Drill promotion to hold the camp.
- **Pressure:** Survival Pressure starts barbarian activity early and increases its strength.

The Mod uses city Food, Growth, Happiness, resources, production dependencies, promotions, and city strength as a **data-layer survival pressure**. It does not claim individual hunger, real-time day/night, an inventory UI, forced single-city play, guaranteed custom barbarian spawning, or permanent death.

## Install and test

1. Select `Civ V - Gods & Kings` as the base ruleset.
2. Install this folder as a Mod, or package it with the repository helper. The Mod declares this base ruleset as an explicit dependency.
3. Run the Ruleset Validator.
4. Start a new game with `Ember Kin` and `Survival Pressure`.
5. Follow the loop in [DESIGN.md](DESIGN.md).
6. Compare runtime observations with [verification.json](../verification.json) and [VERIFICATION.md](../VERIFICATION.md) after the test record is finalized.

The default map is random. The difficulty's fixed starting units provide a repeatable setup for testing, while exact resource and barbarian coordinates remain map-dependent until a saved map fixture is added.
