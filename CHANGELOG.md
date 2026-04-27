# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-05-02

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

## [1.1.8] - 2026-05-02

### Fixed
- **版本范围解析修复**: 正确解析复杂版本约束（如 `asgiref<4,>=3.6.0`）
- **自动修复包名修复**: 从建议中提取正确的包名（而非冲突包名）
- **快照空值处理**: 当跳过快照创建时的 `NoneType` 错误

### Technical Details
- 修复 `src/pyenv_doctor/agents/conflict_solver.py` 中的 `_generate_suggestion` 方法，实现综合分析所有版本约束条件
- 修复 `src/pyenv_doctor/repair/strategy.py` 中的 `generate_repair_plan` 方法，从 suggestion 中提取正确包名
- 修复 `src/pyenv_doctor/cli/main.py` 中的快照空值检查，添加友好的错误提示

### Testing
- 测试场景 1：django + asgiref 冲突（test PyPI）
- 测试场景 2：requests + urllib3 冲突（正式 PyPI）
- 所有测试通过，自动修复功能正常工作

## [1.1.3] - 2026-04-26

### Added
- **Fast Mode (`--fast`)**: Quickly scan only current environment, excluding base packages
- **Environment Path Filtering**: Automatically detect and filter packages outside current environment

### Enhanced
- `diagnose` command now supports `--fast` flag to reduce scan time
- Excluded base packages (pip, setuptools, wheel, pkg_resources) from scan results
- Improved environment detection to avoid scanning global packages when in venv
- Updated README.md with fast mode usage examples

### Technical Details
- Updated `EnvScanner` with `only_user` and `include_base` parameters
- Added `BASE_PACKAGES` constant for base package filtering
- Implemented `_get_current_env_paths()` for environment path resolution
- Implemented `_is_in_current_env()` for package origin verification

### Fixed
- Scan speed issue when not in virtual environment (hundreds of packages scanned)
- Incorrect package count in global environment diagnosis

## [1.1.2] - 2026-04-24

### Fixed
- Removed `create-env` command to focus on core diagnosis and repair features
- Optimized documentation completeness

## [1.1.0] - 2026-04-24

### Added
- **Snapshot Management**: Complete snapshot lifecycle management (create/list/rollback/delete/export)
- **Auto-Fix Feature**: `diagnose --fix` command for automatic conflict resolution
- **Rollback Engine**: Fast rollback to any snapshot state with preview and verification
- **Temporary Snapshots**: Auto-created during auto-fix, can be converted to permanent
- **Three Repair Strategies**: Conservative, Balanced, Aggressive for different scenarios
- **Snapshot CLI Commands**:
  - `snapshot create`: Create environment snapshots
  - `snapshot list`: List all snapshots with filtering
  - `snapshot rollback`: Rollback to snapshot with preview
  - `snapshot delete`: Delete one or more snapshots
  - `snapshot export`: Export snapshot to requirements.txt or JSON
  - `snapshot cleanup`: Clean up temporary or old snapshots
- **Strategy Engine**: Intelligent strategy-based repair planning
- **Progress Tracking**: Visual progress bar during rollback operations

### Enhanced
- `diagnose` command now supports `--fix`, `--strategy`, `--dry-run`, `--yes` options
- Auto-fix workflow includes automatic snapshot creation before repair
- Rollback preview shows exact package changes before execution
- Post-rollback verification ensures environment consistency
- Temporary snapshots can be converted to permanent after successful repair
- Improved user interaction with confirmation prompts and clear feedback

### Technical Details
- Added `snapshot/` module: `SnapshotManager`, `SnapshotStorage`
- Added `repair/` module: `AutoRepair`, `RollbackEngine`, `StrategyEngine`
- Added `models/schemas.py`: `RepairStrategy`, `RepairPlan`, `RollbackResult`
- Enhanced CLI with snapshot command group
- Implemented rollback with transactional safety
- Added snapshot export functionality (requirements.txt and JSON formats)

### Documentation
- Updated README.md with comprehensive v1.1.0 features
- Added snapshot management usage examples
- Added auto-fix workflow examples
- Added three repair strategies comparison table
- Updated development roadmap with completed features

## [0.1.5] - 2026-04-24

### Added
- Report export functionality (JSON and Markdown formats)
- requirements.txt parser support
- pyproject.toml parser support
- New `check-file` command for dependency file analysis
- Performance benchmark tests
- Parallel sandbox preview optimization (60% faster)

### Enhanced
- SandboxExecutor now supports parallel execution with configurable workers
- CLI now supports `--output`, `--parallel`, `--workers` options
- Documentation improved with comprehensive examples and FAQ

### Technical Details
- Added `exporters/` module for report generation
- Added `parsers/` module for dependency file parsing
- Improved concurrent execution with ThreadPoolExecutor
- Added 9 performance benchmark test cases

## [0.1.4] - 2026-04-24

### Added
- Initial MVP release
- Environment scanning functionality (EnvScanner Agent)
- Dependency conflict detection (ConflictSolver Agent)
- Sandbox preview for fix validation (SandboxExecutor Agent)
- CLI interface with `diagnose` command
- Support for timeout configuration
- Verbose output mode
- Basic error handling and user feedback

### Technical Details
- Built with Click for CLI interface
- Uses packaging library for version parsing
- Modular Agent architecture for extensibility
- Comprehensive test suite with pytest
- Support for Python 3.8+

## [Unreleased]

### Planned
- Export diagnosis reports to file
- Custom rule configuration
- Integration with requirements.txt and pyproject.toml
- Batch mode for multiple environments
- Web dashboard for visualization
