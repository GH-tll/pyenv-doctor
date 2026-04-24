# PyEnv Doctor

Python 环境诊断与沙箱预演工具

## 简介

PyEnv Doctor 是一个基于 OpenManus 的环境智能诊断系统。它通过构建依赖图谱、在沙箱中预演修复方案，确保修复建议的安全性。

## 核心功能

- **环境扫描**: 扫描当前 Python 环境已安装包
- **冲突检测**: 检测依赖版本冲突
- **沙箱预演**: 在隔离环境中预演修复方案
- **修复建议**: 提供安全的修复建议

## 安装

```bash
pip install pyenv-doctor
```

## 使用方法

### 基本用法

```bash
pyenv-doctor diagnose
```

### 选项

- `--timeout, -t`: 沙箱预演超时时间（秒），默认 60
- `--verbose, -v`: 显示详细输出
- `--help, -h`: 显示帮助信息

### 示例

```bash
# 基本诊断
pyenv-doctor diagnose

# 自定义超时时间
pyenv-doctor diagnose --timeout 30

# 详细输出
pyenv-doctor diagnose --verbose
```

## 输出示例

### 无冲突

```
[SCAN] 扫描环境...
[OK] 发现 10 个包
[DIAGNOSE] 检测冲突...
[OK] 未发现冲突
```

### 有冲突

```
[SCAN] 扫描环境...
[OK] 发现 10 个包
[DIAGNOSE] 检测冲突...
[WARN] 发现 2 个冲突:
  - pandas 要求 numpy<1.24，但已安装 1.24.0
  - scipy 要求 numpy<1.23，但已安装 1.24.0
[SANDBOX] 模拟修复...
[RESULT] 修复建议:
  [OK] pip install numpy==1.23.5
  [FAIL] numpy==1.22.0: Package not found
```

## 技术架构

```
PyEnv Doctor
├── CLI (Click)
│   └── diagnose 命令
├── Agent Layer
│   ├── EnvScanner: 环境扫描 Agent
│   ├── ConflictSolver: 冲突检测 Agent
│   └── SandboxExecutor: 沙箱预演 Agent
└── Tool Layer
    ├── pip_tool: 封装 pip 命令
    └── venv_tool: 封装 venv 操作
```

## 开发

### 环境准备

```bash
# 克隆仓库
git clone https://github.com/yourusername/pyenv-doctor.git
cd pyenv-doctor

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/ -v
```

## 版本历史

### v0.1.0 (MVP)

- 环境扫描功能
- 冲突检测功能
- 沙箱预演功能
- CLI 命令入口

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
