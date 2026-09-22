# Mechanics index

Use this intent-based index to discover common Unciv effects. It is a starting point, not a complete list of supported mechanics.

**Sources:** use this page for intent-based discovery. For exact examples and parameterized templates reviewed against Unciv 4.22.0, consult [mechanics_registry.json](mechanics_registry.json), whose source links point to the tagged official documentation. An entry marked `documented` has no game result; only an exact example linked to recorded evidence carries a stronger evidence level. A different parameter value may match the same template, but it remains untested until separately exercised.

Square brackets are part of the unique syntax: keep them and replace their contents with valid values, names, or filters from the target ruleset. Keep stat capitalization exact. The “Applicable to” value is an official Unique category. The validator maps JSON owners such as Nations, Policies, Technologies, Buildings, and Founder Beliefs to `Global` where the versioned documentation allows those objects to grant global effects.

## Economy and growth

| Player intent | Documented pattern | Applicable to | Evidence |
|---|---|---|---|
| Add yields in every city | `[+1 Gold, +2 Production] [in all cities]` | Global, FollowerBelief | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |
| Reward trade routes | `[+1 Gold, +2 Production] from each Trade Route` | Global, FollowerBelief | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |
| Scale yields with population | `[+1 Gold, +2 Production] per [3] population [in all cities]` | Global, FollowerBelief | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |
| Reward a tile or improvement type | `[+1 Gold, +2 Production] from [Farm] tiles [in all cities]` | Global, FollowerBelief | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |
| Improve production of a unit class | `[+20]% Production when constructing [Melee] units [in all cities]` | Global, FollowerBelief | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |
| Provide a resource | `Provides [3] [Iron]` | Global, FollowerBelief, Improvement | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |

## Data-layer survival

| Player intent | Documented pattern | Applicable to | Evidence boundary |
|---|---|---|---|
| Express camp food pressure | `[+1 Food] [in all cities]` plus building/resource Food fields | Global, Nation, Building | City-level proxy; it is not per-unit hunger |
| Let a civilian gather resources | `Can build [Land] improvements on tiles` | Unit | Improvement access must be tested on a generated resource |
| Restrict resource improvements | `Can only be built to improve a resource` | Improvement | Does not create an inventory or crafting screen |
| Generate a custom bonus resource | `Generated on every [14] tiles` plus `terrainsCanBeFoundOn` | Resource | Placement is random unless a saved map fixture is used |
| Generate a weighted strategic resource | `Minor deposits generated with weight [20]` plus `terrainsCanBeFoundOn` | Resource | Availability and consumption need a runtime check |
| Start barbarian pressure earlier | `barbarianSpawnDelay`, `barbarianBonus`, and `turnBarbariansCanEnterPlayerTiles` | Difficulty | These settings do not guarantee a custom barbarian spawn pool |

These patterns can approximate gathering, shelter, supply, and enemy pressure with existing data. They do not add real-time day/night, independent unit hunger, an inventory UI, a forced single-city rule, or permanent death.

## Military and exploration

| Player intent | Documented pattern | Applicable to | Evidence |
|---|---|---|---|
| Increase combat strength | `[+20]% Strength` | Global, Unit | [Unit uniques](https://yairm210.github.io/Unciv/Modders/uniques/#unit-uniques); the reference says these percentage bonuses stack additively |
| Increase movement | `[3] Movement` | Global, Unit | [Unit uniques](https://yairm210.github.io/Unciv/Modders/uniques/#unit-uniques) |
| Move faster on selected terrain | `Double movement in [Fresh Water]` | Unit | [Unit uniques](https://yairm210.github.io/Unciv/Modders/uniques/#unit-uniques); the reference notes this behavior is cached |
| Give new melee units experience | `New [Melee] units start with [3] XP [in all cities]` | Global, FollowerBelief | [Global uniques](https://yairm210.github.io/Unciv/Modders/uniques/#global-uniques) |
| Reveal the map as a one-time effect | `Reveals the entire map` | Triggerable | [Triggerable uniques](https://yairm210.github.io/Unciv/Modders/uniques/#triggerable-uniques) |
| Prefer a starting terrain | `Start bias [Fresh Water]` | Nation, CityState | [Nation uniques](https://yairm210.github.io/Unciv/Modders/uniques/#nation-uniques) |

## Rewards and unlocks

| Player intent | Documented pattern | Applicable to | Evidence |
|---|---|---|---|
| Grant a free unit | `Free [Musketman] appears` | Triggerable | [Triggerable uniques](https://yairm210.github.io/Unciv/Modders/uniques/#triggerable-uniques) |
| Grant a free building | `Gain a free [Library] [in all cities]` | Triggerable, Global | [Triggerable uniques](https://yairm210.github.io/Unciv/Modders/uniques/#triggerable-uniques); the reference warns against free buildings that remove themselves |
| Grant a technology | `Discover [Agriculture]` | Triggerable | [Triggerable uniques](https://yairm210.github.io/Unciv/Modders/uniques/#triggerable-uniques) |
| Limit when a unit or building can be built | `Can only be built <after adopting [Oligarchy]>` | Building, Unit | [Building uniques](https://yairm210.github.io/Unciv/Modders/uniques/#building-uniques) |
| Scope an effect to a situation | `<when attacking>`, `<vs [Melee] units>`, `<during a Golden Age>` | Conditional modifier | [Conditional uniques](https://yairm210.github.io/Unciv/Modders/uniques/#conditional-uniques) |

Triggerable uniques are one-time effects. The official reference describes attaching them to technologies, policies, eras, or buildings for their corresponding trigger. A conditional modifier is separate from the effect and only works where that effect supports conditionals.

## Use and verify a pattern

1. Translate the request into an observable effect, then choose a pattern whose trigger and scope match it. Do not treat descriptive text as an implemented effect.
2. Replace parameters with exact names from the target ruleset. Confirm required object fields, prerequisites, and `replaces` relationships in the relevant JSON reference and base data.
3. Check the unique's “Applicable to” category and any documented stacking, caching, or self-removal warning. Combine conditionals only when the selected effect supports them.
4. Run `unciv_mod.py check` for official Schema validation, detectable references, and exact or parameterized registry matching. Then use the game's Ruleset Validator and a feature-specific in-game test. Exact matching can report recorded evidence for that string; template matching confirms only the registered mechanic shape and applicability.

For patterns not listed here, search the official reference linked above. Add entries only when the exact pattern, applicability, source, and review date can be recorded. Do not mark a pattern runtime-tested unless it has been exercised in a game build and the test is documented.
