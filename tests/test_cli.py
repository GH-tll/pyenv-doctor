# -*- coding: utf-8 -*-
"""
CLI 模块单元测试

测试用例覆盖:
- 功能测试：CLI-001 至 CLI-004
- 边界测试：CLI-B01 至 CLI-B02
- 异常测试：CLI-E01 至 CLI-E02
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from importlib.metadata import version

import pytest
from click.testing import CliRunner

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyenv_doctor.cli.main import main
from pyenv_doctor.models.schemas import PackageInfo, Conflict

# 动态获取当前版本号
CURRENT_VERSION = version("pyenv-doctor-tool")


class TestCLI:
    """CLI 测试类"""

    def test_cli_version(self):
        """
        CLI-001: 版本信息显示

        前置条件：无
        预期结果：显示版本号
        """
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert CURRENT_VERSION in result.output

    def test_cli_help(self):
        """
        CLI-002: 帮助信息显示

        前置条件: 无
        预期结果: 显示帮助信息
        """
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "PyEnv Doctor" in result.output

    def test_cli_no_conflicts(self):
        """
        CLI-003: 无冲突环境

        前置条件：环境无冲突
        预期结果：显示未发现冲突
        """
        with patch("pyenv_doctor.cli.main.EnvScanner") as mock_scanner_cls, \
             patch("pyenv_doctor.cli.main.ConflictSolver") as mock_solver_cls:
            
            # 模拟 EnvScanner
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = [
                PackageInfo(name="numpy", version="1.24.0", requires=[]),
                PackageInfo(name="pandas", version="2.0.0", requires=["numpy>=1.21"])
            ]
            mock_scanner_cls.return_value = mock_scanner
            
            # 模拟 ConflictSolver
            mock_solver = MagicMock()
            mock_solver.detect.return_value = []
            mock_solver_cls.return_value = mock_solver
            
            runner = CliRunner()
            result = runner.invoke(main, ['diagnose'])
            
            assert result.exit_code == 0
            assert "未发现冲突" in result.output

    def test_cli_with_conflicts(self):
        """
        CLI-004: 有冲突环境

        前置条件：环境存在冲突
        预期结果：显示冲突和修复建议
        """
        with patch("pyenv_doctor.cli.main.EnvScanner") as mock_scanner_cls, \
             patch("pyenv_doctor.cli.main.ConflictSolver") as mock_solver_cls, \
             patch("pyenv_doctor.cli.main.SandboxExecutor") as mock_executor_cls:
            
            # 模拟 EnvScanner
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = [
                PackageInfo(name="numpy", version="1.24.0", requires=[]),
                PackageInfo(name="pandas", version="1.5.3", requires=["numpy<1.24"])
            ]
            mock_scanner_cls.return_value = mock_scanner
            
            # 模拟 ConflictSolver
            mock_solver = MagicMock()
            mock_solver.detect.return_value = [
                Conflict(
                    package="pandas",
                    requires="numpy<1.24",
                    installed="1.24.0",
                    suggestion="numpy==1.23.0"
                )
            ]
            mock_solver_cls.return_value = mock_solver
            
            # 模拟 SandboxExecutor
            from pyenv_doctor.models.schemas import SandboxResult
            mock_executor = MagicMock()
            mock_executor.preview.return_value = [
                SandboxResult(scheme="numpy==1.23.0", success=True, error=None)
            ]
            mock_executor_cls.return_value = mock_executor
            
            runner = CliRunner()
            result = runner.invoke(main, ['diagnose'])
            
            assert result.exit_code == 0
            assert "发现 1 个冲突" in result.output

    def test_cli_verbose_mode(self):
        """
        CLI-B01: 详细输出模式

        前置条件：无
        预期结果：正常执行
        """
        with patch("pyenv_doctor.cli.main.EnvScanner") as mock_scanner_cls, \
             patch("pyenv_doctor.cli.main.ConflictSolver") as mock_solver_cls:
            
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = []
            mock_scanner_cls.return_value = mock_scanner
            
            mock_solver = MagicMock()
            mock_solver.detect.return_value = []
            mock_solver_cls.return_value = mock_solver
            
            runner = CliRunner()
            result = runner.invoke(main, ['diagnose', "--verbose"])
            
            assert result.exit_code == 0

    def test_cli_custom_timeout(self):
        """
        CLI-B02: 自定义超时时间

        前置条件：有冲突（需要调用 SandboxExecutor）
        预期结果：正常执行，超时参数正确传递
        """
        with patch("pyenv_doctor.cli.main.EnvScanner") as mock_scanner_cls, \
             patch("pyenv_doctor.cli.main.ConflictSolver") as mock_solver_cls, \
             patch("pyenv_doctor.cli.main.SandboxExecutor") as mock_executor_cls:
            
            mock_scanner = MagicMock()
            mock_scanner.scan.return_value = [
                PackageInfo(name="numpy", version="1.24.0", requires=[]),
                PackageInfo(name="pandas", version="1.5.3", requires=["numpy<1.24"])
            ]
            mock_scanner_cls.return_value = mock_scanner
            
            mock_solver = MagicMock()
            mock_solver.detect.return_value = [
                Conflict(
                    package="pandas",
                    requires="numpy<1.24",
                    installed="1.24.0",
                    suggestion="numpy==1.23.0"
                )
            ]
            mock_solver_cls.return_value = mock_solver
            
            from pyenv_doctor.models.schemas import SandboxResult
            mock_executor = MagicMock()
            mock_executor.preview.return_value = [
                SandboxResult(scheme="numpy==1.23.0", success=True, error=None)
            ]
            mock_executor_cls.return_value = mock_executor
            
            runner = CliRunner()
            result = runner.invoke(main, ['diagnose', "--timeout", "120"])
            
            assert result.exit_code == 0
            # 验证超时参数传递
            mock_executor_cls.assert_called_once_with(timeout=120)

    def test_cli_permission_error(self):
        """
        CLI-E01: 权限不足

        前置条件：无读取权限
        预期结果：显示错误信息并退出
        """
        with patch("pyenv_doctor.cli.main.EnvScanner") as mock_scanner_cls:
            mock_scanner = MagicMock()
            mock_scanner.scan.side_effect = PermissionError("Permission denied")
            mock_scanner_cls.return_value = mock_scanner
            
            runner = CliRunner()
            result = runner.invoke(main, ['diagnose'])
            
            assert result.exit_code == 1
            assert "权限不足" in result.output

    def test_cli_scan_error(self):
        """
        CLI-E02: 扫描失败

        前置条件：扫描过程异常
        预期结果：显示错误信息并退出
        """
        with patch("pyenv_doctor.cli.main.EnvScanner") as mock_scanner_cls:
            mock_scanner = MagicMock()
            mock_scanner.scan.side_effect = Exception("Scan failed")
            mock_scanner_cls.return_value = mock_scanner
            
            runner = CliRunner()
            result = runner.invoke(main, ['diagnose'])
            
            assert result.exit_code == 1
            assert "扫描失败" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
