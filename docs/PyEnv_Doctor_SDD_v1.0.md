# PyEnv Doctor 软件详细设计文档 (SDD)

| 文档版本 | 修改日期 | 修改人 | 备注 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-04-24 | 需求规格师 | 初始版本，基于 PRD v3.1 |

---

## 1. 项目结构设计

### 1.1 目录结构

```
pyenv-doctor/
├── pyproject.toml                    # 项目配置文件
├── README.md                         # 项目说明文档
├── src/
│   └── pyenv_doctor/
│       ├── __init__.py               # 包初始化，暴露版本号
│       ├── cli.py                    # CLI 命令入口
│       ├── agents/
│       │   ├── __init__.py           # Agent 模块初始化
│       │   ├── env_scanner.py        # 环境扫描 Agent
│       │   ├── conflict_solver.py    # 冲突检测 Agent
│       │   └── sandbox_executor.py   # 沙箱预演 Agent
│       ├── tools/
│       │   ├── __init__.py           # Tool 模块初始化
│       │   ├── pip_tool.py           # pip 命令封装
│       │   └── venv_tool.py          # venv 操作封装
│       └── models/
│           ├── __init__.py           # 数据模型初始化
│           └── schemas.py            # 数据结构定义
└── tests/
    ├── __init__.py                   # 测试模块初始化
    ├── test_env_scanner.py           # EnvScanner 单元测试
    ├── test_conflict_solver.py       # ConflictSolver 单元测试
    └── test_sandbox_executor.py      # SandboxExecutor 单元测试
```

### 1.2 模块职责划分

| 模块 | 文件路径 | 职责 | 依赖 |
| :--- | :--- | :--- | :--- |
| CLI | `cli.py` | 命令行入口，协调各 Agent 执行 | Click, 所有 Agent |
| EnvScanner | `agents/env_scanner.py` | 扫描当前 Python 环境已安装包 | importlib.metadata |
| ConflictSolver | `agents/conflict_solver.py` | 检测依赖版本冲突 | packaging |
| SandboxExecutor | `agents/sandbox_executor.py` | 创建沙箱并预演修复方案 | venv, subprocess |
| PipTool | `tools/pip_tool.py` | 封装 pip 命令执行 | subprocess |
| VenvTool | `tools/venv_tool.py` | 封装虚拟环境创建 | venv |
| Schemas | `models/schemas.py` | 定义数据结构 | dataclasses |

---

## 2. 接口定义

### 2.1 EnvScanner 接口

#### 2.1.1 类定义

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `name` | `str` | Agent 名称，固定值 `"EnvScanner"` |

#### 2.1.2 方法定义

| 方法名 | 入参 | 出参 | 说明 |
| :--- | :--- | :--- | :--- |
| `scan()` | 无 | `List[PackageInfo]` | 扫描当前环境已安装包 |

#### 2.1.3 入参详细定义

| 参数名 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| - | - | - | - | 无入参 |

#### 2.1.4 出参详细定义

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `name` | `str` | 非空，长度 1-200 | 包名称 |
| `version` | `str` | 符合 PEP 440 版本格式 | 包版本号 |
| `requires` | `List[str]` | 可为空列表 | 依赖列表，每项为依赖声明字符串 |

#### 2.1.5 异常处理

| 异常场景 | 处理方式 | 返回值 |
| :--- | :--- | :--- |
| 环境无包 | 正常返回 | `[]` |
| 元数据读取失败 | 跳过该包，记录日志 | 不包含该包的列表 |
| 权限不足 | 抛出 `PermissionError` | - |

---

### 2.2 ConflictSolver 接口

#### 2.2.1 类定义

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| `name` | `str` | Agent 名称，固定值 `"ConflictSolver"` |

#### 2.2.2 方法定义

| 方法名 | 入参 | 出参 | 说明 |
| :--- | :--- | :--- | :--- |
| `detect(packages)` | `List[PackageInfo]` | `List[Conflict]` | 检测依赖冲突 |
| `_generate_suggestion(name, specifier)` | `str, SpecifierSet` | `str` | 生成修复建议（内部方法） |

