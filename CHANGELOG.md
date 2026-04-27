# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
