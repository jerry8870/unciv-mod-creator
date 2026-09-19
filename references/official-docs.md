# Official Unciv Mod documentation

The Skill works without an Unciv source checkout. Use these public documentation pages for detailed formats and current supported behavior:

- [Introduction to Mods](https://yairm210.github.io/Unciv/Modders/Mods/) — Mod types, folder structure, GitHub topics, maps, and installation.
- [Making a new Civilization](https://yairm210.github.io/Unciv/Modders/Making-a-new-Civilization/) — a guided extension-Mod example.
- [Mod file structure and JSON reference](https://yairm210.github.io/Unciv/Modders/Mod-file-structure/1-Overview/) — JSON object files, fields, and base-ruleset notes.
- [Uniques](https://yairm210.github.io/Unciv/Modders/uniques/) — supported unique patterns and conditionals.
- [Images and Audio](https://yairm210.github.io/Unciv/Modders/Images-and-Audio/) — visual and audio assets.
- [Unciv documentation home](https://yairm210.github.io/Unciv/) — navigation to additional Modder guides, including maps, fonts, tilesets, and translations.
- The [Introduction to Mods](https://yairm210.github.io/Unciv/Modders/Mods/) page lists the repository topics used for Mod Manager categories.

The documentation tracks upstream and can describe features newer than a user's installed game. The Skill does not require a user-selected game version. When a request needs a release-specific compatibility claim, verify that claim against matching documentation or runtime evidence; otherwise mark it unverified. Do not replace this check by reading a local project source checkout.

The official Mod guide distinguishes extension rulesets, base rulesets, and ruleset-agnostic Mods. Data files can compose supported game objects and documented unique abilities, but they cannot introduce a new engine behavior. Flag that boundary when a proposed mechanic is not documented as supported.