#### 2.2.3 入参详细定义

| 参数名 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `packages` | `List[PackageInfo]` | 是 | 非空列表 | EnvScanner 输出的包列表 |

#### 2.2.4 出参详细定义

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `package` | `str` | 非空 | 存在冲突的包名称 |
| `requires` | `str` | 非空，符合依赖声明格式 | 依赖要求字符串 |
| `installed` | `str` | 符合 PEP 440 版本格式 | 当前已安装版本 |
| `suggestion` | `str` | 非空 | 修复建议，格式为 `包名==版本号` |

#### 2.2.5 冲突检测规则

| 规则编号 | 检测逻辑 | 示例 |
| :--- | :--- | :--- |
| R1 | 已安装版本不满足 `<` 约束 | 要求 `numpy<1.24`，已安装 `1.24.0` |
| R2 | 已安装版本不满足 `>` 约束 | 要求 `numpy>1.20`，已安装 `1.19.0` |
| R3 | 已安装版本不满足 `<=` 约束 | 要求 `numpy<=1.23`，已安装 `1.24.0` |
| R4 | 已安装版本不满足 `>=` 约束 | 要求 `numpy>=1.21`，已安装 `1.20.0` |
| R5 | 已安装版本不满足 `==` 约束 | 要求 `numpy==1.23.0`，已安装 `1.24.0` |
| R6 | 已安装版本不满足 `!=` 约束 | 要求 `numpy!=1.24.0`，已安装 `1.24.0` |
| R7 | 已安装版本不满足 `~=` 约束 | 要求 `numpy~=1.23`，已安装 `1.24.0` |

#### 2.2.6 异常处理

| 异常场景 | 处理方式 | 返回值 |
| :--- | :--- | :--- |
| 入参为空列表 | 正常返回 | `[]` |
| 依赖声明格式错误 | 跳过该依赖，继续检测 | 不包含该依赖的冲突列表 |
| 版本号格式错误 | 跳过该包，继续检测 | 不包含该包的冲突列表 |

---

### 2.3 SandboxExecutor 接口

#### 2.3.1 类定义

| 属性 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `name` | `str` | `"SandboxExecutor"` | Agent 名称 |
| `timeout` | `int` | `60` | 单次安装超时时间（秒） |

#### 2.3.2 方法定义

| 方法名 | 入参 | 出参 | 说明 |
| :--- | :--- | :--- | :--- |
| `create_sandbox()` | 无 | `Path` | 创建临时沙箱环境 |
| `get_pip_path(sandbox_dir)` | `Path` | `Path` | 获取沙箱内 pip 路径 |
| `simulate_fix(sandbox_dir, suggestion)` | `Path, str` | `Tuple[bool, str]` | 在沙箱中模拟安装 |
| `preview(conflicts)` | `List[Conflict]` | `List[SandboxResult]` | 批量预演修复方案 |
| `_cleanup(sandbox_dir)` | `Path` | 无 | 清理沙箱环境（内部方法） |

#### 2.3.3 入参详细定义

**create_sandbox()**

| 参数名 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| - | - | - | - | 无入参 |

**get_pip_path(sandbox_dir)**

| 参数名 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `sandbox_dir` | `Path` | 是 | 必须为有效目录 | 沙箱环境根目录 |

**simulate_fix(sandbox_dir, suggestion)**

| 参数名 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `sandbox_dir` | `Path` | 是 | 必须为有效目录 | 沙箱环境根目录 |
| `suggestion` | `str` | 是 | 格式为 `包名==版本号` | 修复建议 |

**preview(conflicts)**

| 参数名 | 类型 | 必填 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `conflicts` | `List[Conflict]` | 是 | 可为空列表 | 冲突列表 |

#### 2.3.4 出参详细定义

**create_sandbox()**

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| 返回值 | `Path` | 必须存在且为有效 venv 目录 | 沙箱环境根目录路径 |

