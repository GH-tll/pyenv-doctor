# PyEnv Doctor v3.1 产品需求文档 (PRD)

| 文档版本 | 修改日期 | 修改人 | 备注 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-04-23 | 阿零-产品领航员 | 初始版本，定义 MVP 核心功能与技术边界 |
| v3.1 | 2026-04-23 | 阿零-产品领航员 | 最终版本：精简 MVP、补充技术实现指南、接口定义、测试用例 |

---

## 1. 产品概述

### 1.1 背景与痛点

Python 开发者在日常工作中频繁遭遇环境管理难题：

- **依赖冲突地狱**：`pip install` 导致现有包版本不兼容，项目无法运行
- **黑盒修复风险**：通用 AI 助手给出的修复命令往往缺乏全局考量，执行后可能导致更严重的损坏
- **试错成本高昂**：环境一旦损坏，重建虚拟环境、重新安装依赖耗时极长

### 1.2 核心价值主张

**"沙箱预演，安全修复。"**

PyEnv Doctor 是一个**基于 OpenManus 的环境智能诊断系统**。它通过构建依赖图谱、在沙箱中预演修复方案，确保修复建议的安全性。

### 1.3 目标用户

- **核心用户**：Python 后端开发者、数据科学家、AI 工程师
- **典型场景**：依赖升级、环境报错排查

### 1.4 竞品分析

| 竞品 | 核心能力 | 局限性 | PyEnv Doctor 差异化优势 |
|:---|:---|:---|:---|
| `pipdeptree` | 依赖树可视化 | 无冲突检测，无修复建议 | 增加冲突检测 + 沙箱预演 + 修复建议 |
| `pip-check` | 列出过时包 | 无依赖冲突分析 | 增加依赖冲突分析 |

**核心壁垒**：沙箱预演机制是真正的技术壁垒，确保修复方案的安全性

---

## 2. 功能需求

### 2.1 版本规划

| 版本 | 核心功能 | 开发周期 | 核心竞争力 | 简历含金量 |
|:---|:---:|:---:|:---|:---:|
| **v1.0 MVP** | 环境扫描 + 冲突检测 + **沙箱预演** + 修复建议 | 14 天 | 沙箱预演是核心壁垒 | 高 |
| **v1.1** | 自动修复 + 回滚机制 + 快照管理 | 7 天 | 完整的"诊断+修复"闭环 | 很高 |
| **v1.2** | LLM 集成 + 自然语言命令 | 5 天 | 智能化增强 | 很高 |

### 2.2 v1.0 MVP 功能清单

| 模块 | 功能 | 验收标准 |
|:---|:---|:---|
| **EnvScanner** | 环境扫描 | 输出已安装包列表及版本，耗时 < 3 秒 |
| **ConflictSolver** | 冲突检测 | 输出冲突列表，准确率 > 95% |
| **SandboxExecutor** | 沙箱预演 | 输出预演结果，耗时 < 60 秒 |
| **CLI** | 命令入口 | `pyenv-doctor diagnose` 命令可用 |

### 2.3 非功能性需求

| 维度 | 要求 |
|:---|:---|
| **性能** | 环境扫描 < 3 秒；沙箱预演 < 60 秒 |
| **兼容性** | Python 3.8+；Windows/Linux/macOS |

---

## 3. 技术架构概要

### 3.1 整体架构

```
PyEnv Doctor
├── CLI (Click)
│   └── diagnose 命令
├── Agent Layer (OpenManus)
│   ├── EnvScanner: 环境扫描 Agent
│   ├── ConflictSolver: 冲突检测 Agent
│   └── SandboxExecutor: 沙箱预演 Agent
└── Tool Layer
    ├── pip_tool: 封装 pip 命令
    └── venv_tool: 封装 venv 操作
```

### 3.2 核心工作流

```
pyenv-doctor diagnose
    ↓
启动检测（Python 版本、虚拟环境）
    ↓
EnvScanner 扫描环境（获取已安装包）
    ↓
ConflictSolver 检测冲突（构建依赖图）
    ↓
SandboxExecutor 沙箱预演（模拟修复）
    ↓
输出诊断报告 + 修复建议
```

### 3.3 技术依赖

| 依赖项 | 版本 | 用途 |
|:---|:---|:---|
| OpenManus | >= 0.1.0 | Agent 框架，从 Day 1 集成 |
| Python | >= 3.8 | 运行环境 |
| Click | >= 8.0 | CLI 框架 |
| packaging | >= 21.0 | 版本解析 |

### 3.4 项目目录结构

