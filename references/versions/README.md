# Reference version catalog

`index.json` records the provenance of bundled official Schemas, normalized base rules, mechanics registry, and reviewed Schema exceptions. Users select a base ruleset; the current reference revision is resolved automatically.

The current reference data was sourced from Unciv 4.22.0 build 1297 and contains both `Civ V - Gods & Kings` and `Civ V - Vanilla`. This is provenance metadata rather than a required Mod target. The selector rejects rulesets that are not present in the catalog.

After adding or refreshing an entry, run:

```bash
python3 scripts/unciv_mod.py audit
python3 -m unittest discover -s tests -v
```