**get_pip_path(sandbox_dir)**

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| 返回值 | `Path` | 必须存在 | pip 可执行文件路径 |

**simulate_fix(sandbox_dir, suggestion)**

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `success` | `bool` | - | 安装是否成功 |
| `error` | `str` | 成功时可为空 | 错误信息 |

**preview(conflicts)**

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| `scheme` | `str` | 非空 | 修复方案 |
| `success` | `bool` | - | 预演是否成功 |
| `error` | `Optional[str]` | 成功时为 `None` | 错误信息 |

#### 2.3.5 异常处理

| 异常场景 | 处理方式 | 返回值 |
| :--- | :--- | :--- |
| venv 创建失败 | 抛出 `OSError` | - |
| pip 不存在 | 抛出 `FileNotFoundError` | - |
| 安装超时 | 返回失败结果 | `(False, "Timeout")` |
| 网络错误 | 返回失败结果 | `(False, "Network error")` |
| 包不存在 | 返回失败结果 | `(False, "Package not found")` |
| 清理失败 | 记录日志，不抛异常 | - |

---

### 2.4 CLI 接口

#### 2.4.1 命令定义

| 命令 | 用法 | 说明 |
| :--- | :--- | :--- |
| `diagnose` | `pyenv-doctor diagnose` | 执行完整诊断流程 |

#### 2.4.2 命令选项

| 选项 | 短选项 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `--timeout` | `-t` | `int` | `60` | 沙箱预演超时时间（秒） |
| `--verbose` | `-v` | `bool` | `False` | 显示详细输出 |
| `--help` | `-h` | - | - | 显示帮助信息 |

#### 2.4.3 执行流程

```
[START] pyenv-doctor diagnose
    |
    v
[STEP 1] 检测 Python 版本
    |
    +-- Python < 3.8 --> [ERROR] 退出，提示版本不兼容
    |
    v
[STEP 2] 检测虚拟环境
    |
    +-- 非虚拟环境 --> [WARN] 提示建议在虚拟环境中运行
    |
    v
[STEP 3] EnvScanner.scan()
    |
    +-- 扫描失败 --> [ERROR] 退出，显示错误信息
    |
    v
[STEP 4] ConflictSolver.detect(packages)
    |
    +-- 无冲突 --> [OK] 输出 "No conflicts found"，退出
    |
    v
[STEP 5] SandboxExecutor.preview(conflicts)
    |
    +-- 预演失败 --> [WARN] 标记失败方案
    |
    v
[STEP 6] 输出诊断报告
    |
    v
[END]
```

#### 2.4.4 输出格式

**正常输出（无冲突）**

```
[SCAN] Scanning environment...
[OK] Found X packages
[DIAGNOSE] Detecting conflicts...
[OK] No conflicts found
```

**正常输出（有冲突）**

```
[SCAN] Scanning environment...
[OK] Found X packages
[DIAGNOSE] Detecting conflicts...
[WARN] Found Y conflicts:
  - package_a requires dependency<1.0, but 1.0.0 installed
  - package_b requires dependency>=2.0, but 1.9.0 installed
[SANDBOX] Simulating fixes...
[RESULT] Fix suggestions:
  [OK] pip install dependency==0.9.0
  [FAIL] dependency==2.0.0: Package not found
```

**错误输出**

```
[ERROR] Failed to scan environment: Permission denied
```

---

## 3. 数据结构定义

### 3.1 PackageInfo

#### 3.1.1 结构定义

| 字段名 | 类型 | 必填 | 默认值 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `name` | `str` | 是 | - | 非空，长度 1-200，仅允许字母、数字、下划线、连字符 | 包名称 |
| `version` | `str` | 是 | - | 符合 PEP 440 版本格式 | 包版本号 |
| `requires` | `List[str]` | 否 | `[]` | 每项符合依赖声明格式 | 依赖列表 |

#### 3.1.2 字段校验规则