```
pyenv-doctor/
├── pyproject.toml
├── README.md
├── src/
│   └── pyenv_doctor/
│       ├── __init__.py
│       ├── cli.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── env_scanner.py
│       │   ├── conflict_solver.py
│       │   └── sandbox_executor.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── pip_tool.py
│       │   └── venv_tool.py
│       └── models/
│           ├── __init__.py
│           └── schemas.py
└── tests/
    ├── __init__.py
    ├── test_env_scanner.py
    ├── test_conflict_solver.py
    └── test_sandbox_executor.py
```

### 3.5 pyproject.toml 配置

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "pyenv-doctor"
version = "0.1.0"
description = "Python environment diagnosis and sandbox preview tool"
requires-python = ">=3.8"
dependencies = [
    "openmanus>=0.1.0",
    "click>=8.0",
    "packaging>=21.0",
]

[project.scripts]
pyenv-doctor = "pyenv_doctor.cli:diagnose"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
```

---

## 4. 技术实现指南（MVP）

### 4.1 EnvScanner 实现

**功能**：获取当前环境已安装的包列表

**技术方案**：
```python
from importlib.metadata import distributions
from typing import List, Dict

class EnvScanner:
    def scan(self) -> List[Dict]:
        packages = []
        for dist in distributions():
            packages.append({
                "name": dist.metadata["Name"],
                "version": dist.version,
                "requires": [str(r) for r in (dist.requires or [])]
            })
        return packages
```

**输入**：无

**输出**：
```python
[
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "pandas", "version": "1.5.3", "requires": ["numpy<1.24"]}
]
```

### 4.2 ConflictSolver 实现

**功能**：检测依赖冲突

**技术方案**：
```python
from packaging.requirements import Requirement
from packaging.version import Version
from typing import List, Dict

class ConflictSolver:
    def detect(self, packages: List[Dict]) -> List[Dict]:
        conflicts = []
        installed = {p["name"].lower(): p["version"] for p in packages}
        
        for pkg in packages:
            for req_str in pkg.get("requires", []):
                try:
                    req = Requirement(req_str)
                    req_name = req.name.lower()
                    if req_name in installed:
                        installed_version = Version(installed[req_name])
                        if not req.specifier.contains(installed_version):
                            conflicts.append({
                                "package": pkg["name"],
                                "requires": req_str,
                                "installed": installed[req_name],
                                "suggestion": self._generate_suggestion(req_name, req.specifier)
                            })
                except Exception:
                    pass
        return conflicts
    
    def _generate_suggestion(self, name: str, specifier) -> str:
        for spec in specifier:
            if spec.operator == "<":
                return f"{name}=={spec.version}"
        return f"{name} (compatible version)"
```

**输入**：EnvScanner 的输出

**输出**：
```python
[
    {
        "package": "pandas",
        "requires": "numpy<1.24",
        "installed": "1.24.0",
        "suggestion": "numpy==1.23.5"
    }
]
```

### 4.3 SandboxExecutor 实现

**功能**：在沙箱中预演修复方案

**技术方案**：
```python
import subprocess
import tempfile
import venv
from pathlib import Path
from typing import List, Dict, Tuple

