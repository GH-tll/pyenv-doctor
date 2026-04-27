# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-04-27

### Added
- **正式发布到 PyPI**: v0.1.5 已发布到正式 PyPI
- **完整的依赖冲突自动修复**:
  - 智能诊断依赖冲突
  - 沙箱预演修复方案
  - 自动执行修复命令
  - 修复后自动验证
- **版本范围解析修复**: 正确解析复杂版本约束（如 `<4,>=3.6.0`）
- **自动修复包名修复**: 从建议中提取正确的包名进行修复
- **错误处理优化**: 快照为空时的友好提示

### Fixed
- 版本范围解析错误：将 `asgiref<4,>=3.6.0` 错误解析为 `asgiref==4`
- 自动修复包名错误：使用冲突包名而非依赖包名
- 快照空引用错误：当跳过快照创建时的 `NoneType` 错误

### Technical Details
- 修复 `conflict_solver.py` 中的 `_generate_suggestion` 方法
- 修复 `strategy.py` 中的 `generate_repair_plan` 方法
- 修复 `main.py` 中的快照空值检查

### Testing
- 测试场景 1：django + asgiref 冲突（test PyPI）
- 测试场景 2：requests + urllib3 冲突（正式 PyPI）
- 所有测试通过，自动修复功能正常工作