| 字段 | 校验规则 | 错误提示 |
| :--- | :--- | :--- |
| `name` | 正则匹配 `^[a-zA-Z0-9_-]+$` | "Invalid package name format" |
| `version` | 使用 `packaging.version.Version` 解析 | "Invalid version format" |
| `requires` | 每项使用 `packaging.requirements.Requirement` 解析 | "Invalid requirement format" |

#### 3.1.3 示例

```python
PackageInfo(
    name="numpy",
    version="1.24.0",
    requires=[]
)

PackageInfo(
    name="pandas",
    version="1.5.3",
    requires=["numpy<1.24", "python-dateutil>=2.8.1"]
)
```

---

### 3.2 Conflict

#### 3.2.1 结构定义

| 字段名 | 类型 | 必填 | 默认值 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `package` | `str` | 是 | - | 非空 | 存在冲突的包名称 |
| `requires` | `str` | 是 | - | 符合依赖声明格式 | 依赖要求字符串 |
| `installed` | `str` | 是 | - | 符合 PEP 440 版本格式 | 当前已安装版本 |
| `suggestion` | `str` | 是 | - | 格式为 `包名==版本号` | 修复建议 |

#### 3.2.2 字段校验规则

| 字段 | 校验规则 | 错误提示 |
| :--- | :--- | :--- |
| `package` | 非空字符串 | "Package name cannot be empty" |
| `requires` | 使用 `packaging.requirements.Requirement` 解析 | "Invalid requirement format" |
| `installed` | 使用 `packaging.version.Version` 解析 | "Invalid installed version format" |
| `suggestion` | 正则匹配 `^[a-zA-Z0-9_-]+==.+$` | "Invalid suggestion format" |

#### 3.2.3 示例

```python
Conflict(
    package="pandas",
    requires="numpy<1.24",
    installed="1.24.0",
    suggestion="numpy==1.23.5"
)
```

---

### 3.3 SandboxResult

#### 3.3.1 结构定义

| 字段名 | 类型 | 必填 | 默认值 | 约束 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `scheme` | `str` | 是 | - | 格式为 `包名==版本号` | 修复方案 |
| `success` | `bool` | 是 | - | - | 预演是否成功 |
| `error` | `Optional[str]` | 否 | `None` | 成功时必须为 `None` | 错误信息 |

#### 3.3.2 字段校验规则

| 字段 | 校验规则 | 错误提示 |
| :--- | :--- | :--- |
| `scheme` | 正则匹配 `^[a-zA-Z0-9_-]+==.+$` | "Invalid scheme format" |
| `success` | 布尔值 | "Success must be boolean" |
| `error` | `success=True` 时必须为 `None` | "Error must be None when success is True" |

#### 3.3.3 示例

```python
# 成功案例
SandboxResult(
    scheme="numpy==1.23.5",
    success=True,
    error=None
)

# 失败案例
SandboxResult(
    scheme="numpy==999.999.999",
    success=False,
    error="Package not found"
)
```

---

## 4. 测试用例设计

### 4.1 EnvScanner 测试用例

#### 4.1.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ES-001 | 空环境扫描 | 新建空 venv | 无 | 调用 `scan()` | 返回 `[]` |
| ES-002 | 单包环境扫描 | 安装 `numpy==1.24.0` | 无 | 调用 `scan()` | 返回包含 1 个元素的列表，`name="numpy"`, `version="1.24.0"` |
| ES-003 | 多包环境扫描 | 安装 `numpy==1.24.0`, `pandas==1.5.3` | 无 | 调用 `scan()` | 返回包含 2 个元素的列表 |
| ES-004 | 包含依赖的包扫描 | 安装 `pandas==1.5.3` | 无 | 调用 `scan()` | pandas 的 `requires` 包含依赖声明 |
| ES-005 | 大量包扫描 | 安装 100+ 个包 | 无 | 调用 `scan()` | 耗时 < 3 秒，返回完整列表 |

