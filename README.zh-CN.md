# unciv-mod-creator

[English](README.md) | **简体中文**

一个与工具厂商无关的 Agent Skill，用于设计、创建、校验、打包、安装和测试数据驱动的 Unciv Mod。它把内置游戏参考、可重复运行的校验器、确定性打包和有边界的运行时证据整合到一个可复用工作流中。

## 这个 Skill 能做什么

| 能力 | 你会得到什么 |
|---|---|
| 设计受支持的玩法 | 把玩家需求转换成 Unciv 对象、字段、Unique 字符串、依赖关系和可观察的验收检查，并识别数据层近似方案和需要修改引擎的机制。 |
| 创建 Mod 起始结构 | 以不覆盖已有目录的方式生成文明扩展、单位/建筑扩展和纯地图 Mod 起始结构，同时生成设计任务表和按类型划分的检查清单。 |
| 按基础规则集校验 | 根据选定的基础规则集加载内置官方 Schema、已审核 Schema 例外、机制数据和完整基础规则快照；不支持的规则集会明确失败。 |
| 检查规则和翻译 | 检测 JSON 格式错误、重复键和名称、无效对象结构、可静态检测的无效跨文件引用、已登记 Unique 的参数或适用范围错误以及翻译占位符错误。 |
| 准备和校验图片 | 检查图片路径、大小写、PNG 文件头、常用图标尺寸、图集名称、图集页面、源文件新旧关系和打包区域；可使用经过哈希校验的依赖生成 LibGDX 图集。 |
| 生成统一预检报告 | 把规则、翻译、图片、图集和 ZIP 完整性检查汇总为 Markdown 或 JSON 报告，记录实际校验输入以及临时确定性包的 SHA-256。 |
| 打包和交付 Mod | 通过固定时间戳、排序、权限和元数据过滤生成可复现 ZIP；既可以只打包，也可以把新归档上传到 Unciv iOS 的 Receive Mod 接收器。 |
| 记录运行时验证 | 指导执行游戏内 Ruleset Validator、新游戏冒烟测试和功能专项检查；结果可以写入 `verification.json`，用 SHA-256 绑定报告、ZIP 和截图，再渲染为 Markdown。 |
| 查询内置百科数据 | 按类别、精确名称或文本搜索内置规则集快照；如果有对应翻译则返回简体中文，并显示该 JSON 类别的官方源码链接。 |
| 维护参考数据 | 审计官方 Schema、基础规则集、清单、校验和及已审核例外；仓库还提供自动测试和跨平台 CI。 |
| 自动化完整流程 | 提供统一的 `unciv_mod.py` 入口，覆盖起始结构、预检、打包、上传、参考数据审计、报告渲染和证据记录，同时保留各个单用途脚本。 |

## 支持范围

- **内置基础规则集：** `Civ V - Gods & Kings` 和 `Civ V - Vanilla`。
- **常见 Mod 类型：** 文明扩展、单位/建筑扩展、纯地图 Mod，以及遵循 Unciv 官方格式的手工数据或视觉 Mod。
- **输出内容：** Mod 目录、设计任务表、预检报告、打包图集、确定性 ZIP、上传结果和证据绑定的验证报告。
- **运行时测试：** Agent 工具能够控制 iOS Simulator 时可以自动执行；也可以由测试人员在真实设备上完成相同检查。

数据 Mod 可以组合 Unciv 已支持的对象和 Unique 效果，但不能增加新的引擎行为。静态校验不能证明实际玩法效果、平衡性或所有游戏 build 的兼容性。内置参考数据会保留来源版本元数据用于审计，但不要求用户选择游戏版本。

## 快速开始

### 1. 安装

在本仓库根目录执行：

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)" ~/.agents/skills/unciv-mod-creator
```

安装后重新加载所使用的 Agent 工具。

### 2. 提出完整任务

```text
$unciv-mod-creator 为 Civ V - Gods & Kings 创建一个拥有特色近战单位和文化建筑的文明 Mod，完成校验、打包并给出验证计划。
```

也可以检查已有 Mod：

```text
$unciv-mod-creator 审核 /absolute/path/to/My-Mod，修正确认的问题，并为 Civ V - Gods & Kings 生成严格预检报告。
```

### 3. 直接运行预检

```bash
python3 -m pip install -r requirements.txt
python3 scripts/unciv_mod.py check /absolute/path/to/My-Mod \
  --source-only \
  --output /absolute/path/to/My-Mod-preflight.json
