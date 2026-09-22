# Survivor Camp MVP design

## Scope

- Base ruleset: `Civ V - Gods & Kings`
- Mod shape: extension Mod (`ModOptions.isBaseRuleset=false`)
- Dependency declaration: `ModOptions` requires `Civ V - Gods & Kings` so the extension is selected against the intended base ruleset.
- Default play: random map with the `Survival Pressure` difficulty
- Deterministic test setup: the same difficulty grants `Gatherer`, `Trailfinder`, and `Camp Guard` at game start and starts barbarian pressure after one turn
- Primary camp: `Ember Camp` is the test focus; the ruleset still permits additional cities
- Art and text: original names, descriptions, translations, and hand-authored icon images

## Player loop

1. Move the Trailfinder away from the camp to reveal nearby terrain.
2. Use the Gatherer to improve Wild Berries or Timber.
3. Research `Campcraft` and build a Campfire, then a Workbench.
4. Research `Shelter Engineering` after Mining and build a Watchtower.
5. Improve Flint and use it to train a Camp Guard.
6. Meet a barbarian after the configured pressure window and complete one combat.
7. Observe city Food, Growth, Happiness, and city strength as the data-layer survival pressure.

## Mechanism matrix

| Feature | Data implementation | Observable result | Boundary / risk | Acceptance check |
|---|---|---|---|---|
| Food pressure | Ember Kin nation `[+1 Food] [in all cities]`; Campfire `food=2`; Wild Berries and Forage Camp add Food | City Food total changes after founding/building/improving | This is city-level pressure, not individual hunger | Inspect city Food before and after Campfire or Forage Camp |
| Resource gathering | `TileResources.json` defines Wild Berries, Timber, Flint; `TileImprovements.json` defines matching improvements | Gatherer can reveal or improve a resource and the tile yield changes | Resource consumption is not modeled as an inventory | Improve one generated resource and inspect tile/city yields |
| Crafting | Workbench and Watchtower depend on `Campcraft`, `Shelter Engineering`, and `Campfire`; Camp Guard requires Flint | Production choices appear only after the required technology/building/resource | This is dependency-based production, not a free recipe UI | Research `Campcraft`, build Campfire then Workbench; verify Guard is available after Flint |
| Exploration | Trailfinder has 3 Movement and the base `Ignore terrain cost` promotion | The unit can move across the early map with fewer terrain restrictions | Terrain movement effects remain engine behavior and need runtime evidence | Move Trailfinder across at least two terrain types |
| Unit growth | `Camp Drill` promotion grants `[+10]% Strength`; Camp Guard also has `[+20]% Strength` | Promotion and strength modifier are visible in the unit detail | Applied combat math is only claimed after an attack | Inspect Camp Guard detail and complete one attack |
| Enemy pressure | `Survival Pressure` sets `barbarianSpawnDelay=1`, `barbarianBonus=0.25`, and `turnBarbariansCanEnterPlayerTiles=5` | Barbarian activity begins within the configured pressure window | A custom unit is not promised to enter the barbarian spawn pool | Record the first barbarian appearance turn and its observed type |
| Environment hazard | No new terrain damage Unique is used in the MVP | No unsupported hazard is presented as a guaranteed mechanic | Terrain damage remains a later, separately verified experiment | Mark as `not-exercised` in `verification.json` |

## Explicit non-goals

The MVP does not implement real-time day/night, per-unit hunger or temperature, freeform inventory recipes, a forced single-city rule, guaranteed custom barbarian spawning, or a survival game-over/permadeath state. If any becomes mandatory, move the requirement to an engine-extension project.

## Validation commands

From the repository root:

```sh
python3 scripts/unciv_mod.py check \
  examples/survivor-camp-mvp/Survivor-Camp-MVP \
  --base-ruleset "Civ V - Gods & Kings" \
  --source-only \
  --output examples/survivor-camp-mvp/preflight.json

python3 scripts/pack_mod_images.py examples/survivor-camp-mvp/Survivor-Camp-MVP
python3 scripts/unciv_mod.py check \
  examples/survivor-camp-mvp/Survivor-Camp-MVP \
  --base-ruleset "Civ V - Gods & Kings" \
  --output examples/survivor-camp-mvp/preflight-full.json
```

Run the in-game Ruleset Validator, then execute the loop above in a new game. Record the observed build as runtime context only; the Mod has no built-in target-version constraint.
