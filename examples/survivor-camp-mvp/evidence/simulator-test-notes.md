# Survivor Camp MVP simulator test notes

Date: 2026-09-19

## Environment

- Device: iPhone 17 Pro Max simulator, iOS 26.5
- Game: Unciv 4.22.0 (1297)
- Base ruleset: `Civ V - Gods & Kings`
- Map setup: generated, Pangaea, Tiny, Quick speed

## Executed observations

1. The Receive Mod endpoint returned HTTP 200 with `Mod installed. Return to Unciv.`
2. The installed mod detail displayed `2 Techs, 1 Nations, 3 Units, 3 Buildings, 3 Resources, 3 Improvements`.
3. The in-game Ruleset Validator displayed a green check and `No problems found.`
4. Selecting `Survivor Camp MVP` exposed `Ember Kin` in the civilization picker.
5. A new game with `Survival Pressure` loaded with `Ember Kin`. The starting unit rotation showed a Settler, Gatherer, Trailfinder, and Camp Guard entries; the difficulty also supplied the additional Camp Guard starting unit, for five idle units in the opening turn.
6. Founding the city created `Ember Camp` and exposed `Pick a tech!` and `Pick construction`.
7. The city Stats screen showed Food `5`, Happiness `-4`, four turns to new population, and seven turns to expansion in the opening city state.
8. Selecting `Campcraft` showed the documented Campfire (`+2 Food`, `+1 Happiness`) and Workbench (`+2 Production`) unlocks; research was started in the live game.

## Not exercised in this run

- Finding and improving a generated Wild Berries, Timber, or Flint tile
- Completing Campfire, Workbench, Watchtower, or Camp Guard production
- Completing `Shelter Engineering`
- A barbarian encounter or combat attack
- Custom barbarian spawn-pool membership
- Terrain damage, independent unit hunger, real-time day/night, inventory recipes, forced single-city play, or permanent death

The observations above are operator-recorded from the simulator session. The bound package and preflight reports provide the reproducible static and installation artifacts; no simulator screenshot file was retained.