```

只有当 Mod 引用了能区分某个内置规则集的对象时，命令才会自动识别基础规则集。如果多个规则集都能满足这些引用，命令会停止并列出有效的 `--base-ruleset` 选项，不会猜测。`check` 默认执行严格的基础引用校验。图片尚未打包时使用 `--source-only`；完成图集打包后，去掉该参数再次运行。

## 统一命令

```text
python3 scripts/unciv_mod.py {create,check,query,pack,upload,verify,audit,evidence} ...
```

- `create` 创建不覆盖已有目录的起始结构。
- `check` 选择或识别基础规则集，生成严格的 Markdown 或 JSON 预检报告。
- `query` 查询内置百科风格的数据，并输出匹配的本地记录和官方源码 URL。
- `pack` 生成确定性 ZIP；`upload` 生成 ZIP 并发送到 iOS 接收器。
- `verify` 校验产物哈希并渲染验证报告。
- `audit` 审计内置参考清单、Schema、基础规则和已审核例外。
- `evidence` 初始化记录、绑定哈希产物、记录运行检查并生成 Markdown 证据。

需要单独执行某个操作时，仍可直接使用原有单用途脚本。

## 安装方式

### 全局安装

全局安装后，可以在所有项目中发现这个 Skill。

链接已有仓库：

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/unciv-mod-creator ~/.agents/skills/unciv-mod-creator
```

或者直接克隆：

```bash
git clone <repository-url> ~/.agents/skills/unciv-mod-creator
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
git clone <repository-url> "$HOME\.agents\skills\unciv-mod-creator"
```

### 安装到单个项目

在目标项目根目录执行：

```bash
mkdir -p .agents/skills
ln -s /absolute/path/to/unciv-mod-creator .agents/skills/unciv-mod-creator
```

也可以把仓库直接克隆进项目：

```bash
git clone <repository-url> .agents/skills/unciv-mod-creator
```

支持 Agent Skills 格式的工具可以导入整个目录。其他工具可以把 [SKILL.md](SKILL.md) 作为工作流指令，并直接运行 Python 脚本。

## 常用工作流

### 创建起始结构

```bash
python3 scripts/unciv_mod.py create \
  --type civilization-extension \
  --mod-name "My-Civilization" \
  --brief "A civilization with a unique unit and building" \
  --base-ruleset "Civ V - Gods & Kings" \
  --output-dir ./output
```

支持的类型为 `civilization-extension`、`unit-building` 和 `map-only`。起始结构只是有组织的开始；在把它视为已实现玩法之前，应先完成其中的 `DESIGN.md`。

### 只校验规则

```bash
python3 scripts/unciv_mod.py check /absolute/path/to/My-Mod \
  --base-ruleset "Civ V - Gods & Kings"
```

JSON 报告提供稳定的诊断 `code`。问题还可以包含 `json_pointer`、`value` 和具体 `suggestion`，便于编辑器、CI 和其他工具进行确定性集成。

### 查询百科数据

内置快照覆盖游戏百科背后的规则 JSON，包括科技、单位、建筑、晋升、政策、
资源、地形、难度、胜利方式、单位名称等类别。查询可以离线执行，结果会带有
对应类别的官方源码链接：

```bash
python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --type Techs \
  --name Agriculture

python3 scripts/unciv_mod.py query \
  --base-ruleset "Civ V - Gods & Kings" \
  --type Units \
  --search "barbarian" \
  --language zh \
  --json
```

使用 `--list-types` 可以查看全部类别和源码链接。类别映射、查询方式以及内置规则
数据与仅源码的教程或界面页面之间的边界，见
[references/encyclopedia.md](references/encyclopedia.md)。结果中的参考版本只是来源
元数据，用户不需要选择游戏版本。

### 校验并打包图片

```bash
python3 scripts/validate_mod_assets.py /absolute/path/to/My-Mod --source-only
python3 scripts/pack_mod_images.py /absolute/path/to/My-Mod
python3 scripts/validate_mod_assets.py /absolute/path/to/My-Mod
```

