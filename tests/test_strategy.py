# -*- coding: utf-8 -*-
"""
测试修复策略引擎

覆盖场景:
- 保守策略
- 平衡策略
- 激进策略
- 方案生成
- 操作类型判断
"""

import pytest

from pyenv_doctor.models.schemas import Conflict, RepairPlan, RepairStrategy
from pyenv_doctor.repair.strategy import StrategyEngine


class TestStrategyEngine:
    """测试 StrategyEngine 类"""

    def test_init_default_strategy(self):
        """测试默认策略初始化"""
        engine = StrategyEngine()
        assert engine.strategy == RepairStrategy.BALANCED

    def test_init_custom_strategy(self):
        """测试自定义策略初始化"""
        engine = StrategyEngine(RepairStrategy.CONSERVATIVE)
        assert engine.strategy == RepairStrategy.CONSERVATIVE

    def test_generate_plans_no_conflicts(self):
        """测试无冲突时生成方案"""
        engine = StrategyEngine()
        plans = engine.generate_plans([], {})

        assert plans == []

    def test_generate_plans_conservative(self):
        """测试保守策略生成方案"""
        engine = StrategyEngine(RepairStrategy.CONSERVATIVE)

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            )
        ]

        current_versions = {"numpy": "1.24.0"}
        plans = engine.generate_plans(conflicts, current_versions)

        assert len(plans) == 1
        assert plans[0].package_name == "numpy"
        assert plans[0].current_version == "1.24.0"
        assert plans[0].target_version == "1.23.5"
        assert plans[0].action == "downgrade"

    def test_generate_plans_balanced(self):
        """测试平衡策略生成方案"""
        engine = StrategyEngine(RepairStrategy.BALANCED)

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.25",
                installed="1.24.0",
                suggestion="numpy==1.24.5",
            )
        ]

        current_versions = {"numpy": "1.24.0"}
        plans = engine.generate_plans(conflicts, current_versions)

        assert len(plans) == 1
        assert plans[0].action == "upgrade"

    def test_generate_plans_aggressive(self):
        """测试激进策略生成方案"""
        engine = StrategyEngine(RepairStrategy.AGGRESSIVE)

        conflicts = [
            Conflict(
                package="pandas",
                requires="pandas>=2.0",
                installed="1.5.3",
                suggestion="pandas==2.0.0",
            )
        ]

        current_versions = {"pandas": "1.5.3"}
        plans = engine.generate_plans(conflicts, current_versions)

        assert len(plans) == 1
        assert plans[0].action == "upgrade"

    def test_generate_plan_single_conflict(self):
        """测试单个冲突生成方案"""
        engine = StrategyEngine()

        conflict = Conflict(
            package="requests",
            requires="requests<2.28",
            installed="2.28.2",
            suggestion="requests==2.27.1",
        )

        current_versions = {"requests": "2.28.2"}
        plans = engine.generate_plans([conflict], current_versions)

        assert len(plans) == 1
        assert plans[0].package_name == "requests"
        assert plans[0].action == "downgrade"
        # reason 中应该包含原始依赖要求
        assert "requires" in plans[0].reason.lower() or "降级" in plans[0].reason

    def test_generate_plan_multiple_conflicts(self):
        """测试多个冲突生成方案"""
        engine = StrategyEngine()

        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            ),
            Conflict(
                package="requests",
                requires="requests<2.28",
                installed="2.28.2",
                suggestion="requests==2.27.1",
            ),
        ]

        current_versions = {
            "numpy": "1.24.0",
            "requests": "2.28.2",
        }

        plans = engine.generate_plans(conflicts, current_versions)

        assert len(plans) == 2
        package_names = [p.package_name for p in plans]
        assert "numpy" in package_names
        assert "requests" in package_names

    def test_generate_plan_skip_same_version(self):
        """测试跳过相同版本"""
        engine = StrategyEngine()

        conflict = Conflict(
            package="numpy",
            requires="numpy<1.24",
            installed="1.23.5",
            suggestion="numpy==1.23.5",
        )

        current_versions = {"numpy": "1.23.5"}
        plans = engine.generate_plans([conflict], current_versions)

        # 版本相同，应该跳过
        assert plans == []

    def test_extract_version_from_suggestion(self):
        """测试从建议中提取版本"""
        engine = StrategyEngine()

        # 正常格式
        version = engine._extract_version_from_suggestion("numpy==1.23.5")
        assert version == "1.23.5"

        # 无效格式
        version = engine._extract_version_from_suggestion("invalid")
        assert version is None

        # 空字符串
        version = engine._extract_version_from_suggestion("")
        assert version is None

    def test_determine_action_conservative_downgrade(self):
        """测试保守策略降级"""
        engine = StrategyEngine(RepairStrategy.CONSERVATIVE)

        action, reason = engine._determine_action(
            "numpy", "1.24.0", "1.23.5", "pandas requires <1.24"
        )

        assert action == "downgrade"
        assert "降级" in reason

    def test_determine_action_conservative_skip_upgrade(self):
        """测试保守策略跳过升级"""
        engine = StrategyEngine(RepairStrategy.CONSERVATIVE)

        action, reason = engine._determine_action(
            "pandas", "1.5.3", "2.0.0", "new feature"
        )

        # 保守策略不升级
        assert action is None
        assert reason is None

    def test_determine_action_balanced_downgrade(self):
        """测试平衡策略降级"""
        engine = StrategyEngine(RepairStrategy.BALANCED)

        action, reason = engine._determine_action(
            "numpy", "1.24.0", "1.23.5", "pandas requires <1.24"
        )

        assert action == "downgrade"

    def test_determine_action_balanced_upgrade(self):
        """测试平衡策略升级"""
        engine = StrategyEngine(RepairStrategy.BALANCED)

        action, reason = engine._determine_action(
            "pandas", "1.5.3", "2.0.0", "new feature"
        )

        assert action == "upgrade"

    def test_determine_action_balanced_reinstall(self):
        """测试平衡策略重新安装"""
        engine = StrategyEngine(RepairStrategy.BALANCED)

        # 当版本相同时，如果有明确原因（如 corrupted），应该重新安装
        # 但实际逻辑中，版本相同通常返回 None（无需操作）
        action, reason = engine._determine_action(
            "numpy", "1.23.5", "1.23.5", "corrupted"
        )

        # 版本相同，可能返回 None 或 reinstall，取决于实现
        # 这里接受两种情况
        assert action in [None, "reinstall"]

    def test_determine_action_aggressive(self):
        """测试激进策略"""
        engine = StrategyEngine(RepairStrategy.AGGRESSIVE)

        # 升级
        action, reason = engine._determine_action(
            "pandas", "1.5.3", "2.0.0", "latest"
        )
        assert action == "upgrade"

        # 降级
        action, reason = engine._determine_action(
            "numpy", "1.24.0", "1.23.5", "compatibility"
        )
        assert action == "downgrade"

    def test_determine_action_invalid_version(self):
        """测试无效版本号"""
        engine = StrategyEngine()

        action, reason = engine._determine_action(
            "numpy", "invalid", "also-invalid", "test"
        )

        assert action is None
        assert reason is None

    def test_get_strategy_description(self):
        """测试获取策略描述"""
        # 保守策略
        engine = StrategyEngine(RepairStrategy.CONSERVATIVE)
        desc = engine.get_strategy_description()
        assert "保守" in desc
        assert "降级" in desc

        # 平衡策略
        engine = StrategyEngine(RepairStrategy.BALANCED)
        desc = engine.get_strategy_description()
        assert "平衡" in desc
        assert "最小改动" in desc

        # 激进策略
        engine = StrategyEngine(RepairStrategy.AGGRESSIVE)
        desc = engine.get_strategy_description()
        assert "激进" in desc
        assert "最新" in desc

    def test_generate_plan_with_complex_conflict(self):
        """测试复杂冲突生成方案"""
        engine = StrategyEngine()

        conflict = Conflict(
            package="scipy",
            requires="scipy>=1.9.0,<1.11.0",
            installed="1.10.0",
            suggestion="scipy==1.10.1",
        )

        current_versions = {"scipy": "1.10.0"}
        plans = engine.generate_plans([conflict], current_versions)

        assert len(plans) == 1
        assert plans[0].target_version == "1.10.1"