#### 4.1.2 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ES-B01 | 包名含特殊字符 | 安装包名含连字符的包 | `python-dateutil` | 调用 `scan()` | 正确返回包名 |
| ES-B02 | 版本号含预发布标识 | 安装预发布版本 | `numpy==1.24.0rc1` | 调用 `scan()` | 正确返回版本号 |
| ES-B03 | 本地包扫描 | 通过 `pip install -e .` 安装本地包 | 无 | 调用 `scan()` | 正确返回本地包信息 |

#### 4.1.3 异常测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| ES-E01 | 元数据损坏 | 模拟包元数据损坏 | 无 | 调用 `scan()` | 跳过损坏包，返回其他包列表 |
| ES-E02 | 权限不足 | 无读取权限 | 无 | 调用 `scan()` | 抛出 `PermissionError` |

---

### 4.2 ConflictSolver 测试用例

#### 4.2.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CS-001 | 无冲突检测 | 无冲突环境 | 见下方数据 1 | 调用 `detect()` | 返回 `[]` |
| CS-002 | 单冲突检测 | 单冲突环境 | 见下方数据 2 | 调用 `detect()` | 返回包含 1 个冲突的列表 |
| CS-003 | 多冲突检测 | 多冲突环境 | 见下方数据 3 | 调用 `detect()` | 返回包含 2 个冲突的列表 |
| CS-004 | 版本范围冲突 | 版本范围约束冲突 | 见下方数据 4 | 调用 `detect()` | 正确检测冲突 |

**测试数据 1（无冲突）**

```python
[
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "pandas", "version": "2.0.0", "requires": ["numpy>=1.21"]}
]
```

**测试数据 2（单冲突）**

```python
[
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "pandas", "version": "1.5.3", "requires": ["numpy<1.24"]}
]
```

**测试数据 3（多冲突）**

```python
[
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "pandas", "version": "1.5.3", "requires": ["numpy<1.24"]},
    {"name": "scipy", "version": "1.10.0", "requires": ["numpy<1.23"]}
]
```

**测试数据 4（版本范围冲突）**

```python
[
    {"name": "numpy", "version": "1.20.0", "requires": []},
    {"name": "pandas", "version": "2.0.0", "requires": ["numpy>=1.21"]}
]
```

#### 4.2.2 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CS-B01 | 空列表输入 | 无 | `[]` | 调用 `detect()` | 返回 `[]` |
| CS-B02 | 复杂版本约束 | 多重约束 | 见下方数据 | 调用 `detect()` | 正确解析所有约束 |
| CS-B03 | 循环依赖 | A 依赖 B，B 依赖 A | 见下方数据 | 调用 `detect()` | 正确处理，不无限循环 |

**测试数据（复杂版本约束）**

```python
[
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "package", "version": "1.0.0", "requires": ["numpy>=1.21,<1.25,!=1.23.0"]}
]
```

#### 4.2.3 异常测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CS-E01 | 无效依赖声明 | 依赖声明格式错误 | 见下方数据 | 调用 `detect()` | 跳过无效依赖，继续检测 |
| CS-E02 | 无效版本号 | 版本号格式错误 | 见下方数据 | 调用 `detect()` | 跳过无效版本，继续检测 |

**测试数据（无效依赖声明）**

```python
[
    {"name": "numpy", "version": "1.24.0", "requires": []},
    {"name": "package", "version": "1.0.0", "requires": ["invalid<<<requirement"]}
]
```

---

### 4.3 SandboxExecutor 测试用例

#### 4.3.1 功能测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SE-001 | 成功预演 | 网络正常 | `numpy==1.23.5` | 调用 `preview()` | `success=True`, `error=None` |
| SE-002 | 失败预演-包不存在 | 网络正常 | `numpy==999.999.999` | 调用 `preview()` | `success=False`, `error` 包含 "not found" |
| SE-003 | 批量预演 | 网络正常 | 多个冲突 | 调用 `preview()` | 返回多个结果 |
| SE-004 | 沙箱创建 | 无 | 无 | 调用 `create_sandbox()` | 返回有效 venv 目录路径 |
| SE-005 | 沙箱清理 | 已创建沙箱 | 无 | 调用 `_cleanup()` | 沙箱目录被删除 |

