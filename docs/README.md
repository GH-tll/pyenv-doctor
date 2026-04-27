# docs 目录说明

**更新日期**: 2026-04-27  
**公开策略**: docs 根目录文档默认公开

---

## 📁 当前目录结构

```
docs/
├── PyEnv_Doctor_PRD_v1.2.md       # ✅ 产品需求文档（最新版）
├── PyEnv_Doctor_SDD_v1.1.md       # ✅ 系统设计文档（最新版）
├── PyPI_发布完整指南.md           # ✅ PyPI 发布教程
├── README.md                      # ✅ 本说明文档
└── 目录结构说明.md                # ✅ 项目目录结构说明
```

---

## ✅ 公开文档列表

| 文件 | 类型 | 说明 |
|:---|:---|:---|
| `PyEnv_Doctor_PRD_v1.2.md` | 产品需求文档 | 最终版产品规划（v1.2） |
| `PyEnv_Doctor_SDD_v1.1.md` | 系统设计文档 | 技术架构设计（v1.1） |
| `PyPI_发布完整指南.md` | 发布指南 | PyPI 发布完整教程 |
| `README.md` | 目录说明 | 本文档 |
| `目录结构说明.md` | 结构说明 | 项目目录结构说明 |

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

## 🎯 公开策略

### 公开原则
- ✅ docs 根目录下的文档默认公开
- ✅ 只保留最新版本文档（PRD v1.2、SDD v1.1）
- ✅ 提供实用技术参考（发布指南、目录说明）

### 禁止原则
- ❌ `docs/PyPI/*.txt` - 恢复代码
- ❌ `docs/prd_bak/` - 历史版本
- ❌ 个人敏感信息

---

## 📝 文档管理

### 添加新文档
```bash
# 1. 将文档放在 docs/ 根目录
cp 新文档.md docs/

# 2. 提交
git add docs/新文档.md
git commit -m "docs: 添加新文档"
```

### 版本文档更新
- 更新版本文档时，保留最新版（如 PRD v1.2）
- 旧版本移至 `docs/prd_bak/` 目录（不提交）
- 保持 docs 目录简洁，只保留最新版本

---

**维护者**: PyEnv Doctor Team  
**最后更新**: 2026-04-27  
**当前版本**: v0.1.5（正式 PyPI）