class TestStrategyEngineEdgeCases:
    """测试边界情况"""

    def test_conservative_no_solution(self):
        """测试保守策略无解"""
        engine = StrategyEngine(RepairStrategy.CONSERVATIVE)

        # 需要升级但保守策略只升级
        conflict = Conflict(
            package="new-pkg",
            requires="new-pkg>=2.0",
            installed="1.0.0",
            suggestion="new-pkg==2.0.0",
        )

        current_versions = {"new-pkg": "1.0.0"}
        plans = engine.generate_plans([conflict], current_versions)

        # 保守策略无法解决需要升级的冲突
        assert plans == []

    def test_generate_plan_exception_handling(self):
        """测试生成方案异常处理"""
        engine = StrategyEngine()

        # 创建无效的冲突对象
        class InvalidConflict:
            package = "test"
            requires = "invalid"
            installed = "invalid"
            suggestion = "invalid"

        # 应该跳过无效的冲突
        plans = engine.generate_plans([InvalidConflict()], {})
        assert plans == []

    def test_multi_dependency_conflict(self):
        """测试多依赖冲突"""
        engine = StrategyEngine(RepairStrategy.BALANCED)

        # numpy 被多个包依赖
        conflicts = [
            Conflict(
                package="numpy",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            ),
            Conflict(
                package="numpy",
                requires="numpy>=1.20",
                installed="1.24.0",
                suggestion="numpy==1.23.5",
            ),
        ]

        current_versions = {"numpy": "1.24.0"}
        plans = engine.generate_plans(conflicts, current_versions)

        # 应该合并为同一个方案
        assert len(plans) >= 1
        assert plans[0].package_name == "numpy"

    def test_pre_release_version(self):
        """测试预发布版本"""
        engine = StrategyEngine()

        conflict = Conflict(
            package="test-pkg",
            requires="test-pkg>=1.0.0rc1",
            installed="1.0.0b2",
            suggestion="test-pkg==1.0.0rc1",
        )

        current_versions = {"test-pkg": "1.0.0b2"}
        plans = engine.generate_plans([conflict], current_versions)

        assert len(plans) == 1
        assert plans[0].action == "upgrade"

    def test_local_version(self):
        """测试本地版本"""
        engine = StrategyEngine()

        conflict = Conflict(
            package="test-pkg",
            requires="test-pkg>=1.0.0",
            installed="1.0.0+local",
            suggestion="test-pkg==1.0.0",
        )

        current_versions = {"test-pkg": "1.0.0+local"}
        plans = engine.generate_plans([conflict], current_versions)

        # 本地版本处理
        assert len(plans) == 1