class SandboxExecutor:
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
    
    def create_sandbox(self) -> Path:
        sandbox_dir = Path(tempfile.mkdtemp(prefix="pyenv_doctor_"))
        venv.create(sandbox_dir, with_pip=True)
        return sandbox_dir
    
    def get_pip_path(self, sandbox_dir: Path) -> Path:
        if (sandbox_dir / "Scripts" / "pip.exe").exists():
            return sandbox_dir / "Scripts" / "pip.exe"
        return sandbox_dir / "bin" / "pip"
    
    def simulate_fix(self, sandbox_dir: Path, suggestion: str) -> Tuple[bool, str]:
        pip_path = self.get_pip_path(sandbox_dir)
        try:
            result = subprocess.run(
                [str(pip_path), "install", suggestion, "--quiet"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result.returncode == 0, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Timeout"
    
    def preview(self, conflicts: List[Dict]) -> List[Dict]:
        results = []
        sandbox = self.create_sandbox()
        
        for conflict in conflicts:
            suggestion = conflict["suggestion"]
            success, error = self.simulate_fix(sandbox, suggestion)
            results.append({
                "scheme": suggestion,
                "success": success,
                "error": error if not success else None
            })
        
        self._cleanup(sandbox)
        return results
    
    def _cleanup(self, sandbox_dir: Path):
        import shutil
        shutil.rmtree(sandbox_dir, ignore_errors=True)
```

**输入**：ConflictSolver 的输出

**输出**：
```python
[
    {
        "scheme": "numpy==1.23.5",
        "success": True,
        "error": None
    }
]
```

### 4.4 CLI 实现

**功能**：命令行入口

**技术方案**：
```python
import click

@click.command()
def diagnose():
    click.echo("[SCAN] Scanning environment...")
    
    scanner = EnvScanner()
    packages = scanner.scan()
    click.echo(f"[OK] Found {len(packages)} packages")
    
    click.echo("[DIAGNOSE] Detecting conflicts...")
    solver = ConflictSolver()
    conflicts = solver.detect(packages)
    
    if not conflicts:
        click.echo("[OK] No conflicts found")
        return
    
    click.echo(f"[WARN] Found {len(conflicts)} conflicts:")
    for c in conflicts:
        click.echo(f"  - {c['package']} requires {c['requires']}, but {c['installed']} installed")
    
    click.echo("[SANDBOX] Simulating fixes...")
    executor = SandboxExecutor()
    results = executor.preview(conflicts)
    
    click.echo("[RESULT] Fix suggestions:")
    for r in results:
        if r["success"]:
            click.echo(f"  [OK] pip install {r['scheme']}")
        else:
            click.echo(f"  [FAIL] {r['scheme']}: {r['error']}")

if __name__ == "__main__":
    diagnose()
```

### 4.5 OpenManus 集成

**功能**：将模块封装为 Agent

**技术方案**：
```python
from openmanus import Agent, Tool

class PipTool(Tool):
    name = "pip"
    
    def execute(self, command: str):
        import subprocess
        result = subprocess.run(
            ["pip"] + command.split(),
            capture_output=True,
            text=True
        )
        return result.stdout

class VenvTool(Tool):
    name = "venv"
    
    def execute(self, path: str):
        import venv
        venv.create(path, with_pip=True)
        return f"Created venv at {path}"

class EnvScannerAgent(Agent):
    tools = [PipTool()]
    
    def execute(self, task: str):
        scanner = EnvScanner()
        return scanner.scan()

class ConflictSolverAgent(Agent):
    def execute(self, packages):
        solver = ConflictSolver()
        return solver.detect(packages)

class SandboxExecutorAgent(Agent):
    tools = [VenvTool(), PipTool()]
    
    def execute(self, conflicts):
        executor = SandboxExecutor()
        return executor.preview(conflicts)
```

---

## 5. 数据结构定义

### 5.1 PackageInfo

```python
@dataclass
class PackageInfo:
    name: str
    version: str
    requires: List[str]
```

### 5.2 Conflict

```python
@dataclass
class Conflict:
    package: str
    requires: str
    installed: str
    suggestion: str
```

### 5.3 SandboxResult

```python
@dataclass
class SandboxResult:
    scheme: str
    success: bool
    error: Optional[str]
```

---

## 6. 测试用例

### 6.1 EnvScanner 测试

| 用例 | 测试数据 | 预期输出 |
|:---|:---|:---|
| 空环境 | 新建 venv | `[]` |
| 单包环境 | 安装 `numpy==1.24.0` | `[{"name": "numpy", "version": "1.24.0", "requires": []}]` |
| 多包环境 | 安装 numpy、pandas | 包含两个包的列表 |

### 6.2 ConflictSolver 测试

| 用例 | 测试数据 | 预期输出 |
|:---|:---|:---|
| 无冲突 | numpy 1.24.0, pandas 2.0.0 | `[]` |
| 单冲突 | numpy 1.24.0, pandas 1.5.3 | 包含 1 个冲突 |
| 多冲突 | numpy 1.24.0, pandas 1.5.3, scipy 1.10.0 (冲突) | 包含 2 个冲突 |

**具体测试数据**：
```python
test_packages = [
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "pandas", "version": "1.5.3", "requires": ["numpy<1.24"]}
]
# 预期输出：1 个冲突
```

### 6.3 SandboxExecutor 测试

| 用例 | 测试数据 | 预期输出 |
|:---|:---|:---|
| 成功预演 | `numpy==1.23.5` | `success=True` |
| 失败预演 | `numpy==999.999.999` (不存在) | `success=False` |
| 超时处理 | 大包安装 | 超时返回 `success=False` |

---

## 7. 开发计划（MVP）

### 7.1 详细任务拆分

| 天数 | 任务 | 具体工作 | 产出 |
|:---:|:---|:---|:---|
| 1 | 项目初始化 | 创建项目结构、配置 pyproject.toml、安装 OpenManus | 可运行的项目骨架 |
| 2 | CLI 入口 | 实现 `pyenv-doctor diagnose` 命令 | 命令可执行 |
| 3 | EnvScanner | 实现 scan() 方法 | 返回包列表 |
| 4 | EnvScanner 测试 | 编写单元测试 | pytest 通过 |
| 5 | ConflictSolver | 实现 detect() 方法 | 返回冲突列表 |
| 6 | ConflictSolver 测试 | 编写单元测试 | pytest 通过 |
| 7 | SandboxExecutor | 实现 create_sandbox() | 创建临时环境 |
| 8 | SandboxExecutor | 实现 simulate_fix() | 模拟安装 |
| 9 | SandboxExecutor 测试 | 编写单元测试 | pytest 通过 |
| 10 | 集成测试 | 端到端测试 | 完整流程通过 |
| 11 | OpenManus Agent | 封装为 Agent | Agent 可调度 |
| 12 | 错误处理 | 添加异常处理 | 友好错误信息 |
| 13 | 文档 | 编写 README | 可用的文档 |
| 14 | 发布 | 打包发布到 PyPI | 可 pip install |

### 7.2 每日产出物

| 天数 | 产出物 | 验收标准 |
|:---:|:---|:---|
| 1 | 项目骨架 | `pyenv-doctor --version` 可执行 |
| 2 | CLI 命令 | `pyenv-doctor diagnose` 可执行 |
| 3 | scan() | 返回包列表 |
| 4 | 单元测试 | pytest 通过 |
| 5 | detect() | 返回冲突列表 |
| 6 | 单元测试 | pytest 通过 |
| 7 | create_sandbox() | 创建临时 venv |
| 8 | simulate_fix() | 模拟安装成功/失败 |
| 9 | 单元测试 | pytest 通过 |
| 10 | 端到端测试 | 完整流程通过 |
| 11 | Agent 封装 | OpenManus 可调度 |
| 12 | 错误处理 | 友好错误信息 |
| 13 | README | 可用的文档 |
| 14 | PyPI 发布 | 可 pip install |

---

## 8. 风险评估

| 风险 | 可能性 | 影响 | 应对 |
|:---|:---:|:---:|:---|
| OpenManus 不熟悉 | 高 | 中 | Day 1 开始学习，Day 11 封装 |
| 沙箱创建慢 | 中 | 中 | 设置 60 秒超时 |
| 依赖解析复杂 | 中 | 中 | MVP 只检测明显冲突 |

---

## 9. 简历亮点

| 亮点 | 描述 |
|:---|:---|
| **AI Agent 架构** | 基于 OpenManus 框架设计模块化 Agent 架构，将 pip、venv 操作封装为 Tool，实现任务自主调度 |
| **沙箱隔离技术** | 创新性地引入沙箱预演机制，在隔离环境中验证修复方案，预演耗时 < 60 秒 |
| **依赖解析** | 使用 packaging 库实现依赖冲突检测，准确率 > 95% |
| **工程化** | 完整的测试覆盖、PyPI 发布、多平台兼容 |

---

## 10. 面试准备

### 10.1 关于 OpenManus

**Q: 为什么用 OpenManus？**

A: OpenManus 提供了模块化的 Agent 架构。我将 EnvScanner、ConflictSolver、SandboxExecutor 封装为独立 Agent，每个 Agent 有明确的职责。同时 OpenManus 的 Tool Use 机制让我可以将 pip、venv 操作封装为标准 Tool，便于扩展。

### 10.2 关于沙箱预演

**Q: 沙箱预演如何实现？**

A: 使用 Python 内置的 venv 模块创建临时虚拟环境，然后用 subprocess 执行 pip install 命令模拟安装。通过检查返回码判断是否成功。设置 60 秒超时防止长时间等待。

**Q: 沙箱预演有什么局限？**

A: 沙箱环境与真实环境可能存在差异，比如系统依赖、C 扩展编译等。所以预演结果仅供参考，最终还需要用户确认。

### 10.3 关于依赖解析

**Q: 依赖解析是怎么实现的？**

A: 使用 Python 的 packaging 库解析版本约束。遍历每个包的依赖，检查已安装版本是否满足约束条件。MVP 阶段只检测明显的版本冲突，不处理复杂的依赖链。

---

## 11. MVP 水平定位

| 维度 | 水平 | 说明 |
|:---|:---:|:---|
| 功能完整性 | **可用** | 核心诊断 + 沙箱预演 + 修复建议 |
| 技术深度 | **中高** | AI Agent 架构 + 沙箱隔离 + 依赖解析 |
| 可落地性 | **高** | 有具体的技术实现指南、测试用例、项目结构 |
| 简历含金量 | **高** | 有技术深度和展开空间 |
| 开发周期 | **合理** | 14 天，每天有明确产出 |
| 重量 | **轻** | 4 个模块、1 个命令、4 个依赖 |
| 真实性 | **高** | 都是可实现的功能 |
