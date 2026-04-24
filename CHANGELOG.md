# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-24

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
