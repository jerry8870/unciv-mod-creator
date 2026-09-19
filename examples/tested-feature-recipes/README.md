# Feature recipe smoke-test package

`Recipe-Lab/` combines three small recipes in one Civ V - Gods & Kings extension Mod so they can be installed and checked together:

1. **Economy:** the Nation uses `[+1 Gold] from each Trade Route`.
2. **Military:** `Recipe Guard` replaces `Warrior` and uses `[+20]% Strength`.
3. **Building:** `Recipe Hall` replaces `Monument`, keeping the same cost and maintenance while increasing Culture from 2 to 3.

Each recipe has a direct observation target: the civilization ability appears in setup, the replacement starting unit appears for the civilization, and the replacement building appears in the capital's construction choices. See `verification.json` for the machine-readable evidence and `VERIFICATION.md` for its generated human-readable report.

`Recipe Test` is a deterministic runtime-test difficulty. It adds one Settler, one Worker, and two Recipe Guards so a tester can found a second city, connect it by road, and exercise the unit's combat modifier without waiting for production. Use it only for the recipe verification run.

The recipes target the bundled Civ V - Gods & Kings reference. Recorded evidence applies only to the stated test build and actions; it is not a blanket compatibility or balance claim.
