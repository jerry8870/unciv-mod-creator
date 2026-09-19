# Recipe Lab verification

Target: Unciv 4.22.0 build 1297 with the Civ V - Gods & Kings base ruleset.

## Static evidence

[`preflight.md`](preflight.md) records **PASS** in source-only mode with 0 errors and 0 warnings. The preflight covers official Schema validation, cross-file references, registered mechanics, translations, assets, and temporary ZIP integrity.

## Bound artifacts

- **preflight** (report): [`preflight.md`](preflight.md) — `26553d1ac8baf4c5bec4503804d39f069e74857a0cf1f79ea481605ecb2c21b7`
- **installed-zip** (package): [`evidence/Recipe-Lab.zip`](evidence/Recipe-Lab.zip) — `afbd9edaaaf9276b0d4bbad908a495f8a9fa249f8eade934e0760ec1644a7744`
- **installed-content-screen** (screenshot): [`evidence/installed-content.png`](evidence/installed-content.png) — `0c0e50b59feb1a44acf79ca18b19fcb3ab3408723cf79811ed582cede29bb6eb`
- **ruleset-validator-screen** (screenshot): [`evidence/ruleset-validator.png`](evidence/ruleset-validator.png) — `193722b6ff2296abd377bc9367023dae6437acd1ad7effe2417cbafe1390ae65`
- **combat-modifier-screen** (screenshot): [`evidence/combat-modifier-detail.png`](evidence/combat-modifier-detail.png) — `62f666d87e8418a077bdd95a8a9ea799b386db4026adf8ca6b6ebd480ef5c080`
- **two-cities-screen** (screenshot): [`evidence/two-cities.png`](evidence/two-cities.png) — `ec2d6107dd631e246d451e58ee7fbeebcff164c660014d880d1c9de5db651d46`
- **runtime-crash-screen** (screenshot): [`evidence/runtime-crash.png`](evidence/runtime-crash.png) — `bcdd5c4b14cc8f1040e6f489a7defc485109f95b67be113e3fc3d3bebff1f2b2`
- **optimized-workflow-new-game** (screenshot): [`evidence/optimized-workflow-new-game.png`](evidence/optimized-workflow-new-game.png) — `f9423e18bb404215a35aec3e81baf2cd06a7c605bb2440808d658ab56cfc86be`

## Simulator evidence

Result: **PARTIAL** for the bounded smoke test on 2026-09-19.

- **PASS — receiver-upload:** The Receive Mod endpoint returned HTTP 200 with `Mod installed. Return to Unciv.` Evidence: installed-zip.
- **PASS — installed-content:** Installed Mods displayed 1 Nation, 1 Unit, and 1 Building for Recipe Lab. The later in-game Ruleset Validator screenshot verifies that the updated package containing Recipe Test loaded successfully. Evidence: installed-content-screen, ruleset-validator-screen.
- **PASS — ruleset-validator:** Check mod used Civ V - Gods & Kings and displayed a green check with `No problems found.` after the Recipe Test difficulty was added. Evidence: ruleset-validator-screen.
- **PASS — runtime-fixture:** The Recipe Test difficulty appeared in new-game settings and produced six idle units: two Settlers, one Worker, and three Recipe Guards including the era starting replacement.
- **PASS — two-city-setup:** Beacon Bay and Copper Haven were founded in the same Ancient-era test game. Evidence: two-cities-screen.
- **PASS — unit-replacement:** Recipe Guard appeared as the starting Warrior replacement and in the city production list. Evidence: combat-modifier-screen.
- **PASS — building-replacement:** Recipe Hall appeared in the city production flow and was observed completing in Beacon Bay; the retained screenshot establishes its production presence, not the completion notification. Evidence: two-cities-screen.
- **PASS — combat-modifier-loaded:** The live city production detail for Recipe Guard displayed `+20% Strength`. Evidence: combat-modifier-screen.
- **NOT EXERCISED — combat-math:** No attack preview was completed, so applied combat damage math remains unverified.
- **NOT EXERCISED — trade-route-yield:** Two cities were founded, but the road connection was not completed; the +1 Gold city-connection yield remains unverified. Evidence: two-cities-screen.
- **FAIL — runtime-ui-stability:** Unciv raised a recoverable NullPointerException in CityScreenCityPickerTable.update while the city production UI was operated; the app was restarted and the autosave resumed. Evidence: runtime-crash-screen.
- **PASS — unified-workflow-regression:** On 2026-09-19, the unified upload command produced the same SHA-256-bound package and the receiver returned HTTP 200. The in-game Ruleset Validator reported `No problems found.` for Civ V - Gods & Kings, and a new Recipe Test game loaded with six idle units including Recipe Guard. Evidence: installed-zip, optimized-workflow-new-game.

## Evidence boundary

- The retained artifacts establish deterministic ZIP installation, official in-game Ruleset Validator acceptance, two-city creation, replacement content availability, and live display of the +20% Strength unique.
- The session record also reports the Recipe Test starting-unit fixture and Recipe Hall completion, but no dedicated screenshot of those two observations was retained.
- It does not establish trade-route yield application, combat damage math, long-run balance, or compatibility with other game versions.
- The captured CityScreenCityPickerTable NullPointerException is an observed Unciv UI failure during test operation; this evidence does not identify the Mod or the test automation as its root cause.
- The 2026-09-19 regression artifact establishes that the optimized unified workflow still reaches a loaded Recipe Test game with the exact previously bound ZIP.
