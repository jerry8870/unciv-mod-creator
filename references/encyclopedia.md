# Civilopedia data and source map

This skill includes an offline, queryable snapshot of the JSON data used by the
game's Civilopedia-style screens. The snapshot is selected by base ruleset:

- [Gods & Kings snapshot](snapshots/gk-baseline/)
- [Vanilla snapshot](snapshots/vanilla-baseline/)

The files are generated from the upstream ruleset JSON files and the Simplified
Chinese translation file. Each snapshot's `manifest.json` records the source
commit, checksums, and direct raw-source URLs. The source URLs are links to the
upstream database files, so a user can inspect the original data or compare a
newer game build without treating the bundled snapshot as live game state.
The corresponding upstream JSON tree is also available at
[Unciv's `android/assets/jsons` directory](https://github.com/yairm210/Unciv/tree/4.22.0/android/assets/jsons).

## Query from the command line

List every available data category and its direct source link:

```bash
python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --list-types
```

Look up an exact entry:

```bash
python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --type Techs \
  --name Agriculture
```

Search across one category or the whole snapshot:

```bash
python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --type UnitPromotions \
  --search "cover"

python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --search "barbarian" \
  --language zh \
  --json
```

`--name` is an exact, case-insensitive name lookup and requires `--type`.
`--search` is a case-insensitive substring search through an entry's nested
values. `--language zh` adds a Simplified Chinese translation when the
translation snapshot contains one. `--json` is intended for scripts and other
tools; human-readable output includes the local snapshot and direct source URL.

The command does not require a user-selected game version. The reference
version printed in the result is provenance metadata for reproducibility.

## Category map

The category names below are the JSON keys accepted by `--type`. Aliases such
as `technology`, `units`, `promotions`, `tutorials`, and `victory types` are
also accepted.

| Civilopedia or game concept | Bundled JSON type | Typical entries |
|---|---|---|
| Civilizations / nations | `Nations` | Leaders, unique abilities, cities, diplomacy text |
| Technologies | `Techs` | Technology tree nodes, prerequisites, quotes |
| Units | `Units` | Cost, movement, combat values, required technology |
| Unit types | `UnitTypes` | Melee, ranged, scout, civilian and other classes |
| Promotions | `UnitPromotions` | Promotion names, prerequisites, Unique effects |
| Buildings and wonders | `Buildings` | Production cost, yields, maintenance, effects |
| Policies | `Policies` | Policy branches and nested policy entries |
| Religions and beliefs | `Religions`, `Beliefs` | Religion names and belief effects |
| Game difficulty | `Difficulties` | Happiness, cost modifiers, barbarian timing |
| Victory methods | `VictoryTypes` | Victory milestones and victory text |
| Unit names | `UnitNameGroups` | Names grouped by great person or unit role |
| Resources | `TileResources` | Strategic, luxury, and bonus resources |
| Tile improvements | `TileImprovements` | Improvement yields, requirements, and effects |
| Terrain | `Terrains` | Terrain movement, yields, and restrictions |
| Eras and game speed | `Eras`, `Speeds` | Era progression and speed modifiers |
| City states and quests | `CityStateTypes`, `Quests` | City-state behavior and quest definitions |
| Ruins and events | `Ruins`, `Events` | Ancient ruins rewards and event/tutorial tasks |
| Specialists and global rules | `Specialists`, `GlobalUniques`, `ModOptions` | Specialist yields and global rule values |

The built-in encyclopedia also contains presentation pages, tutorial images,
contact/help text, and other UI content. Those pages are not all standalone
ruleset JSON records. When a page is absent from the bundled categories, use the
official source tree linked by the snapshot manifest and mark the answer as
source-only; do not infer that a missing page is unsupported by the game.

## Data and runtime boundaries

The query command answers questions about the selected ruleset's bundled data
and its upstream source files. It does not inspect a live save, active Mod,
current difficulty overrides, or a running game. Use `unciv_mod.py check` for a
Mod's static references and the in-game Ruleset Validator and gameplay test for
engine behavior. A value found in this reference database is evidence of the
data definition, not proof that every Unique or UI interaction works in every
game build.

## 中文说明

本 Skill 已内置可离线查询的规则集快照，并保留每个 JSON 文件的官方源码链接。
使用 `--list-types` 查看百科类别，使用 `--type` 和 `--name` 查询精确条目，使用
`--search` 搜索文本，使用 `--language zh` 显示简体中文翻译。结果中的本地快照、
源码 URL 和参考版本用于复现和审计，不代表当前运行中的存档状态。

截图中的教程、帮助和界面展示页面不一定对应独立规则 JSON。若本地类别没有该页面，
应沿着清单中的官方源码链接查找，并把结果标记为“仅源码依据”；不要把“本地没有
独立条目”解释成“游戏不支持”。
