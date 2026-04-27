# PyEnv Doctor

Python 环境诊断与沙箱预演工具

[![PyPI version](https://badge.fury.io/py/pyenv-doctor-tool.svg)](https://pypi.org/project/pyenv-doctor-tool/)
[![GitHub stars](https://img.shields.io/github/stars/GH-tll/pyenv-doctor)](https://github.com/GH-tll/pyenv-doctor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 简介

PyEnv Doctor 是一个智能的 Python 环境诊断与自动修复工具。它通过构建依赖图谱、在沙箱中预演修复方案，确保修复建议的安全性。v0.1.5 版本实现了**完整的依赖冲突自动修复功能**，包括智能诊断、沙箱预演、自动修复和报告导出。

**核心价值：** 沙箱预演，安全修复，智能诊断。

### 解决什么问题？

- 依赖冲突地狱：`pip install` 导致现有包版本不兼容，项目无法运行
- 黑盒修复风险：通用 AI 助手给出的修复命令缺乏全局考量，执行后可能导致更严重的损坏
- 试错成本高昂：环境一旦损坏，重建虚拟环境、重新安装依赖耗时极长
- 修复后无法回滚：执行修复命令后发现问题更严重，但无法快速恢复到修复前状态

### 核心特性

#### v0.1.5 核心功能

- 智能诊断：自动扫描环境，检测依赖冲突
- 沙箱预演：在隔离环境中验证修复方案，确保安全
- 自动修复：`diagnose --fix` 自动执行修复，智能生成修复建议
- 多格式报告：支持 JSON 和 Markdown 格式诊断报告
- 文件检查：支持检查 requirements.txt 和 pyproject.toml 文件

#### 技术优势

- 沙箱隔离：所有修复建议都在沙箱中验证，确保不会影响当前环境
- 智能解析：正确解析复杂的版本约束（如 `<4,>=3.6.0`）
- 并行优化：多线程并行预演，提升诊断速度
- 用户友好：清晰的诊断报告和修复建议

---

## 快速开始

### 安装

#### 从正式 PyPI 安装（推荐）

当前稳定版本 `0.1.5` 已发布到正式 PyPI，包含完整的依赖冲突自动修复功能。

```bash
# 1. 卸载旧版本（如果已安装）
pip uninstall pyenv-doctor-tool -y

# 2. 从正式 PyPI 安装
pip install pyenv-doctor-tool

# 3. 验证安装
pyenv-doctor --version
```

#### 从 TestPyPI 安装（测试版）

如果需要测试最新功能，可以从 TestPyPI 安装：

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyenv-doctor-tool==1.1.8
```

---

## 新手入门（第一次使用必读）

### 第一步：安装工具

```bash
# 1. 确保 Python 版本 >= 3.8
python --version

# 2. 安装工具（从 TestPyPI 安装最新版）
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyenv-doctor-tool==1.1.3

# 3. 验证安装
pyenv-doctor --version
```

### 第二步：创建虚拟环境（强烈建议）

**为什么需要虚拟环境？**
- 隔离项目依赖，避免不同项目之间相互影响
- 防止全局环境被污染
- 便于项目迁移和部署

```bash
# Windows (CMD)
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# 激活后，命令行前面会出现 (venv) 标识
```

### 第三步：诊断当前环境

```bash
# 使用快速模式诊断（推荐）
pyenv-doctor diagnose --fast

# 如果有冲突，会自动显示修复建议
```

### 第四步：根据建议修复

**方式一：自动修复（推荐新手）**
```bash
# 使用默认策略自动修复
pyenv-doctor diagnose --fix

# 修复成功后会询问是否保留状态
```

**方式二：手动执行修复命令**
```bash
# 根据诊断结果中的建议，手动执行 pip install
pip install numpy==1.23.5 pandas==1.5.3
```

### 第五步：创建快照（可选但建议）

```bash
# 环境正常后，创建快照备份
pyenv-doctor snapshot create --label "healthy-state"

# 后续如果环境出问题，可以快速回滚
pyenv-doctor snapshot rollback --latest
```

### 常用命令速查

| 目的 | 命令 |
|:---|:---|
| 诊断环境 | `pyenv-doctor diagnose --fast` |
| 自动修复 | `pyenv-doctor diagnose --fix` |
| 创建快照 | `pyenv-doctor snapshot create` |
| 回滚环境 | `pyenv-doctor snapshot rollback --latest` |
| 查看帮助 | `pyenv-doctor --help` |

---

## 基本用法

诊断当前环境：

```bash
pyenv-doctor diagnose
```

诊断并自动修复：

```bash
# 使用平衡策略自动修复（默认）
pyenv-doctor diagnose --fix

# 使用保守策略自动修复
pyenv-doctor diagnose --fix --strategy conservative

# 预演修复但不实际执行
pyenv-doctor diagnose --fix --dry-run
```

检查依赖文件：

```bash
pyenv-doctor check-file requirements.txt
pyenv-doctor check-file pyproject.toml
```

创建环境快照：

```bash
# 创建永久快照
pyenv-doctor snapshot create --label "before-upgrade"

# 创建临时快照（自动修复时使用）
pyenv-doctor snapshot create --temporary
```

查看快照列表：

```bash
pyenv-doctor snapshot list
```

回滚到快照：

```bash
# 回滚到最新快照
pyenv-doctor snapshot rollback --latest

# 回滚到指定快照
pyenv-doctor snapshot rollback <SNAPSHOT_ID>
```

---

## 完整用法

### 0. 环境准备（对小白友好）

#### 步骤 1：创建并激活虚拟环境

```bash
# 创建虚拟环境（Windows CMD）
python -m venv venv
venv\Scripts\activate.bat

# 创建虚拟环境（Windows PowerShell）
python -m venv venv
.\venv\Scripts\Activate.ps1

# 创建虚拟环境（Linux/macOS）
python3 -m venv venv
source venv/bin/activate
```

#### 步骤 2：卸载旧版本（如果已安装）

```bash
pip uninstall pyenv-doctor-tool -y
```

#### 步骤 3：安装指定版本

**安装测试环境版本（最新功能）：**

```bash
# 安装 TestPyPI 上的 1.1.3 版本
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyenv-doctor-tool==1.1.3
```

**安装正式环境版本（稳定版）：**

```bash
# 安装 PyPI 上的稳定版本
pip install pyenv-doctor-tool
```

#### 步骤 4：查看版本号

```bash
pyenv-doctor --version
# 预期输出：pyenv-doctor-tool, version 1.1.3
```

#### 步骤 5：更新到最新版本

**更新到 TestPyPI 最新版本：**

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --upgrade pyenv-doctor-tool
```

**更新到 PyPI 最新版本：**

```bash
pip install --upgrade pyenv-doctor-tool
```

### 1. 环境诊断 (`diagnose`)

诊断当前 Python 环境的依赖冲突：

```bash
# 基本诊断
pyenv-doctor diagnose

# 快速模式（仅扫描当前环境，排除基础包，推荐）
pyenv-doctor diagnose --fast

# 自定义超时时间（秒）
pyenv-doctor diagnose --timeout 30

# 启用详细输出
pyenv-doctor diagnose --verbose

# 导出诊断报告
pyenv-doctor diagnose --output report.json
pyenv-doctor diagnose --output report.md

# 启用并行预演（默认开启）
pyenv-doctor diagnose --parallel

# 自定义并行工作线程数
pyenv-doctor diagnose --workers 5
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `--fast` | - | 快速模式（排除基础包，仅扫描当前环境） | False |
| `--timeout` | `-t` | 沙箱预演超时时间（秒） | 60 |
| `--verbose` | `-v` | 显示详细输出 | False |
| `--output` | `-o` | 导出报告文件路径 | None |
| `--parallel` | - | 启用并行预演 | True |
| `--workers` | `-w` | 并行工作线程数 | 3 |
| `--fix` | - | 启用自动修复 | False |
| `--strategy` | - | 修复策略（conservative/balanced/aggressive） | balanced |
| `--dry-run` | - | 预演模式，只显示不执行 | False |
| `--yes` | `-y` | 跳过确认 | False |

#### 快速模式 (`--fast`)

快速模式是推荐的诊断方式，特别适合以下场景：

- **包数量过多**：全局环境有几百个包时，快速模式可以大幅减少扫描数量
- **未激活虚拟环境**：诊断全局环境时，快速模式排除基础包（pip、setuptools、wheel）
- **提升速度**：扫描速度显著提升，减少等待时间

**快速模式行为：**
- 排除基础包：pip、setuptools、wheel、pkg_resources
- 仅扫描当前 Python 环境的包（site-packages）
- 跳过外部环境的包

**使用示例：**

```bash
# 推荐：使用快速模式诊断
pyenv-doctor diagnose --fast

# 快速模式 + 自动修复
pyenv-doctor diagnose --fix --fast

# 快速模式 + 详细输出（查看跳过的包）
pyenv-doctor diagnose --fast --verbose
```

**虚拟环境 vs 全局环境：**

```bash
# 场景 1：已激活虚拟环境
(venv) $ pyenv-doctor diagnose
# → 扫描虚拟环境中的包（通常 20-50 个）

# 场景 2：未激活虚拟环境（全局环境）
$ pyenv-doctor diagnose
# → 扫描全局环境（可能几百个包）

# 场景 3：未激活虚拟环境 + 快速模式（推荐）
$ pyenv-doctor diagnose --fast
# → 仅扫描当前环境，排除基础包（约几十到百个包）
```

#### 自动修复模式

`diagnose --fix` 命令会自动执行修复流程：

1. 创建临时快照：自动创建临时快照，记录修复前状态
2. 执行修复：根据指定策略执行修复
3. 用户确认：修复成功后询问是否保留状态
4. 快照管理：可选择转为永久快照或回滚

**修复策略说明：**

| 策略 | 说明 | 适用场景 |
|:---|:---|:---|
| `conservative` | 保守策略 - 只降级，避免升级风险 | 生产环境，稳定性优先 |
| `balanced` | 平衡策略 - 最小改动，按需升降级 | 开发环境，推荐默认 |
| `aggressive` | 激进策略 - 升到最新，获取最新功能 | 测试环境，追求最新 |

**使用示例：**

```bash
# 使用平衡策略自动修复（推荐）
pyenv-doctor diagnose --fix --strategy balanced

# 使用保守策略，跳过确认
pyenv-doctor diagnose --fix --strategy conservative --yes

# 预演修复但不实际执行
pyenv-doctor diagnose --fix --dry-run --verbose
```

**自动修复流程示例：**

```bash
$ pyenv-doctor diagnose --fix

[SCAN] 扫描环境...
[OK] 发现 280 个包
[DIAGNOSE] 检测冲突...
[WARN] 发现 2 个冲突...
[SANDBOX] 并行模拟修复（3 个工作线程）...
[RESULT] 修复建议:
...

============================================================
[AUTO-FIX] 自动修复模式启动
============================================================
[INFO] 修复策略：平衡策略 - 最小改动，按需升降级
[INFO] 预演模式：否

[SNAPSHOT] 创建临时快照...
[OK] 快照 ID: 20260424_143022_abc123 (临时)

[AUTO-FIX] 开始执行修复...
[INSTALL] 正在安装 numpy==1.23.5...
[INSTALL] 正在安装 pandas==1.5.3...
[OK] 修复成功！

  - 修复包数量：2
  - 耗时：15.3 秒
  - 验证：通过

[KEEP] 是否保留当前状态？[Y/n] Y
[OK] 临时快照已转为永久快照
  快照 ID: 20260424_143022_abc123
```

### 2. 文件检查 (`check-file`)

检查依赖文件中的潜在冲突，无需激活环境即可分析项目依赖。

**使用场景：**
- 项目迁移前：检查目标项目的依赖是否与当前环境兼容
- 代码审查时：快速检查新添加的依赖是否有冲突
- 多项目管理：批量检查多个项目的依赖健康度
- CI/CD 集成：在自动化流程中加入依赖检查

```bash
# 基本用法
pyenv-doctor check-file requirements.txt
pyenv-doctor check-file pyproject.toml

# 导出依赖列表为 JSON
pyenv-doctor check-file requirements.txt --output deps.json

# 手动指定文件格式（当文件后缀不明确时）
pyenv-doctor check-file my-deps.txt --format requirements
pyenv-doctor check-file config.toml --format pyproject

# 检查其他项目的依赖文件
pyenv-doctor check-file ../project-b/requirements.txt
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `file` | - | 文件路径（必需） | - |
| `--output` | `-o` | 导出报告文件路径 | None |
| `--format` | `-f` | 文件格式（auto/requirements/pyproject） | auto |

**输出示例：**

```bash
$ pyenv-doctor check-file requirements.txt

[INFO] 解析文件：requirements.txt
[OK] 解析到 15 个依赖

检测到的依赖:
  - requests>=2.28.0
  - numpy>=1.21.0
  - pandas>=1.3.0
  - flask>=2.0.0
  ...

# 导出 JSON 时
[OK] 依赖列表已导出：deps.json
```

**支持的文件格式：**
- **requirements.txt**: Python 标准依赖文件格式
- **pyproject.toml**: 现代 Python 项目配置文件（PEP 621）

**注意事项：**
- 文件必须存在，否则报错
- 自动检测文件格式（基于文件名），也可手动指定
- 仅解析依赖列表，不执行安装或验证

### 3. 快照管理 (`snapshot`)

管理环境快照，支持创建、列表、回滚、删除、导出等操作。

#### 3.1 创建快照

```bash
# 创建永久快照
pyenv-doctor snapshot create

# 创建带标签的快照
pyenv-doctor snapshot create --label "before-upgrade"

# 创建临时快照（自动修复成功后可转为永久）
pyenv-doctor snapshot create --temporary
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `--label` | `-l` | 快照标签 | None |
| `--temporary` | - | 创建临时快照 | False |

**输出示例：**

```bash
$ pyenv-doctor snapshot create --label "before-upgrade"

[SNAPSHOT] 正在创建快照...
[OK] 快照创建成功！
  - ID: 20260424_143022_abc123
  - 时间：2026-04-24 14:30:22
  - 标签：before-upgrade
  - Python 版本：3.11.5
  - 虚拟环境：/path/to/venv
  - 包数量：280

回滚命令：
  pyenv-doctor snapshot rollback 20260424_143022_abc123
```

#### 3.2 查看快照列表

```bash
# 列出所有快照
pyenv-doctor snapshot list

# 限制显示数量
pyenv-doctor snapshot list --limit 5

# JSON 格式输出
pyenv-doctor snapshot list --json
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `--json` | - | JSON 格式输出 | False |
| `--limit` | `-n` | 限制显示数量 | None |

**输出示例：**

```bash
$ pyenv-doctor snapshot list

ID                       Time                Label                Packages   Temp
─────────────────────────────────────────────────────────────────────────────────
20260424_143022_abc123   2026-04-24 14:30:22 before-upgrade       280        No
20260424_120000_def456   2026-04-24 12:00:00 -                    275        No
20260423_180000_ghi789   2026-04-23 18:00:00 auto-fix             270        Yes

共 3 个快照
```

#### 3.3 回滚快照

```bash
# 回滚到最新快照
pyenv-doctor snapshot rollback --latest

# 回滚到指定快照
pyenv-doctor snapshot rollback 20260424_143022_abc123

# 预演回滚（不实际执行）
pyenv-doctor snapshot rollback --latest --dry-run

# 跳过确认回滚
pyenv-doctor snapshot rollback --latest --yes

# 禁用回滚后验证
pyenv-doctor snapshot rollback --latest --no-verify
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `snapshot_id` | - | 快照 ID（与 --latest 二选一） | None |
| `--latest` | - | 回滚到最新快照 | False |
| `--dry-run` | - | 预览不回滚 | False |
| `--yes` | `-y` | 跳过确认 | False |
| `--verify` | - | 回滚后验证（默认开启） | True |

**回滚流程示例：**

```bash
$ pyenv-doctor snapshot rollback --latest

[INFO] 使用最新快照：20260424_143022_abc123
[ROLLBACK] 回滚预览:
============================================================
将恢复 2 个包
  - numpy: 1.24.0 → 1.23.5
  - pandas: 1.5.3 → 1.5.0

[CONFIRM] 是否继续回滚？[y/N] y

[ROLLBACK] 正在回滚到 20260424_143022_abc123...
[ROLLBACK] 进度 [██████████████████████████░░░░] 80.0% (2/3) numpy
[OK] 回滚成功！
  - 恢复包数量：2
  - 耗时：8.5 秒
  - 验证：通过

环境已恢复到：
  2026-04-24 14:30:22
```

#### 3.4 删除快照

```bash
# 删除单个快照
pyenv-doctor snapshot delete 20260424_143022_abc123

# 删除多个快照
pyenv-doctor snapshot delete id1 id2 id3

# 跳过确认删除
pyenv-doctor snapshot delete id1 --yes
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `snapshot_ids` | - | 一个或多个快照 ID（必需） | - |
| `--yes` | `-y` | 跳过确认 | False |

#### 3.5 导出快照

```bash
# 导出为 requirements.txt
pyenv-doctor snapshot export 20260424_143022_abc123

# 导出为 JSON
pyenv-doctor snapshot export 20260424_143022_abc123 --format json

# 自定义输出文件
pyenv-doctor snapshot export 20260424_143022_abc123 --output my-deps.txt
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `snapshot_id` | - | 快照 ID（必需） | - |
| `--output` | `-o` | 输出文件路径 | requirements.txt |
| `--format` | `-f` | 导出格式（requirements/json） | requirements |

#### 3.6 清理快照

```bash
# 清理所有快照
pyenv-doctor snapshot cleanup

# 仅清理临时快照
pyenv-doctor snapshot cleanup --temporary

# 跳过确认清理
pyenv-doctor snapshot cleanup --yes
```

**参数说明：**

| 参数 | 简写 | 说明 | 默认值 |
|:---|:---|:---|:---:|
| `--temporary` | - | 仅清理临时快照 | False |
| `--yes` | `-y` | 跳过确认 | False |

---

## 输出示例

### 无冲突环境

```
$ pyenv-doctor diagnose
[SCAN] 扫描环境...
[OK] 发现 10 个包
[DIAGNOSE] 检测冲突...
[OK] 未发现冲突
```

### 有冲突环境

```
$ pyenv-doctor diagnose
[SCAN] 扫描环境...
[OK] 发现 280 个包
[DIAGNOSE] 检测冲突...
[WARN] 发现 2 个冲突:
  - pandas 要求 numpy<1.24，但已安装 1.24.0
  - scipy 要求 numpy<1.23，但已安装 1.24.0
[SANDBOX] 并行模拟修复（3 个工作线程）...
[RESULT] 修复建议:

【方案一】推荐方案 [已验证] ★★★★★
============================================================
说明：此方案中每个版本都已在沙箱中单独验证可行
推荐度：强烈推荐（优先使用）

  1. pip install numpy==1.23.5
  2. pip install pandas==1.5.3

一键执行：
  pip install numpy==1.23.5 pandas==1.5.3

【方案二】保守方案 [部分验证] ★★★☆☆
============================================================
说明：此方案中每个版本已单独验证，但组合使用未经过测试
推荐度：保守选择（适合不想大幅变动的环境）

  1. pip install numpy==1.22.0
  2. pip install pandas==1.5.0

一键执行：
  pip install numpy==1.22.0 pandas==1.5.0

============================================================
[重要说明]
  - 方案一：每个版本已单独验证，强烈推荐优先使用
  - 方案二：每个版本已单独验证，但组合效果未经测试
  - 所有验证均在沙箱隔离环境中进行，确保安全性
============================================================
```

### 导出 Markdown 报告

```bash
$ pyenv-doctor diagnose --output diagnosis.md
```

生成的 Markdown 报告示例：

```markdown
# PyEnv Doctor 诊断报告

**生成时间**: 2026-04-24 18:00:00
**工具版本**: v1.1.3

---

## 概要统计

- **总包数**: 280
- **冲突数**: 2
- **成功验证**: 2 个方案
- **验证失败**: 0 个方案
- **健康分数**: 99.3/100

✅ **环境状态**: 优秀

---

## 检测到的冲突

### 冲突 1

- **包名**: `pandas`
- **依赖要求**: `numpy<1.24`
- **已安装版本**: `1.24.0`
- **修复建议**: `numpy==1.23.5`

...

## 修复建议

### 推荐方案（已验证）

以下方案已在沙箱环境中验证可行：

1. `pip install numpy==1.23.5`
2. `pip install pandas==1.5.3`

**一键执行命令**:
```bash
pip install numpy==1.23.5 pandas==1.5.3
```
```

---

## 技术架构

```
PyEnv Doctor
├── CLI (Click)
│   ├── diagnose: 环境诊断命令
│   ├── check-file: 文件检查命令
│   └── snapshot: 快照管理命令组
├── Agent Layer
│   ├── EnvScanner: 环境扫描 Agent
│   ├── ConflictSolver: 冲突检测 Agent
│   └── SandboxExecutor: 沙箱预演 Agent（支持并行）
├── Exporters
│   ├── JSONExporter: JSON 报告导出
│   └── MarkdownExporter: Markdown 报告导出
├── Parsers
│   ├── RequirementsParser: requirements.txt 解析
│   └── PyProjectParser: pyproject.toml 解析
└── Tool Layer
    ├── pip_tool: 封装 pip 命令
    └── venv_tool: 封装 venv 操作
```

### 核心工作流程

```
pyenv-doctor diagnose
    ↓
启动检测（Python 版本、虚拟环境）
    ↓
EnvScanner 扫描环境（获取已安装包）
    ↓
ConflictSolver 检测冲突（构建依赖图）
    ↓
SandboxExecutor 沙箱预演（并行/串行）
    ↓
输出诊断报告 + 修复建议
    ↓
[可选] 导出 JSON/Markdown 报告
```

---

## 开发

### 环境准备

```bash
# 克隆仓库
git clone https://github.com/GH-tll/pyenv-doctor.git
cd pyenv-doctor

# 创建虚拟环境（Windows CMD）
python -m venv venv
venv\Scripts\activate.bat

# 创建虚拟环境（Windows PowerShell）
python -m venv venv
.\venv\Scripts\Activate.ps1

# 创建虚拟环境（Linux/macOS）
python3 -m venv venv
source venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行性能基准测试
pytest tests/test_benchmarks.py -v -s

# 生成覆盖率报告
pytest tests/ --cov=pyenv_doctor --cov-report=html
```

### 代码规范

```bash
# 代码格式化
ruff format src/ tests/

# 代码检查
ruff check src/ tests/
```

---

## 性能基准

### 扫描性能

| 包数量 | 目标耗时 | 实际耗时 | 状态 |
|:---:|:---:|:---:|:---:|
| 10 | < 1 秒 | ~0.1 秒 | ✅ |
| 100 | < 3 秒 | ~0.5 秒 | ✅ |
| 500 | < 10 秒 | ~2 秒 | ✅ |

### 冲突检测性能

| 包数量 | 目标耗时 | 实际耗时 | 状态 |
|:---:|:---:|:---:|:---:|
| 10 | < 0.5 秒 | ~0.05 秒 | ✅ |
| 100 | < 2 秒 | ~0.3 秒 | ✅ |
| 500 | < 10 秒 | ~1.5 秒 | ✅ |

### 沙箱预演性能

| 模式 | 冲突数 | 目标耗时 | 优化效果 |
|:---|:---:|:---:|:---:|
| 串行 | 1 | < 60 秒 | 基准 |
| 串行 | 5 | < 300 秒 | 基准 |
| 并行 (3 workers) | 5 | < 120 秒 | ⚡ 提升 60% |

---

## 使用场景

### 场景 1：项目迁移前检查

在将项目迁移到新环境前，检查依赖兼容性：

```bash
# 检查当前环境
pyenv-doctor diagnose --output current-env.json

# 检查目标项目的依赖文件
pyenv-doctor check-file requirements.txt --output target-deps.json
```

### 场景 2：CI/CD 集成

在 CI/CD 流程中加入环境检查：

```yaml
# .github/workflows/ci.yml
- name: Check environment health
  run: |
    pip install pyenv-doctor-tool
    pyenv-doctor diagnose --output report.json
    # 检查健康分数，低于 80 分则警告
```

### 场景 3：多项目管理

为多个项目生成依赖报告：

```bash
# 批量检查多个项目
for project in project-a project-b project-c; do
  cd $project
  pyenv-doctor check-file requirements.txt --output ../reports/$project.json
done
```

---

## 常见问题

### Q: 沙箱预演会不会影响我的当前环境？

**A:** 不会。沙箱预演在临时创建的虚拟环境中进行，预演完成后会自动清理，不会影响当前环境。

### Q: 并行预演比串行快多少？

**A:** 取决于冲突数量和网络速度。一般来说，5 个冲突并行预演（3 workers）比串行快 60% 左右。

### Q: 为什么有些修复方案验证失败？

**A:** 可能的原因：
- 包版本不存在（如 999.999.999）
- 包已废弃或下架
- 网络连接问题
- 系统依赖缺失（如 C 扩展编译失败）

### Q: 如何解读健康分数？

**A:** 健康分数计算公式：`100 * (1 - 冲突数/总包数)`
- 90-100: 优秀 ✅
- 70-89: 良好 ⚠️
- 50-69: 一般 ⚠️
- 0-49: 较差 ❌

### Q: 支持哪些 Python 版本？

**A:** Python 3.8+，包括 3.8、3.9、3.10、3.11、3.12。

### Q: 支持哪些操作系统？

**A:** Windows、Linux、macOS 全平台支持。

---

## 故障排查

### 问题 1：命令找不到 `pyenv-doctor`

**症状：**
```bash
'pyenv-doctor' 不是内部或外部命令
# 或
command not found: pyenv-doctor
```

**解决方案：**
1. **检查是否已安装**
   ```bash
   pip show pyenv-doctor-tool
   ```
   如果未安装，执行：
   ```bash
   pip install pyenv-doctor-tool
   ```

2. **检查 PATH 环境变量**
   - Windows: 确保 `C:\Users\<用户名>\AppData\Roaming\Python\Python3x\Scripts` 在 PATH 中
   - Linux/macOS: 确保 `~/.local/bin` 在 PATH 中
   
3. **使用完整路径运行**
   ```bash
   # Windows
   C:\Python39\Scripts\pyenv-doctor.exe
   
   # Linux/macOS
   ~/.local/bin/pyenv-doctor
   ```

### 问题 1.5：多个安装路径冲突

**症状：**
```bash
# Windows 下运行 where.exe pyenv-doctor 显示多个路径
D:\tll\AI_Projects\pyenv-doctor\test-conflict-env\Scripts\pyenv-doctor.exe
D:\tll\Python3.11\Scripts\pyenv-doctor.exe
```

**原因：**
- 全局环境安装了一个版本
- 虚拟环境又安装了一个版本
- 可能存在开发版本（`pip install -e .`）和发布版本同时存在

**解决方案：**
1. **确认当前使用的版本**
   ```bash
   # 查看当前激活的是哪个版本
   where.exe pyenv-doctor  # Windows
   which pyenv-doctor      # Linux/macOS
   
   # 查看版本号
   pyenv-doctor --version
   ```

2. **使用虚拟环境中的版本（推荐）**
   ```bash
   # 确保虚拟环境已激活
   # 命令行前面应该有 (venv) 或环境名标识
   
   # 如果未激活，重新激活（替换 venv 为你的环境名）
   # Windows CMD
   venv\Scripts\activate.bat
   
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **卸载不需要的版本**
   
   **场景 A：只想保留虚拟环境版本**
   ```bash
   # 停用虚拟环境（这样 pip 操作的就是全局环境）
   deactivate
   
   # 卸载全局环境的版本
   pip uninstall pyenv-doctor-tool -y
   
   # 重新激活虚拟环境（替换 venv 为你的环境名）
   # Windows CMD
   venv\Scripts\activate.bat
   
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv/bin/activate
   ```
   
   **场景 B：只想保留全局版本**
   ```bash
   # 确保在虚拟环境中
   # 卸载虚拟环境的版本
   pip uninstall pyenv-doctor-tool -y
   
   # 停用虚拟环境后，使用的就是全局版本
   deactivate
   ```

4. **开发版本 vs 发布版本**
   ```bash
   # 如果同时安装了开发版本和发布版本
   # 查看安装位置
   pip show pyenv-doctor-tool
   
   # 如果 Location 指向项目目录（如 D:\tll\AI_Projects\pyenv-doctor）
   # 说明是开发版本（pip install -e .）
   
   # 如果想切换到发布版本
   pip uninstall pyenv-doctor-tool -y
   pip install pyenv-doctor-tool
   ```

5. **清理所有版本重新安装**
   ```bash
   # 步骤 1：在虚拟环境中卸载虚拟环境版本
   pip uninstall pyenv-doctor-tool -y
   
   # 步骤 2：停用虚拟环境
   deactivate
   
   # 步骤 3：卸载全局环境版本
   pip uninstall pyenv-doctor-tool -y
   
   # 步骤 4：重新激活虚拟环境（替换 venv 为你的环境名）
   # Windows CMD
   venv\Scripts\activate.bat
   
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv/bin/activate
   
   # 步骤 5：重新安装（从 TestPyPI）
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyenv-doctor-tool==1.1.3
   ```

**最佳实践：**
- 始终在虚拟环境中使用和安装工具
- 避免在全局环境和虚拟环境同时安装
- 开发时使用 `pip install -e .`，测试时使用 `pip install pyenv-doctor-tool`


### 问题 2：权限错误

**症状：**
```bash
[ERROR] 权限不足，无法扫描环境
PermissionError: [Errno 13] Permission denied
```

**解决方案：**
1. **使用管理员/超级用户权限**
   - Windows: 右键点击命令行 → "以管理员身份运行"
   - Linux/macOS: 在命令前加 `sudo`
   
2. **在虚拟环境中运行（推荐）**
   ```bash
   # Windows CMD
   python -m venv venv
   venv\Scripts\activate.bat
   
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   
   pip install pyenv-doctor-tool
   pyenv-doctor diagnose
   ```

### 问题 3：扫描时间过长

**症状：**
诊断命令运行超过 5 分钟仍未完成

**解决方案：**
1. **使用快速模式（强烈推荐）**
   ```bash
   pyenv-doctor diagnose --fast
   ```
   可排除基础包，大幅减少扫描数量

2. **在虚拟环境中运行**
   虚拟环境通常只有几十个包，而全局环境可能有几百个

3. **减少超时时间**
   ```bash
   pyenv-doctor diagnose --timeout 30
   ```

### 问题 4：虚拟环境检测失败

**症状：**
```bash
[WARN] 建议在虚拟环境中运行
```
但实际已经在虚拟环境中

**解决方案：**
1. **确认虚拟环境已正确激活**
   ```bash
   # Windows
   echo %VIRTUAL_ENV%
   
   # Linux/macOS
   echo $VIRTUAL_ENV
   ```
   应该输出虚拟环境路径

2. **重新激活虚拟环境**
   ```bash
   deactivate
   
   # Windows CMD
   venv\Scripts\activate.bat
   
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **在虚拟环境中重新安装工具**
   ```bash
   pip uninstall pyenv-doctor-tool -y
   pip install pyenv-doctor-tool
   ```

### 问题 5：沙箱预演超时

**症状：**
```bash
[WARN] 沙箱预演超时：60 秒
```

**解决方案：**
1. **增加超时时间**
   ```bash
   pyenv-doctor diagnose --timeout 120
   ```

2. **检查网络连接**
   沙箱预演需要下载包，网络慢会导致超时

3. **使用国内镜像源**
   ```bash
   # 在沙箱环境中使用国内镜像
   # 工具会自动检测并使用配置的镜像源
   ```

### 问题 6：快照创建失败

**症状：**
```bash
[ERROR] 创建快照失败：...
```

**解决方案：**
1. **检查磁盘空间**
   快照需要存储空间，确保磁盘有足够剩余空间

2. **检查快照目录权限**
   默认快照存储在用户目录下，确保有写入权限

3. **查看错误详情**
   使用 `--verbose` 查看详细错误信息

### 问题 7：回滚失败

**症状：**
```bash
[ERROR] 回滚失败：...
```

**解决方案：**
1. **确认快照存在**
   ```bash
   pyenv-doctor snapshot list
   ```

2. **检查虚拟环境是否匹配**
   快照只能在创建时的 Python 版本和虚拟环境中回滚

3. **手动回滚**
   如果自动回滚失败，可以手动执行快照中的依赖安装命令

### 其他问题

如果以上方案无法解决您的问题：
1. 查看 [GitHub Issues](https://github.com/GH-tll/pyenv-doctor/issues) 是否有类似问题
2. 提交新 Issue，附上错误信息和环境信息
3. 使用 `--verbose` 参数获取详细日志

---

## 版本历史

### v1.1.3 (当前版本)

**发布日期**: 2026-04-26

**新增功能：**
- 快速模式（`--fast`）：仅扫描当前环境，排除基础包，大幅提升诊断速度
- 虚拟环境精准识别：自动检测并优先扫描当前激活的虚拟环境
- 基础包过滤：自动排除 pip、setuptools、wheel、pkg_resources 等基础包

**优化改进：**
- 解决全局环境扫描包数量过多问题（从几百个减少到几十个）
- 提升诊断速度，减少等待时间
- 改善用户体验，避免误扫描外部环境包

### v1.1.2

**发布日期**: 2026-04-24

**修复改进**：
- 移除 `create-env` 命令，聚焦核心诊断修复功能
- 优化文档完整性

### v1.1.0

**新增功能：**
- 快照管理：完整的快照生命周期管理（创建/列表/回滚/删除/导出）
- 自动修复：`diagnose --fix` 自动执行修复命令
- 回滚引擎：支持快速回滚到任意快照状态
- 临时快照：自动修复时自动创建临时快照，支持转永久
- 三种修复策略：保守/平衡/激进，适配不同场景

**修复策略说明：**
- **保守策略** (`conservative`)：只降级，避免升级风险，适合生产环境
- **平衡策略** (`balanced`)：最小改动，按需升降级，适合开发环境（默认）
- **激进策略** (`aggressive`)：升到最新，获取最新功能，适合测试环境

**自动修复流程：**
1. 创建临时快照（记录修复前状态）
2. 根据策略执行修复
3. 修复成功后询问是否保留
4. 可选择转为永久快照或回滚

### v0.1.5

**新增功能：**
- 报告导出功能（JSON/Markdown）
- requirements.txt 解析支持
- pyproject.toml 解析支持
- 沙箱预演并行优化（提升 60% 速度）
- 新增 `check-file` 命令
- 性能基准测试

**优化改进：**
- 并行预演支持自定义工作线程数
- 导出报告包含健康分数和智能建议
- 完善文档和使用示例

### v0.1.0 (MVP)

- 环境扫描功能
- 冲突检测功能
- 沙箱预演功能
- CLI 命令入口

---

## 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献者

- [@GH-tll](https://github.com/GH-tll) - 项目创建者

### 开发路线图

- [x] 自动修复功能（v1.1.0）
- [x] 环境快照管理（v1.1.0）
- [x] 回滚引擎（v1.1.0）
- [ ] LLM 集成（自然语言诊断）
- [ ] Web 界面（可视化）
- [ ] 批量模式（多环境对比）

---

## 许可证

MIT License

---

## 相关链接

- [GitHub 仓库](https://github.com/GH-tll/pyenv-doctor)
- [Gitee 镜像](https://gitee.com/longl_T/pyenv-doctor)
- [PyPI 页面](https://pypi.org/project/pyenv-doctor-tool/)
- [问题反馈](https://github.com/GH-tll/pyenv-doctor/issues)

---

<div align="center">

**PyEnv Doctor - 让 Python 环境管理更安全、更智能**

[⬆ 返回顶部](#pyenv-doctor)

</div>
