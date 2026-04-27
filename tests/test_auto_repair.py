# -*- coding: utf-8 -*-
"""
测试自动修复执行器

覆盖场景:
- 一键修复流程
- 沙箱预演
- 执行修复
- 验证结果
- 用户取消
- 失败处理
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from pyenv_doctor.models.schemas import Conflict, RepairStrategy
from pyenv_doctor.repair.auto_repair import AutoRepair


class TestAutoRepair:
    """测试 AutoRepair 类"""

    @pytest.fixture
    def mock_sandbox(self):
        """模拟沙箱执行器"""
        mock = MagicMock()
        mock.preview.return_value = []
        return mock

    @pytest.fixture
    def mock_strategy_engine(self):
        """模拟策略引擎"""
        mock = MagicMock()
        mock.generate_plans.return_value = []
        return mock

    def test_init_default(self):
        """测试默认初始化"""
        repair = AutoRepair()
        assert repair.strategy == RepairStrategy.BALANCED
        assert repair.dry_run is False
        assert repair.timeout == 60

    def test_init_custom(self):
        """测试自定义初始化"""
        repair = AutoRepair(
            strategy=RepairStrategy.CONSERVATIVE,
            dry_run=True,
            timeout=30,
        )
        assert repair.strategy == RepairStrategy.CONSERVATIVE
        assert repair.dry_run is True
        assert repair.timeout == 30

    def test_execute_no_conflicts(self):
        """测试无冲突时执行"""
        repair = AutoRepair()
        
        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = []
            
            result = repair.execute([], {})
            
            assert result.success is True
            assert result.repaired == []
            assert result.failed == []

    def test_execute_with_conflicts(self):
        """测试有冲突时执行"""
        repair = AutoRepair()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        # Mock 策略引擎生成方案
        from pyenv_doctor.models.schemas import RepairPlan
        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="pandas requires <1.24",
            )
        ]

        # Mock 沙箱预演成功
        from pyenv_doctor.models.schemas import SandboxResult
        preview_results = [
            SandboxResult(
                scheme="numpy==1.23.5",
                success=True,
                error=None,
            )
        ]

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                with patch.object(repair, '_execute_plan', return_value=True):
                    result = repair.execute(conflicts, {"numpy": "1.24.0"})

        assert result.success is True
        assert len(result.repaired) == 1
        assert "numpy" in result.repaired
        assert result.failed == []

    def test_execute_dry_run(self):
        """测试预演模式"""
        repair = AutoRepair(dry_run=True)

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        from pyenv_doctor.models.schemas import RepairPlan, SandboxResult

        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="test",
            )
        ]

        preview_results = [
            SandboxResult(
                scheme="numpy==1.23.5",
                success=True,
                error=None,
            )
        ]

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                # 预演模式不应调用 _execute_plan
                with patch.object(repair, '_execute_plan') as mock_execute:
                    result = repair.execute(conflicts, {"numpy": "1.24.0"})

        # 预演模式下不实际执行
        mock_execute.assert_not_called()
        assert result.success is True

    def test_execute_preview_failed(self):
        """测试预演失败"""
        repair = AutoRepair()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        from pyenv_doctor.models.schemas import RepairPlan, SandboxResult

        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="test",
            )
        ]

        # 预演失败
        preview_results = [
            SandboxResult(
                scheme="numpy==1.23.5",
                success=False,
                error="Installation failed",
            )
        ]

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                result = repair.execute(conflicts, {"numpy": "1.24.0"})

        # 预演失败，修复应该失败
        assert result.success is False
        assert result.repaired == []
        assert "numpy" in result.failed

    def test_execute_partial_success(self):
        """测试部分成功"""
        repair = AutoRepair()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            ),
            Conflict(
                package="pandas",
                requires="pandas>=1.5",
                installed="1.4.0",
                suggestion="pandas==1.5.3",
            ),
        ]

        from pyenv_doctor.models.schemas import RepairPlan, SandboxResult

        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="test",
            ),
            RepairPlan(
                package_name="pandas",
                current_version="1.4.0",
                target_version="1.5.3",
                action="upgrade",
                reason="test",
            ),
        ]

        preview_results = [
            SandboxResult(scheme="numpy==1.23.5", success=True, error=None),
            SandboxResult(scheme="pandas==1.5.3", success=True, error=None),
        ]

        # numpy 成功，pandas 失败
        def execute_plan(plan):
            return plan.package_name == "numpy"

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                with patch.object(repair, '_execute_plan', side_effect=execute_plan):
                    result = repair.execute(conflicts, {})

        assert result.success is False  # 有失败
        assert "numpy" in result.repaired
        assert "pandas" in result.failed

    def test_execute_user_cancel(self):
        """测试用户取消"""
        repair = AutoRepair()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        from pyenv_doctor.models.schemas import RepairPlan, SandboxResult

        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="test",
            )
        ]

        preview_results = [
            SandboxResult(scheme="numpy==1.23.5", success=True, error=None),
        ]

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                # 模拟用户取消
                with patch.object(repair, '_execute_plan') as mock_execute:
                    mock_execute.side_effect = KeyboardInterrupt()
                    
                    result = repair.execute(conflicts, {})

        assert result.cancelled_by_user is True
        assert result.success is False

    def test_execute_plan_success(self):
        """测试执行方案成功"""
        repair = AutoRepair()

        from pyenv_doctor.models.schemas import RepairPlan

        plan = RepairPlan(
            package_name="numpy",
            current_version="1.24.0",
            target_version="1.23.5",
            action="downgrade",
            reason="test",
        )

        # Mock subprocess 成功
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            success = repair._execute_plan(plan)

        assert success is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "pip" in call_args
        assert "numpy==1.23.5" in call_args

    def test_execute_plan_failure(self):
        """测试执行方案失败"""
        repair = AutoRepair()

        from pyenv_doctor.models.schemas import RepairPlan

        plan = RepairPlan(
            package_name="numpy",
            current_version="1.24.0",
            target_version="1.23.5",
            action="downgrade",
            reason="test",
        )

        # Mock subprocess 失败
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error"

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            success = repair._execute_plan(plan)

        assert success is False

    def test_execute_plan_timeout(self):
        """测试执行方案超时"""
        repair = AutoRepair(timeout=1)

        from pyenv_doctor.models.schemas import RepairPlan

        plan = RepairPlan(
            package_name="numpy",
            current_version="1.24.0",
            target_version="1.23.5",
            action="downgrade",
            reason="test",
        )

        # Mock subprocess 超时
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd="pip", timeout=1)):
            success = repair._execute_plan(plan)

        assert success is False

    def test_execute_plan_exception(self):
        """测试执行方案异常"""
        repair = AutoRepair()

        from pyenv_doctor.models.schemas import RepairPlan

        plan = RepairPlan(
            package_name="numpy",
            current_version="1.24.0",
            target_version="1.23.5",
            action="downgrade",
            reason="test",
        )

        # Mock subprocess 抛出异常
        with patch('subprocess.run', side_effect=Exception("Unexpected error")):
            success = repair._execute_plan(plan)

        assert success is False

    def test_preview_repairs(self):
        """测试预览修复"""
        repair = AutoRepair()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        from pyenv_doctor.models.schemas import RepairPlan, SandboxResult

        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="test",
            )
        ]

        preview_results = [
            SandboxResult(scheme="numpy==1.23.5", success=True, error=None),
        ]

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                results = repair.preview_repairs(conflicts, {"numpy": "1.24.0"})

        assert len(results) == 1
        assert results[0].success is True

    def test_preview_repairs_no_plans(self):
        """测试预览无方案"""
        repair = AutoRepair()

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = []
            
            results = repair.preview_repairs([], {})

        assert results == []


class TestAutoRepairEdgeCases:
    """测试边界情况"""

    def test_execute_snapshot_id(self):
        """测试带快照 ID 执行"""
        repair = AutoRepair()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        from pyenv_doctor.models.schemas import RepairPlan, SandboxResult

        plans = [
            RepairPlan(
                package_name="numpy",
                current_version="1.24.0",
                target_version="1.23.5",
                action="downgrade",
                reason="test",
            )
        ]

        preview_results = [
            SandboxResult(scheme="numpy==1.23.5", success=True, error=None),
        ]

        with patch.object(repair, 'strategy_engine') as mock_strategy:
            mock_strategy.generate_plans.return_value = plans
            
            with patch.object(repair, 'sandbox_executor') as mock_sandbox:
                mock_sandbox.preview.return_value = preview_results
                
                with patch.object(repair, '_execute_plan', return_value=True):
                    result = repair.execute(
                        conflicts,
                        {"numpy": "1.24.0"},
                        snapshot_id="20260424_143022_abc123",
                    )

        assert result.snapshot_id == "20260424_143022_abc123"
        assert result.rollback_available is True

    def test_execute_strategy_in_result(self):
        """测试结果中包含策略"""
        repair = AutoRepair(strategy=RepairStrategy.CONSERVATIVE)

        conflicts = []

        result = repair.execute(conflicts, {})

        assert result.strategy == "conservative"

    def test_execute_duration_positive(self):
        """测试耗时为正数"""
        repair = AutoRepair()

        result = repair.execute([], {})

        assert result.duration >= 0
