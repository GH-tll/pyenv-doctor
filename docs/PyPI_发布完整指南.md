# PyPI 发布完整指南

**文档版本**: v2.1  
**创建日期**: 2026-04-24  
**最后更新**: 2026-04-27  
**适用项目**: pyenv-doctor  
**当前版本**: v0.1.5（正式 PyPI）

---

## 目录

1. [环境准备](#1-环境准备)
2. [构建分发包](#2-构建分发包)
3. [重新构建分发包](#3-重新构建分发包)
4. [PyPI 账号注册与 Token 创建](#4-pypi-账号注册与-token-创建)
5. [正式环境发布 (PyPI)](#5-正式环境发布-pypi)
6. [安装与验证](#6-安装与验证)
7. [常见问题排查](#7-常见问题排查)
8. [快速命令参考](#8-快速命令参考)
9. [版本发布流程清单](#9-版本发布流程清单)

---

## 1. 环境准备

### 1.1 安装必需工具

```powershell
# 方式 1：全局安装（系统 Python 环境）
pip install build twine

# 方式 2：虚拟环境安装（推荐）
python -m venv .venv
.venv\Scripts\activate
pip install build twine

# 方式 3：安装项目所有依赖（含开发工具）
pip install -e ".[dev]"
```

### 1.2 验证安装

```powershell
# 检查版本
python -m build --version
twine --version
```

### 1.3 项目目录结构

```powershell
pyenv-doctor/
├── pyproject.toml          # 项目配置（版本号在此处修改）
├── README.md               # 项目说明
├── LICENSE                 # 许可证
├── CHANGELOG.md            # 版本变更日志
├── src/
│   └── pyenv_doctor/       # 源代码
│       ├── __init__.py
│       ├── cli.py          # CLI 入口
│       └── ...
├── tests/                  # 测试代码
├── build/                  # 构建临时目录
├── dist/                   # 分发包输出目录
│   ├── pyenv_doctor-0.1.5-py3-none-any.whl
│   └── pyenv_doctor-0.1.5.tar.gz
└── docs/                   # 文档目录
```

---

## 2. 构建分发包（首次）

### 2.1 进入项目目录

```powershell
cd pyenv-doctor
```

### 2.2 修改版本号（如需）

编辑 `pyproject.toml`：

```toml
[project]
name = "pyenv-doctor-tool"
version = "0.1.5"  # 修改此版本号
```

同步修改 `src/pyenv_doctor/cli.py` 中的版本号：

```python
@cli.command()
@click.version_option(version="0.1.5", prog_name="pyenv-doctor")
```

### 2.3 执行构建

```powershell
python -m build
```

**构建产物**（位于 `dist/` 目录）：
- `pyenv_doctor-x.x.x-py3-none-any.whl` - Wheel 包
- `pyenv_doctor-x.x.x.tar.gz` - 源码包

### 2.4 检查分发包

```powershell
# 基本检查
twine check dist\*

# 严格检查（推荐）
twine check --strict dist\*
```

**预期输出**：
```
Checking dist\pyenv_doctor-0.1.5-py3-none-any.whl: PASSED
Checking dist\pyenv_doctor-0.1.5.tar.gz: PASSED
```

### 2.5 验证分发包内容

```powershell
# 查看 wheel 包内容
python -m zipfile -l dist\pyenv_doctor-0.1.5-py3-none-any.whl

# 查看源码包内容
python -m zipfile -l dist\pyenv_doctor-0.1.5.tar.gz
```

---

## 3. 重新构建分发包

### 3.1 何时需要重新构建

| 场景 | 说明 |
|:---|:---|
| 代码更新后 | 修改了源代码，需要同步到分发包 |
| 配置更新后 | 修改了 `pyproject.toml`、`README.md` 等 |
| 版本号更新后 | 增加了版本号，需要构建新版本 |
| 分发包损坏 | 构建过程中出现错误 |
| 发现旧包问题 | 如入口点配置错误、缺少文件等 |

### 3.2 清理旧构建

```powershell
# 删除构建目录
Remove-Item build\ -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item dist\ -Recurse -Force -ErrorAction SilentlyContinue

# 删除 egg-info（可选）
Remove-Item src\pyenv_doctor.egg-info\ -Recurse -Force -ErrorAction SilentlyContinue
```

### 3.3 重新构建

```powershell
# 确保在项目目录
cd pyenv-doctor

# 执行构建
python -m build
```

### 3.4 验证新构建

```powershell
# 检查分发包
twine check dist\*

# 查看文件大小和修改时间
Get-ChildItem dist\ | Select-Object Name, LastWriteTime, Length

# 验证关键文件是否包含（如 cli.py）
python -m zipfile -l dist\pyenv_doctor-x.x.x-py3-none-any.whl | Select-String "cli"
```

---

## 4. PyPI 账号注册与 Token 创建

### 4.1 正式 PyPI

#### 注册账号

1. 访问：https://pypi.org/account/register/
2. 填写用户名、邮箱、密码
3. 验证邮箱

#### 创建 Token

1. 登录后访问：https://pypi.org/manage/account/token/
2. 点击 **"Add API token"**
3. 填写信息：
   - **Token name**: 如 `pyenv-doctor-publish`
   - **Scope**: 
     - 首次发布：选择 `Entire account`
     - 后续更新：选择 `Project: pyenv-doctor-tool`
4. 点击 **"Create token"**
5. **重要**：立即复制 Token（格式 `pypi-...`，仅显示一次）

### 4.2 Token 重要说明

| 项目 | 说明 |
|:---|:---|
| **网址** | https://pypi.org |
| **Token 格式** | `pypi-...` |
| **用途** | 正式发布到 PyPI |
| **包名冲突** | 不允许（包名全局唯一） |

**安全提醒**：
- Token 不可逆向获取，丢失需重新创建
- 不要提交到 Git 仓库（已加入 `.gitignore`）
- 定期轮换 Token（建议 90 天）
- 使用最小权限原则

---

## 5. 正式环境发布 (PyPI)

### 5.1 前置条件

- [ ] 功能验证完整
- [ ] README 最终版确认
- [ ] 版本号确认（发布后不可删除）
- [ ] 分发包检查通过

### 5.2 完整发布流程

```powershell
# 步骤 1：进入项目目录
cd pyenv-doctor

# 步骤 2：上传到 PyPI
twine upload -u __token__ -p "你的正式 PyPI_Token" dist\*
```

**参数说明**：
- `-u __token__`：固定值，不要修改
- `-p`：完整的 Token（包含 `pypi-` 前缀）
- `dist\*`：匹配所有分发包

### 5.3 预期输出

```
Uploading distributions to https://upload.pypi.org/legacy/
Uploading pyenv_doctor-0.1.5-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 14.6/14.6 kB • 00:00 • ?
Uploading pyenv_doctor-0.1.5.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 19.1/19.1 kB • 00:00 • ?

View at:
https://pypi.org/project/pyenv-doctor-tool/0.1.5/
```

### 5.4 查看项目页面

访问：https://pypi.org/project/pyenv-doctor-tool/

检查：
- [ ] 项目名称正确
- [ ] 版本号正确
- [ ] 描述信息完整
- [ ] README 渲染正常
- [ ] 依赖列表正确

---

## 6. 安装与验证

### 6.1 从正式 PyPI 安装

```powershell
# 创建新虚拟环境
python -m venv prod_env
prod_env\Scripts\activate

# 安装正式版
pip install pyenv-doctor-tool
```

### 6.2 版本验证

```powershell
# 查看版本
pyenv-doctor --version

# 查看已安装版本信息
pip show pyenv-doctor-tool
```

**预期输出**：
```
pyenv-doctor-tool, version 0.1.5
```

### 6.3 功能验证

```powershell
# 查看帮助
pyenv-doctor --help

# 基本诊断
pyenv-doctor diagnose

# 快速模式（推荐）
pyenv-doctor diagnose --fast

# 自动修复
pyenv-doctor diagnose --fix

# 详细输出
pyenv-doctor diagnose --verbose
```

### 6.4 依赖验证

```powershell
# 查看依赖树
pip list

# 检查依赖是否完整
pip check
```

### 6.5 卸载

```powershell
# 卸载当前版本
pip uninstall pyenv-doctor-tool

# 卸载并清理缓存
pip uninstall pyenv-doctor-tool -y
pip cache purge
```

---

## 7. 常见问题排查

### 7.1 build 模块缺失

**症状**：
```
No module named build
```

**解决**：
```powershell
pip install build
```

### 7.2 twine 模块缺失

**症状**：
```
twine : 无法将"twine"项识别为 cmdlet
```

**解决**：
```powershell
pip install twine
```

### 7.3 分发包不存在

**症状**：
```
Cannot find file (or expand pattern): 'dist\*'
```

**解决**：
```powershell
# 先构建
python -m build

# 再检查
twine check dist\*
```

### 7.4 Token 无效

**症状**：
```
ERROR    HTTPError: 403 Invalid API token
```

**检查清单**：
- [ ] Token 是否正确（包含完整 `pypi-` 前缀）
- [ ] Token 是否已过期或被撤销
- [ ] 项目名是否在 Token 权限范围内

### 7.5 包名已被占用

**症状**：
```
ERROR    HTTPError: 409 Conflict
```

**解决**：
- 修改 `pyproject.toml` 中的 `name` 字段
- 在 PyPI 搜索确认名称可用性

### 7.6 版本已存在

**症状**：
```
ERROR    HTTPError: 400 File already exists
```

**解决**：
- 增加版本号（如 `0.1.4` → `0.1.5`）
- 修改 `pyproject.toml` 中的 `version` 字段
- 修改 `cli.py` 中的 `version` 字段
- 重新构建：`python -m build`
- 重新上传

### 7.7 网络问题

**症状**：连接超时或 SSL 错误

**解决**：
```powershell
# 使用国内镜像
pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple pyenv-doctor-tool

# 设置超时时间
twine upload --timeout 300 dist\*
```

---

## 8. 快速命令参考

### 8.1 环境准备

```powershell
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装开发工具
pip install -e ".[dev]"

# 验证工具
python -m build --version
twine --version
```

### 8.2 构建

```powershell
# 进入项目目录
cd pyenv-doctor

# 清理旧构建
Remove-Item build\ -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item dist\ -Recurse -Force -ErrorAction SilentlyContinue

# 构建
python -m build

# 检查
twine check dist\*
```

### 8.3 正式发布

```powershell
# 上传到 PyPI
twine upload -u __token__ -p "正式 PyPI_Token" dist\*

# 安装正式版
pip uninstall pyenv-doctor-tool -y
pip install pyenv-doctor-tool

# 验证
pyenv-doctor --version
pyenv-doctor diagnose
```

### 8.4 版本管理

```powershell
# 查看已安装版本
pip show pyenv-doctor-tool

# 卸载
pip uninstall pyenv-doctor-tool

# 指定版本安装
pip install pyenv-doctor-tool==0.1.5

# 查看可用版本
pip index versions pyenv-doctor-tool
```

### 8.5 Git 操作

```powershell
# 查看当前版本
git describe --tags

# 打 Tag
git tag v0.1.5
git push origin v0.1.5

# 删除本地 Tag
git tag -d v0.1.5

# 删除远程 Tag
git push origin --delete v0.1.5
```

---

## 9. 版本发布流程清单

### 9.1 发布前检查

- [ ] 代码审查完成
- [ ] 所有测试通过 (`pytest tests/`)
- [ ] 测试覆盖率达标（> 80%）
- [ ] 文档更新完成
- [ ] CHANGELOG.md 更新
- [ ] 版本号已更新（`pyproject.toml` + `cli.py`）
- [ ] pyproject.toml 元数据正确
- [ ] README.md 最终版确认
- [ ] 构建工具已安装 (`pip install -e ".[dev]"`)

### 9.2 构建与检查

- [ ] 清理旧构建文件
- [ ] 执行 `python -m build`
- [ ] 检查分发包 `twine check dist\*`
- [ ] 验证分发包内容包含关键文件

### 9.3 正式发布

- [ ] 执行正式上传
- [ ] 网页验证发布成功
- [ ] 从 PyPI 安装验证
- [ ] Git Tag 已创建
- [ ] GitHub Release 已创建

### 9.4 发布后

- [ ] 版本号递增（准备下一版本）
- [ ] 通知相关用户
- [ ] 更新项目文档
- [ ] 记录 Token 信息

---

## 附录

### A. pyproject.toml 关键字段

```toml
[project]
name = "pyenv-doctor-tool"
version = "0.1.5"
description = "Python environment diagnosis and sandbox preview tool"
requires-python = ">=3.8"

[project.scripts]
pyenv-doctor = "pyenv_doctor.cli:main"
```

### B. 版本号规范

遵循 [语义化版本](https://semver.org/)：

| 类型 | 格式 | 说明 | 示例 |
|:---|:---|:---|:---|
| 主版本 | `x.0.0` | 不兼容的 API 修改 | `1.0.0` |
| 次版本 | `0.x.0` | 向下兼容的功能新增 | `0.2.0` |
| 修订号 | `0.0.x` | 向下兼容的问题修正 | `0.1.5` |

### C. 分发包类型

| 类型 | 扩展名 | 说明 |
|:---|:---|:---|
| Wheel | `.whl` | 预编译包，安装快 |
| Source | `.tar.gz` | 源码包，兼容性好 |

### D. 相关资源

| 资源 | 链接 |
|:---|:---|
| PyPI 官网 | https://pypi.org |
| twine 文档 | https://twine.readthedocs.io/ |
| packaging 指南 | https://packaging.python.org/ |
| 语义化版本 | https://semver.org/ |
| setuptools 文档 | https://setuptools.pypa.io/ |

---

**最后更新**: 2026-04-27  
**维护者**: PyEnv Doctor Team  
**当前版本**: v0.1.5（正式 PyPI）
