# docs 目录结构说明

**更新日期**: 2026-04-24  
**公开策略**: 根目录文档公开，其他禁止公开

---

## 📁 当前目录结构

```
docs/
├── PyPI/                          # 🔒 禁止公开（敏感信息）
│   ├── PyPI-Recovery-Codes-*.txt  # PyPI 账号恢复代码
│   └── TestPyPI-Recovery-Codes-*.txt  # TestPyPI 账号恢复代码
│
├── prd_bak/                       # 🔒 禁止公开（历史版本）
│   ├── PyEnv_Doctor_PRD_v2.0.md
│   ├── PyEnv_Doctor_PRD_v3.0.md
│   └── PyEnv_Doctor_PRD_v3.1.md
│
├── PyEnv_Doctor_PRD_v3.1.md       # ✅ 公开（产品文档）
├── PyEnv_Doctor_SDD_v1.0.md       # ✅ 公开（设计文档）
├── 2026-04-24-终验审计报告.md     # ✅ 公开（验收报告）
├── PyPI_发布完整指南.md           # ✅ 公开（发布教程）
└── README.md                      # ✅ 公开（本说明文档）
```

---

## 🔒 禁止公开的内容

### 1. PyPI/ 目录

| 文件 | 原因 | 风险等级 |
|:---|:---|:---:|
| `PyPI-Recovery-Codes-*.txt` | 包含 PyPI 账号恢复代码 | 🔴 **高危** |
| `TestPyPI-Recovery-Codes-*.txt` | 包含 TestPyPI 账号恢复代码 | 🔴 **高危** |

**说明**：
- 恢复代码用于账号紧急恢复，泄露可能导致账号被盗
- `.gitignore` 已配置：`docs/PyPI/*.txt` 和 `*-Recovery-Codes-*.txt`
- **PyPI_发布完整指南.md** 在根目录，可以公开

### 2. prd_bak/ 目录

| 文件 | 原因 |
|:---|:---|
| `prd_bak/*.md` | 历史版本文档，不公开 |

---

## ✅ 建议公开的内容（docs 根目录）

### 技术文档（核心价值）

| 文件 | 类型 | 价值 | 说明 |
|:---|:---|:---|:---|
| `PyEnv_Doctor_PRD_v3.1.md` | 产品需求文档 | ⭐⭐⭐⭐⭐ | 最终版产品规划 |
| `PyEnv_Doctor_SDD_v1.0.md` | 系统设计文档 | ⭐⭐⭐⭐⭐ | 技术架构设计 |
| `2026-04-24-终验审计报告.md` | 验收报告 | ⭐⭐⭐⭐ | 质量审计报告 |
| `PyPI/PyPI_发布完整指南.md` | 发布指南 | ⭐⭐⭐⭐ | PyPI 发布教程 |
| `README.md` | 目录说明 | ⭐⭐⭐ | 本说明文档 |

---

## 📋 .gitignore 配置

```gitignore
# 禁止公开
docs/PyPI/*.txt              # PyPI 恢复代码
*-Recovery-Codes-*.txt       # 所有恢复代码文件
.pypirc                      # Token 配置
.pypirc.template             # Token 模板
docs/prd_bak/                # 历史版 PRD

# 允许公开（docs 根目录）
docs/*.md                    # 根目录 Markdown 文档
```

---

## 🎯 公开策略原则

### 公开原则

**根目录优先**：
- ✅ docs 根目录下的文档默认公开
- ✅ 展示项目核心价值（PRD、SDD、审计报告）
- ✅ 提供实用技术参考（发布指南）

### 禁止原则

**子目录隔离**：
- ❌ `docs/PyPI/*.txt` - 恢复代码
- ❌ `docs/prd_bak/` - 历史版本
- ❌ 个人敏感信息

---

## 📝 最佳实践

### ✅ 推荐做法

- 将需要公开的文档放在 `docs/` 根目录
- 使用清晰的命名：`日期 - 主题.md` 或 `项目_文档类型_v 版本.md`
- 敏感信息放入子目录并配置 `.gitignore`
- 定期更新 `docs/README.md` 说明文档结构

### ❌ 避免做法

- 将恢复代码、Token 等写入 `.md` 文档
- 在公开文档中提及个人账号信息
- 将历史版本与最终版本混放

---

## 🔄 目录调整历史

| 日期 | 操作 | 说明 |
|:---|:---|:---|
| 2026-04-24 | 整理 docs 目录 | 明确公开策略 |
| 2026-04-24 | 分离敏感信息 | PyPI/ 目录禁止公开 |
| 2026-04-24 | 禁止历史版本 | prd_bak/ 禁止公开 |
| 2026-04-24 | 更新 .gitignore | 配置公开规则 |

---

## 📂 快速参考

### 要公开新文档

```bash
# 1. 将文档放在 docs/ 根目录
cp 新文档.md docs/

# 2. 确认 .gitignore 未禁止
git status

# 3. 提交
git add docs/新文档.md
git commit -m "docs: 添加新文档"
```

### 要禁止敏感文件

```bash
# 1. 放入对应子目录
mv 敏感文件.md docs/PyPI/

# 2. 或创建新的子目录
mkdir docs/private/
mv 私人文档.md docs/private/

# 3. 更新 .gitignore（如需要）
echo "docs/private/" >> .gitignore
```

---

**维护者**: PyEnv Doctor Team  
**最后更新**: 2026-04-24