#### 4.3.2 边界测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SE-B01 | 空冲突列表 | 无 | `[]` | 调用 `preview()` | 返回 `[]` |
| SE-B02 | 超时处理 | 网络慢 | 大包安装 | 调用 `preview(timeout=1)` | `success=False`, `error="Timeout"` |
| SE-B03 | 并发沙箱 | 无 | 无 | 同时创建多个沙箱 | 各沙箱独立，互不影响 |

#### 4.3.3 异常测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SE-E01 | 网络断开 | 无网络连接 | 任意包 | 调用 `preview()` | `success=False`, `error` 包含网络错误信息 |
| SE-E02 | 磁盘空间不足 | 磁盘满 | 无 | 调用 `create_sandbox()` | 抛出 `OSError` |
| SE-E03 | 清理失败 | 沙箱目录被占用 | 无 | 调用 `_cleanup()` | 记录日志，不抛异常 |

---

### 4.4 集成测试用例

#### 4.4.1 端到端测试

| 用例编号 | 用例名称 | 前置条件 | 测试数据 | 执行步骤 | 预期结果 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| E2E-001 | 完整诊断流程-无冲突 | 干净环境 | 无 | 执行 `pyenv-doctor diagnose` | 输出 "No conflicts found" |
| E2E-002 | 完整诊断流程-有冲突 | 冲突环境 | 安装冲突包 | 执行 `pyenv-doctor diagnose` | 输出冲突列表和修复建议 |
| E2E-003 | 详细模式 | 任意环境 | 无 | 执行 `pyenv-doctor diagnose -v` | 输出详细信息 |
| E2E-004 | 自定义超时 | 任意环境 | 无 | 执行 `pyenv-doctor diagnose -t 30` | 使用 30 秒超时 |

---

## 5. 技术实现细节

### 5.1 依赖版本解析

#### 5.1.1 版本解析规则

| 操作符 | 含义 | 示例 | 匹配版本 |
| :--- | :--- | :--- | :--- |
| `==` | 精确匹配 | `==1.24.0` | `1.24.0` |
| `!=` | 排除 | `!=1.24.0` | 除 `1.24.0` 外的所有版本 |
| `<` | 小于 | `<1.24.0` | `1.23.9`, `1.23.0`, ... |
| `<=` | 小于等于 | `<=1.24.0` | `1.24.0`, `1.23.9`, ... |
| `>` | 大于 | `>1.24.0` | `1.24.1`, `1.25.0`, ... |
| `>=` | 大于等于 | `>=1.24.0` | `1.24.0`, `1.24.1`, ... |
| `~=` | 兼容版本 | `~=1.24.0` | `>=1.24.0, ==1.24.*` |
| `===` | 任意匹配 | `===1.24.0` | 字符串完全匹配 |

#### 5.1.2 版本比较逻辑

```python
from packaging.version import Version
from packaging.specifiers import SpecifierSet

def check_version_conflict(installed_version: str, requirement: str) -> bool:
    """
    检查版本冲突
    
    Args:
        installed_version: 已安装版本号
        requirement: 依赖要求字符串
    
    Returns:
        True 表示存在冲突，False 表示无冲突
    """
    spec = SpecifierSet(requirement)
    version = Version(installed_version)
    return not spec.contains(version)
```

---

### 5.2 沙箱环境管理

#### 5.2.1 沙箱生命周期

```
[创建] create_sandbox()
    |
    v
[使用] simulate_fix()
    |
    v
[清理] _cleanup()
```

#### 5.2.2 沙箱目录结构

```
{temp_dir}/pyenv_doctor_{random_id}/
├── Scripts/          # Windows
│   ├── python.exe
│   ├── pip.exe
│   └── activate.bat
├── bin/              # Linux/macOS
│   ├── python
│   ├── pip
│   └── activate
├── lib/
│   └── python{version}/
│       └── site-packages/
└── pyvenv.cfg
```

