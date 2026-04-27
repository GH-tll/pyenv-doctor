# PyEnv Doctor

Python 环境诊断与自动修复工具

[![PyPI version](https://badge.fury.io/py/pyenv-doctor-tool.svg)](https://pypi.org/project/pyenv-doctor-tool/)
[![GitHub stars](https://img.shields.io/github/stars/GH-tll/pyenv-doctor)](https://github.com/GH-tll/pyenv-doctor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 简介

PyEnv Doctor 是一个智能的 Python 环境诊断与自动修复工具。它通过构建依赖图谱、在沙箱中预演修复方案，确保修复建议的安全性。

**核心价值：** 沙箱预演，安全修复，智能诊断。

### 解决什么问题？

- **依赖冲突**：`pip install` 导致现有包版本不兼容，项目无法运行
- **修复风险**：AI 给出的修复命令缺乏全局考量，执行后可能导致更严重的损坏
- **试错成本**：环境一旦损坏，重建虚拟环境、重新安装依赖耗时极长
- **无法回滚**：执行修复命令后发现问题更严重，但无法快速恢复到修复前状态

### 核心功能

- ✅ **智能诊断**：自动扫描环境，检测依赖冲突
- ✅ **沙箱预演**：在隔离环境中验证修复方案，确保安全
- ✅ **自动修复**：`diagnose --fix` 自动执行修复，智能生成修复建议
- ✅ **快照管理**：创建环境快照，支持快速回滚
- ✅ **多格式报告**：支持 JSON 和 Markdown 格式诊断报告

---

## 快速开始

### 安装

#### 从正式 PyPI 安装（推荐）

```bash
# 卸载旧版本（如果已安装）
pip uninstall pyenv-doctor-tool -y

# 从正式 PyPI 安装（稳定版 v0.1.5）
pip install pyenv-doctor-tool

# 验证安装
pyenv-doctor --version
```

### 基本使用

```bash
# 1. 诊断当前环境（推荐快速模式）
pyenv-doctor diagnose --fast

# 2. 自动修复依赖冲突
pyenv-doctor diagnose --fix

# 3. 创建环境快照
pyenv-doctor snapshot create --label "healthy-state"

# 4. 回滚到快照
pyenv-doctor snapshot rollback --latest
```

### 常用命令

| 命令 | 说明 |
|:---|:---|
| `pyenv-doctor diagnose` | 诊断环境依赖冲突 |
| `pyenv-doctor diagnose --fix` | 自动修复依赖冲突 |
| `pyenv-doctor diagnose --fast` | 快速模式（推荐） |
| `pyenv-doctor snapshot create` | 创建环境快照 |
| `pyenv-doctor snapshot list` | 查看快照列表 |
| `pyenv-doctor snapshot rollback --latest` | 回滚到最新快照 |
| `pyenv-doctor check-file requirements.txt` | 检查依赖文件 |

---

## 核心功能详解

### 1. 环境诊断

```bash
# 基本诊断
pyenv-doctor diagnose

# 快速模式（推荐，排除基础包，仅扫描当前环境）
pyenv-doctor diagnose --fast

# 自动修复（使用平衡策略）
pyenv-doctor diagnose --fix

# 保守策略（只降级，避免升级风险）
pyenv-doctor diagnose --fix --strategy conservative

# 导出诊断报告
pyenv-doctor diagnose --output report.json
pyenv-doctor diagnose --output report.md
```

**修复策略：**
- `conservative`：保守策略 - 只降级，适合生产环境
- `balanced`：平衡策略 - 最小改动，适合开发环境（默认）
- `aggressive`：激进策略 - 升到最新，适合测试环境

### 2. 快照管理

```bash
# 创建永久快照
pyenv-doctor snapshot create --label "before-upgrade"

# 创建临时快照（自动修复时使用）
pyenv-doctor snapshot create --temporary

# 查看快照列表
pyenv-doctor snapshot list

# 回滚到最新快照
pyenv-doctor snapshot rollback --latest

# 回滚到指定快照
pyenv-doctor snapshot rollback <SNAPSHOT_ID>

# 删除快照
pyenv-doctor snapshot delete <SNAPSHOT_ID>

# 导出快照为 requirements.txt
pyenv-doctor snapshot export <SNAPSHOT_ID>
```

### 3. 文件检查

```bash
# 检查 requirements.txt
pyenv-doctor check-file requirements.txt

# 检查 pyproject.toml
pyenv-doctor check-file pyproject.toml

# 导出依赖列表
pyenv-doctor check-file requirements.txt --output deps.json
```

---

## 输出示例

### 无冲突环境

```
$ pyenv-doctor diagnose --fast
[SCAN] 扫描环境...
[OK] 发现 10 个包
[DIAGNOSE] 检测冲突...
[OK] 未发现冲突
```

### 有冲突环境

```
$ pyenv-doctor diagnose --fast
[SCAN] 扫描环境...
[OK] 发现 280 个包
[DIAGNOSE] 检测冲突...
[WARN] 发现 2 个冲突:
  - pandas 要求 numpy<1.24，但已安装 1.24.0
  - scipy 要求 numpy<1.23，但已安装 1.24.0
[SANDBOX] 并行模拟修复（3 个工作线程）...
[RESULT] 修复建议:

【推荐方案】[已验证] ★★★★★
  pip install numpy==1.23.5 pandas==1.5.3

【保守方案】[部分验证] ★★★☆☆
  pip install numpy==1.22.0 pandas==1.5.0
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
│   ├── EnvScanner: 环境扫描
│   ├── ConflictSolver: 冲突检测
│   └── SandboxExecutor: 沙箱预演（支持并行）
├── Repair Layer
│   ├── AutoRepair: 自动修复
│   ├── RollbackEngine: 回滚引擎
│   └── StrategyEngine: 修复策略
└── Snapshot Layer
    ├── SnapshotManager: 快照管理
    └── SnapshotStorage: 快照存储
```

### 核心工作流程

```
pyenv-doctor diagnose
    ↓
扫描环境（获取已安装包）
    ↓
检测冲突（构建依赖图）
    ↓
沙箱预演（并行/串行验证修复方案）
    ↓
输出诊断报告 + 修复建议
    ↓
[可选] 自动修复 / 导出报告
```

---

## 性能基准

| 场景 | 包数量 | 耗时 | 状态 |
|:---:|:---:|:---:|:---:|
| 快速扫描 | 50 | ~0.3 秒 | ✅ |
| 完整扫描 | 280 | ~1.5 秒 | ✅ |
| 冲突检测 | 280 | ~0.5 秒 | ✅ |
| 沙箱预演（并行） | 5 冲突 | ~60 秒 | ✅ 提升 60% |

---

## 常见问题

### Q: 沙箱预演会不会影响当前环境？

**A:** 不会。沙箱预演在临时创建的虚拟环境中进行，预演完成后会自动清理，不会影响当前环境。

### Q: 快速模式（`--fast`）有什么作用？

**A:** 快速模式排除基础包（pip、setuptools、wheel 等），仅扫描当前环境，大幅提升诊断速度。特别适合全局环境包数量过多的场景。

### Q: 如何解读健康分数？

**A:** 健康分数计算公式：`100 * (1 - 冲突数/总包数)`
- 90-100: 优秀 ✅
- 70-89: 良好 ⚠️
- 50-69: 一般 ⚠️
- 0-49: 较差 ❌

### Q: 支持哪些 Python 版本和操作系统？

**A:** 
- Python: 3.8, 3.9, 3.10, 3.11, 3.12
- 操作系统：Windows、Linux、macOS 全平台支持

---

## 版本历史

### v0.1.5 (正式 PyPI 稳定版) - 2026-04-27

**新增功能：**
- 完整的依赖冲突自动修复功能
- 智能诊断依赖冲突
- 沙箱预演修复方案
- 自动执行修复命令
- 修复后自动验证
- 版本范围解析修复：正确解析复杂版本约束（如 `<4,>=3.6.0`）
- 自动修复包名修复：从建议中提取正确的包名
- 错误处理优化：快照为空时的友好提示

---

## 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献者

- [@GH-tll](https://github.com/GH-tll) - 项目创建者

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
