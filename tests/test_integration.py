# -*- coding: utf-8 -*-
"""
集成测试

测试用例覆盖:
- 完整诊断流程: INT-001 至 INT-003
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyenv_doctor.agents.env_scanner import EnvScanner
from pyenv_doctor.agents.conflict_solver import ConflictSolver
from pyenv_doctor.agents.sandbox_executor import SandboxExecutor
from pyenv_doctor.models.schemas import PackageInfo, Conflict, SandboxResult


class TestIntegration:
    """集成测试类"""

    def test_full_diagnosis_flow_no_conflicts(self):
        """
        INT-001: 完整诊断流程 - 无冲突

        前置条件: 环境无冲突
        预期结果: 各 Agent 协同工作，返回空冲突列表
        """
        # STEP 1: EnvScanner 扫描环境
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_dist1 = MagicMock()
            mock_dist1.metadata = {"Name": "numpy"}
            mock_dist1.version = "1.24.0"
            mock_dist1.requires = []
            
            mock_dist2 = MagicMock()
            mock_dist2.metadata = {"Name": "pandas"}
            mock_dist2.version = "2.0.0"
            mock_dist2.requires = [MagicMock(__str__=lambda self: "numpy>=1.21")]
            
            mock_distributions.return_value = [mock_dist1, mock_dist2]
            
            scanner = EnvScanner()
            packages = scanner.scan()
            
            assert len(packages) == 2
            
            # STEP 2: ConflictSolver 检测冲突
            solver = ConflictSolver()
            conflicts = solver.detect(packages)
            
            assert len(conflicts) == 0

    def test_full_diagnosis_flow_with_conflicts(self):
        """
        INT-002: 完整诊断流程 - 有冲突

        前置条件: 环境存在冲突
        预期结果: 各 Agent 协同工作，返回冲突列表和修复建议
        """
        # STEP 1: EnvScanner 扫描环境
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_dist1 = MagicMock()
            mock_dist1.metadata = {"Name": "numpy"}
            mock_dist1.version = "1.24.0"
            mock_dist1.requires = []
            
            mock_dist2 = MagicMock()
            mock_dist2.metadata = {"Name": "pandas"}
            mock_dist2.version = "1.5.3"
            mock_dist2.requires = [MagicMock(__str__=lambda self: "numpy<1.24")]
            
            mock_distributions.return_value = [mock_dist1, mock_dist2]
            
            scanner = EnvScanner()
            packages = scanner.scan()
            
            assert len(packages) == 2
            
            # STEP 2: ConflictSolver 检测冲突
            solver = ConflictSolver()
            conflicts = solver.detect(packages)
            
            assert len(conflicts) == 1
            assert conflicts[0].package == "pandas"
            
            # STEP 3: SandboxExecutor 预演修复方案
            with patch.object(SandboxExecutor, "create_sandbox") as mock_create, \
                 patch.object(SandboxExecutor, "simulate_fix") as mock_simulate, \
                 patch.object(SandboxExecutor, "_cleanup") as mock_cleanup:
                
                mock_create.return_value = Path("/tmp/test_sandbox")
                mock_simulate.return_value = (True, "")
                
                executor = SandboxExecutor()
                results = executor.preview(conflicts)
                
                assert len(results) == 1
                assert results[0].success is True

    def test_package_with_dots_full_flow(self):
        """
        INT-003: 包名包含点号的完整流程

        前置条件: 包名包含点号（如 pdfminer.six）
        预期结果: 各 Agent 正确处理包含点号的包名
        """
        # STEP 1: EnvScanner 扫描环境
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_dist1 = MagicMock()
            mock_dist1.metadata = {"Name": "pdfminer.six"}
            mock_dist1.version = "20221105"
            mock_dist1.requires = []
            
            mock_dist2 = MagicMock()
            mock_dist2.metadata = {"Name": "ruamel.yaml"}
            mock_dist2.version = "0.17.21"
            mock_dist2.requires = [MagicMock(__str__=lambda self: "pdfminer.six>=20221105")]
            
            mock_distributions.return_value = [mock_dist1, mock_dist2]
            
            scanner = EnvScanner()
            packages = scanner.scan()
            
            assert len(packages) == 2
            assert packages[0].name == "pdfminer.six"
            assert packages[1].name == "ruamel.yaml"
            
            # STEP 2: ConflictSolver 检测冲突
            solver = ConflictSolver()
            conflicts = solver.detect(packages)
            
            # 无冲突
            assert len(conflicts) == 0

    def test_sandbox_executor_parameter_validation(self):
        """
        INT-004: SandboxExecutor 参数验证

        前置条件: 恶意构造的包名
        预期结果: 拒绝执行并返回错误
        """
        executor = SandboxExecutor()
        sandbox_dir = Path("/tmp/test")
        
        # 测试恶意包名（命令注入尝试）
        success, error = executor.simulate_fix(sandbox_dir, "numpy==1.0.0; rm -rf /")
        assert success is False
        assert "Dangerous characters" in error
        
        # 测试无效格式
        success, error = executor.simulate_fix(sandbox_dir, "invalid-format")
        assert success is False
        assert "Invalid suggestion format" in error

    def test_sandbox_cleanup_retry(self):
        """
        INT-005: 沙箱清理重试机制

        前置条件: 清理失败
        预期结果: 重试机制生效
        """
        import shutil
        
        with patch("shutil.rmtree") as mock_rmtree:
            # 模拟前两次失败，第三次成功
            mock_rmtree.side_effect = [
                Exception("Permission denied"),
                Exception("Permission denied"),
                None  # 第三次成功
            ]
            
            executor = SandboxExecutor()
            executor._cleanup(Path("/tmp/test_sandbox"))
            
            # 验证重试了 3 次
            assert mock_rmtree.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