#### 5.2.3 沙箱隔离策略

| 隔离维度 | 实现方式 | 说明 |
| :--- | :--- | :--- |
| 文件系统 | 临时目录 + venv | 独立的虚拟环境目录 |
| Python 解释器 | venv 内置隔离 | 独立的 site-packages |
| 环境变量 | 继承 + 覆盖 | 继承系统环境变量，覆盖 PATH |
| 网络 | 无隔离 | 可访问 PyPI |

---

### 5.3 错误处理策略

#### 5.3.1 错误分类

| 错误级别 | 说明 | 处理方式 |
| :--- | :--- | :--- |
| `CRITICAL` | 致命错误，无法继续 | 输出错误信息，退出程序 |
| `ERROR` | 模块错误，跳过该模块 | 记录日志，继续执行 |
| `WARNING` | 警告信息，不影响执行 | 输出警告，继续执行 |
| `INFO` | 信息提示 | 输出信息 |

#### 5.3.2 错误码定义

| 错误码 | 错误名称 | 说明 |
| :--- | :--- | :--- |
| `E001` | `PYTHON_VERSION_ERROR` | Python 版本不兼容 |
| `E002` | `ENV_SCAN_ERROR` | 环境扫描失败 |
| `E003` | `CONFLICT_DETECT_ERROR` | 冲突检测失败 |
| `E004` | `SANDBOX_CREATE_ERROR` | 沙箱创建失败 |
| `E005` | `SANDBOX_TIMEOUT_ERROR` | 沙箱预演超时 |
| `E006` | `PERMISSION_ERROR` | 权限不足 |
| `E007` | `NETWORK_ERROR` | 网络错误 |

---

### 5.4 性能优化策略

#### 5.4.1 性能指标

| 模块 | 性能指标 | 目标值 | 测量方法 |
| :--- | :--- | :--- | :--- |
| EnvScanner | 扫描耗时 | < 3 秒 | 100 个包环境 |
| ConflictSolver | 检测耗时 | < 1 秒 | 100 个包环境 |
| SandboxExecutor | 单次预演耗时 | < 60 秒 | 单包安装 |

#### 5.4.2 优化策略

| 优化点 | 策略 | 说明 |
| :--- | :--- | :--- |
| 包扫描 | 使用 `importlib.metadata` | 比 `pip list` 更快 |
| 冲突检测 | 构建依赖图缓存 | 避免重复解析 |
| 沙箱预演 | 并行预演 | 多个冲突并行处理（v1.1） |
| 沙箱创建 | 使用 `--without-pip` | 延迟安装 pip |

---

### 5.5 跨平台兼容性

#### 5.5.1 平台差异处理

| 平台 | 差异点 | 处理方式 |
| :--- | :--- | :--- |
| Windows | pip 路径为 `Scripts/pip.exe` | 动态检测路径 |
| Linux/macOS | pip 路径为 `bin/pip` | 动态检测路径 |
| Windows | 路径分隔符为 `\` | 使用 `pathlib.Path` |
| Linux/macOS | 路径分隔符为 `/` | 使用 `pathlib.Path` |

#### 5.5.2 路径处理规范

```python
from pathlib import Path

# 正确：使用 Path 对象
pip_path = sandbox_dir / "Scripts" / "pip.exe"

# 错误：使用字符串拼接
pip_path = sandbox_dir + "\\Scripts\\pip.exe"
```

---

## 6. 模块交互规则

### 6.1 调用顺序

```
CLI
  |
  +-- EnvScanner.scan()
  |     |
  |     +-- 返回 List[PackageInfo]
  |
  +-- ConflictSolver.detect(packages)
  |     |
  |     +-- 返回 List[Conflict]
  |
  +-- SandboxExecutor.preview(conflicts)
        |
        +-- 返回 List[SandboxResult]