图集打包需要 Java；本地没有缓存时，脚本可能从 Maven Central 下载经过 SHA-256 校验的 LibGDX 1.14.2 jar。

### 只打包，不上传

```bash
python3 scripts/unciv_mod.py pack /absolute/path/to/My-Mod \
  --output /absolute/path/to/My-Mod.zip
```

脚本不会覆盖已有 ZIP；归档必须位于 Mod 目录之外，超过接收器 256 MiB 限制的归档会被拒绝。

### 打包并上传到 Unciv iOS

在 Unciv 中打开 **Mods → Receive Mod**，然后运行：

```bash
python3 scripts/unciv_mod.py upload /absolute/path/to/My-Mod \
  --receiver-url http://192.168.x.x:port/ \
  --access-code 123456 \
  --output /absolute/path/to/My-Mod-upload.zip
```

接收器必须使用界面显示的 localhost 或私有网络 IPv4 地址。HTTP 200 只能证明传输成功，不能证明 Mod 可以加载或玩法正确。

### 记录并渲染运行时证据

```bash
python3 scripts/unciv_mod.py evidence init \
  --mod My-Mod \
  --base-ruleset "Civ V - Gods & Kings" \
  --preflight /absolute/path/to/My-Mod-preflight.json \
  --zip /absolute/path/to/My-Mod.zip \
  --output /absolute/path/to/verification.json

python3 scripts/unciv_mod.py evidence add-check /absolute/path/to/verification.json \
  --id ruleset-validator \
  --status passed \
  --observation "游戏内 Ruleset Validator 未报告问题。"

python3 scripts/unciv_mod.py evidence finalize /absolute/path/to/verification.json \
  --runtime-result PASS \
  --output /absolute/path/to/VERIFICATION.md
```

该流程不要求目标游戏版本。如有需要，测试人员可以把实际观察到的版本或 build 写入 `test_environment`。记录会区分通过、失败和未执行的检查，并验证每个绑定产物的 SHA-256。

### 审计 Skill 并运行测试

```bash
python3 scripts/unciv_mod.py audit
python3 -m unittest discover -s tests -v
```

[references/validation_coverage.json](references/validation_coverage.json) 以机器可读方式声明校验范围，包含官方 Schema、语义引用、附加检查、集成场景和运行时证据边界。

## 环境要求

- Python 3.10 或更高版本。
- 使用 `python3 -m pip install -r requirements.txt` 安装 Python 依赖。
- 只有打包图片图集时才需要 Java。
- 自动化游戏界面测试需要能够访问已安装 Unciv 的 iOS Simulator；也可以在真实设备上人工执行相同运行时检查。

## 示例和关键文件

- [SKILL.md](SKILL.md)：完整 Agent 工作流和证据规则。
- [references/knowledge-index.md](references/knowledge-index.md)：版本化参考资料和制作指南入口。
- [references/encyclopedia.md](references/encyclopedia.md)：百科类别映射、查询示例、源码链接以及数据/运行时边界。
- [references/versions/index.json](references/versions/index.json)：内置参考数据来源和基础规则集目录。
- [references/mechanics_registry.json](references/mechanics_registry.json)：已审核的 Unique 示例、模板、适用范围和测试证据。
- [scripts/unciv_mod.py](scripts/unciv_mod.py)：统一工作流命令。
- [scripts/check_mod.py](scripts/check_mod.py)：单用途的组合预检命令和库。
- [references/validation_coverage.json](references/validation_coverage.json)：机器可读的校验覆盖范围和边界。
- [examples/minimal-civilization-extension/](examples/minimal-civilization-extension/)：经过模拟器测试的最小文明示例。
- [examples/rich-civilization-extension/](examples/rich-civilization-extension/)：包含文明、单位和建筑的较完整静态示例。
- [examples/tested-feature-recipes/](examples/tested-feature-recipes/)：包含通过、失败和未执行检查的证据绑定模拟器示例。
- [examples/survivor-camp-mvp/](examples/survivor-camp-mvp/)：双语、可安装的回合制生存示例，包含机制矩阵和部分模拟器证据。
