# Survivor Camp MVP verification

Test environment: Unciv 4.22.0 build 1297 with the Civ V - Gods & Kings base ruleset.

## Static evidence

[`preflight-full.json`](preflight-full.json) records **PASS** in full mode with 0 errors and 0 warnings. The preflight covers official Schema validation, cross-file references, registered mechanics, translations, assets, and temporary ZIP integrity.

## Bound artifacts

- **preflight** (report): [`preflight-full.json`](preflight-full.json) — `ba9687d26417efead102836bf8fbb6a9008e1fa673383979f4f8406cb5654b10`
- **installed-zip** (package): [`evidence/Survivor-Camp-MVP-upload.zip`](evidence/Survivor-Camp-MVP-upload.zip) — `54f4fa02c6f2e3925922ddbb0b12463227d4cebc20e0be2618288564d3cfe8d5`
- **simulator-test-notes** (runtime-log): [`evidence/simulator-test-notes.md`](evidence/simulator-test-notes.md) — `1b0a2e5653fa9cf3d0c8e0942d3e20b0be1548dd24ffcc9839ab5262250ee3ff`

## Runtime evidence

Result: **PARTIAL** for the bounded smoke test on 2026-09-19.

- **PASS — receiver-upload:** The Receive Mod endpoint returned HTTP 200 and reported Mod installed. Evidence: installed-zip, simulator-test-notes.
- **PASS — installed-content:** Installed Mods displayed 2 Techs, 1 Nation, 3 Units, 3 Buildings, 3 Resources, and 3 Improvements. Evidence: simulator-test-notes.
- **PASS — ruleset-validator:** The in-game Ruleset Validator displayed a green check and No problems found. Evidence: simulator-test-notes.
- **PASS — extension-selection:** Selecting Survivor Camp MVP exposed Ember Kin in the civilization picker. Evidence: simulator-test-notes.
- **PASS — runtime-fixture:** A new generated Pangaea game with Survival Pressure loaded Ember Kin and showed the Settler, Gatherer, Trailfinder, and Camp Guard entries; the opening turn reported five idle units. Evidence: simulator-test-notes.
- **PASS — city-food-growth:** Founding Ember Camp exposed the tech and construction prompts. The city Stats screen showed Food 5, Happiness -4, four turns to new population, and seven turns to expansion. Evidence: simulator-test-notes.
- **PASS — tech-unlock:** Selecting Campcraft displayed the Campfire plus 2 Food plus 1 Happiness and Workbench plus 2 Production unlock descriptions, and research was started. Evidence: simulator-test-notes.
- **NOT EXERCISED — resource-improvement:** No generated Wild Berries, Timber, or Flint tile was improved during this run. Evidence: simulator-test-notes.
- **NOT EXERCISED — production-completion:** Campfire, Workbench, Watchtower, and Camp Guard production were not completed during this run. Evidence: simulator-test-notes.
- **NOT EXERCISED — combat:** No barbarian encounter or attack was completed, so combat results remain unverified. Evidence: simulator-test-notes.
- **NOT EXERCISED — barbarian-pressure:** The first barbarian appearance turn and custom barbarian spawn-pool membership were not observed. Evidence: simulator-test-notes.
- **NOT EXERCISED — environment-hazard:** No environment damage effect was implemented or exercised in this MVP. Evidence: simulator-test-notes.
- **NOT EXERCISED — survival-boundaries:** Independent unit hunger, real-time day/night, inventory recipes, forced single-city play, and permanent death were not exercised and are outside the MVP. Evidence: simulator-test-notes.

## Evidence boundary

- The bound artifacts identify the exact static preflight and install package used by this record.
- Only checks with recorded observations count as runtime evidence; unrecorded behavior remains unverified.