```

### 6.2 数据流向

```
[用户输入] pyenv-doctor diagnose
      |
      v
[EnvScanner] --> List[PackageInfo]
      |
      v
[ConflictSolver] --> List[Conflict]
      |
      v
[SandboxExecutor] --> List[SandboxResult]
      |
      v
[用户输出] 诊断报告
```

### 6.3 接口契约

| 调用方 | 被调用方 | 入参类型 | 出参类型 | 异常处理 |
| :--- | :--- | :--- | :--- | :--- |
| CLI | EnvScanner | 无 | `List[PackageInfo]` | 捕获并输出错误 |
| CLI | ConflictSolver | `List[PackageInfo]` | `List[Conflict]` | 捕获并输出错误 |
| CLI | SandboxExecutor | `List[Conflict]` | `List[SandboxResult]` | 捕获并输出错误 |

---

## 7. 功能硬性边界

### 7.1 MVP 边界

| 功能 | 是否包含 | 说明 |
| :--- | :---: | :--- |
| 环境扫描 | 是 | 核心功能 |
| 冲突检测 | 是 | 核心功能 |
| 沙箱预演 | 是 | 核心功能 |
| 修复建议 | 是 | 核心功能 |
| 自动修复 | 否 | v1.1 功能 |
| 回滚机制 | 否 | v1.1 功能 |
| 快照管理 | 否 | v1.1 功能 |
| LLM 集成 | 否 | v1.2 功能 |
| 自然语言命令 | 否 | v1.2 功能 |

### 7.2 检测范围边界

| 检测类型 | 是否包含 | 说明 |
| :--- | :---: | :--- |
| 直接依赖冲突 | 是 | MVP 范围 |
| 传递依赖冲突 | 否 | v1.1 功能 |
| 循环依赖 | 是 | MVP 范围 |
| 缺失依赖 | 否 | v1.1 功能 |
| 过时依赖 | 否 | v1.1 功能 |

### 7.3 沙箱边界

| 操作 | 是否支持 | 说明 |
| :--- | :---: | :--- |
| pip install | 是 | 核心功能 |
| pip uninstall | 否 | v1.1 功能 |
| pip upgrade | 否 | v1.1 功能 |
| 系统依赖安装 | 否 | 不支持 |
| C 扩展编译 | 受限 | 可能失败，需提示用户 |

---

## 8. 版本兼容性

### 8.1 Python 版本兼容性

| Python 版本 | 是否支持 | 说明 |
| :--- | :---: | :--- |
| 3.8 | 是 | 最低支持版本 |
| 3.9 | 是 | 完全支持 |
| 3.10 | 是 | 完全支持 |
| 3.11 | 是 | 完全支持 |
| 3.12 | 是 | 完全支持 |
| < 3.8 | 否 | 不支持 |

### 8.2 操作系统兼容性

| 操作系统 | 是否支持 | 说明 |
| :--- | :---: | :--- |
| Windows 10/11 | 是 | 完全支持 |
| Ubuntu 20.04+ | 是 | 完全支持 |
| macOS 11+ | 是 | 完全支持 |
| 其他 Linux | 是 | 理论支持 |

---

## 9. 附录

### 9.1 术语表

| 术语 | 说明 |
| :--- | :--- |
| Agent | OpenManus 框架中的智能代理单元 |
| Tool | OpenManus 框架中的工具封装单元 |
| Sandbox | 隔离的虚拟环境，用于预演修复方案 |
| Conflict | 依赖版本冲突 |
| PEP 440 | Python 包版本号规范 |

### 9.2 参考文档

| 文档 | 链接 |
| :--- | :--- |
| PEP 440 | https://peps.python.org/pep-0440/ |
| packaging 库文档 | https://packaging.pypa.io/ |
| Click 文档 | https://click.palletsprojects.com/ |
| venv 文档 | https://docs.python.org/3/library/venv.html |

---

[spec-writer] HANDOVER: 任务完成。产出物：《SDD详细设计 v1.0》。
