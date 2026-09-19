# Feature design workflow

Use this guide when a Mod request adds gameplay behavior or several connected content types, such as civilization abilities, units, buildings, improvements, technologies, policies, resources, or terrain.

## Capture the request

Record only the choices that affect the Mod's structure or gameplay:

- Base ruleset and Mod type.
- Theme, intended playstyle, and the player-facing effect.
- Trigger, scope, limits, prerequisites, and requested content objects.
- Desired complexity or power level.
- Art and language requirements when they affect the result.

Reuse details already given. If ambiguity changes the intended mechanic, present the viable interpretations and ask before generating JSON. For low-impact, reversible choices, state a reasonable assumption.

## Map intent to supported data

For each requested behavior, make a small mapping before editing files:

| Requested behavior | Unciv implementation | Data location and dependencies | Evidence | Acceptance check |
|---|---|---|---|---|
| What the player should experience | Exact object type, fields, and unique string | JSON file, base object, replacement, prerequisite, or resource | Official or bundled reference, or mark unverified | Observable game behavior |

Start with [mechanics-index.md](mechanics-index.md) for common patterns, then check official documentation when the feature may have changed across releases. Use the matching base-ruleset snapshot to check object names and compare values. Curated Mods can suggest structure, but do not establish that a field or unique is supported. Do not invent unique strings.

Classify each mechanic as one of:

- **Directly supported:** the requested effect maps to a documented game behavior.
- **Data-only approximation:** a nearby supported effect can represent part of the intent; explain the difference.
- **Requires engine support:** Mod data cannot create the requested behavior; identify the gap and offer a supported alternative when one exists.

Keep visible descriptions separate from implementation. A Civilopedia entry or custom unique text does not add an effect to the game.

## Assemble a coherent feature set

Choose content objects that express the requested theme and work together. For each ability or replacement, specify its trigger, target, strength, timing, cost, prerequisites, and whether its effects stack. Compare replacements with the nearest object in the selected base ruleset. Avoid adding extra systems that do not support the request.

When the design has tradeoffs, present concise options such as a faithful supported effect, a simpler approximation, or a version-dependent implementation. State the gameplay difference so the user can choose without needing to inspect raw JSON.

## Validate each feature

Run `scripts/unciv_mod.py check MOD --base-ruleset RULESET` to apply the bundled official Schemas and catch detectable nested references, mechanic parameter references, translation mistakes, applicability errors, asset problems, and packaging failures. The command uses strict base-reference checks by default and JSON output exposes stable diagnostic codes for automation. A parameterized mechanic match validates its registered shape and owner category, while recorded runtime evidence remains specific to the exact tested string. Static checks do not prove that mechanics behave as intended.

When a game session is available, use the in-game Ruleset Validator and test each mechanic with a concrete acceptance check. Use a named test fixture for setup that would otherwise depend on random spawns or long production. Use `scripts/unciv_mod.py evidence` to bind the exact preflight, installed ZIP, and screenshots by SHA-256 and record the base ruleset plus passed, failed, and unexercised checks. The target version is optional runtime context, not a validation input.

For large requests, deliver a short feature plan before generating the full package: the mapped effects, required files, version assumptions, and acceptance checks. For a small, clear request, apply the same checks without adding process overhead.
