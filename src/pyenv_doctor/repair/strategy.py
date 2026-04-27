# -*- coding: utf-8 -*-
"""
StrategyEngine - 修复策略引擎

实现三种修复策略：保守、平衡、激进。

@skill 修复策略引擎
"""

import logging
from typing import Dict, List

from packaging.version import Version

from ..models.schemas import Conflict, RepairPlan, RepairStrategy


class StrategyEngine:
    """
    修复策略引擎

    根据配置的策略生成修复方案。

    属性:
        name: Agent 名称，固定值 "StrategyEngine"
        strategy: 修复策略枚举
    """

    name: str = "StrategyEngine"

    def __init__(self, strategy: RepairStrategy = RepairStrategy.BALANCED):
        """
        初始化 StrategyEngine

        参数:
            strategy: 修复策略，默认平衡策略
        """
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"策略引擎初始化完成，当前策略：{strategy.value}")

    def generate_plans(self, conflicts: List[Conflict], 
                       current_versions: Dict[str, str]) -> List[RepairPlan]:
        """
        根据策略生成修复方案

        参数:
            conflicts: 冲突列表
            current_versions: 当前已安装版本字典 {包名：版本号}

        返回:
            List[RepairPlan]: 修复方案列表

        示例:
            >>> engine = StrategyEngine(RepairStrategy.CONSERVATIVE)
            >>> plans = engine.generate_plans(conflicts, current_versions)
        """
        plans: List[RepairPlan] = []

        if not conflicts:
            self.logger.debug("无冲突需要修复")
            return plans

        self.logger.info(f"开始生成修复方案，策略：{self.strategy.value}, 冲突数：{len(conflicts)}")

        for conflict in conflicts:
            try:
                plan = self._generate_plan(conflict, current_versions)
                if plan:
                    plans.append(plan)
            except Exception as e:
                self.logger.warning(f"生成 {conflict.package} 修复方案失败：{e}")
                continue

        self.logger.info(f"生成 {len(plans)} 个修复方案")
        return plans

    def _generate_plan(self, conflict: Conflict, 
                       current_versions: Dict[str, str]) -> RepairPlan:
        """
        为单个冲突生成修复方案

        参数:
            conflict: 冲突信息（Conflict 对象）
            current_versions: 当前版本字典

        返回:
            RepairPlan: 修复方案，无法生成时返回 None
        """
        # FIX-类型检查：确保传入的是 Conflict 对象
        if not hasattr(conflict, 'suggestion'):
            self.logger.warning(f"预期 Conflict 对象，但收到：{type(conflict)}, 跳过")
            return None
        
        # 解析目标版本
        target_version = self._extract_version_from_suggestion(conflict.suggestion)
        if not target_version:
            self.logger.warning(f"无法解析建议版本：{conflict.suggestion}")
            return None
        
        # FIX-从 suggestion 中提取正确的包名（而不是 conflict.package）
        # suggestion 格式：包名==版本号
        try:
            repair_package_name = conflict.suggestion.split('==')[0].strip()
        except Exception as e:
            self.logger.warning(f"无法从建议提取包名 {conflict.suggestion}: {e}")
            repair_package_name = conflict.package

        # 获取当前版本
        current_version = current_versions.get(
            repair_package_name.lower(), 
            conflict.installed
        )

        # 确定操作类型和原因
        action, reason = self._determine_action(
            repair_package_name,
            current_version,
            target_version,
            conflict.requires
        )

        if not action:
            self.logger.debug(f"跳过 {repair_package_name}: 无需修复")
            return None

        return RepairPlan(
            package_name=repair_package_name,
            current_version=current_version,
            target_version=target_version,
            action=action,
            reason=reason,
            dependencies=[]  # 简化版本暂不处理依赖拓扑
        )

    def _extract_version_from_suggestion(self, suggestion: str) -> str:
        """
        从修复建议中提取版本号

        参数:
            suggestion: 修复建议，格式为 包名==版本号

        返回:
            str: 版本号，解析失败返回 None
        """
        try:
            if "==" in suggestion:
                return suggestion.split("==")[1].strip()
            return None
        except Exception:
            return None

    def _determine_action(self, package: str, current: str, 
                          target: str, requires: str) -> tuple:
        """
        确定修复操作类型

        参数:
            package: 包名
            current: 当前版本
            target: 目标版本
            requires: 依赖要求

        返回:
            tuple: (操作类型，原因说明)，无需修复时返回 (None, None)
        """
        try:
            current_ver = Version(current)
            target_ver = Version(target)
        except Exception as e:
            self.logger.warning(f"版本解析失败 {package}: {e}")
            return None, None

        # 版本相同，无需修复
        if current_ver == target_ver:
            return None, None

        # 根据策略决定操作
        if self.strategy == RepairStrategy.CONSERVATIVE:
            # 保守策略：只降级
            if target_ver < current_ver:
                return "downgrade", f"降级以满足 {requires}"
            else:
                self.logger.info(
                    f"保守策略跳过 {package}: 目标版本 {target} 高于当前 {current}"
                )
                return None, None

        elif self.strategy == RepairStrategy.BALANCED:
            # 平衡策略：最小改动
            if target_ver < current_ver:
                return "downgrade", f"降级以满足 {requires}"
            elif target_ver > current_ver:
                return "upgrade", f"升级以满足 {requires}"
            else:
                return "reinstall", f"重新安装以修复 {requires}"

        elif self.strategy == RepairStrategy.AGGRESSIVE:
            # 激进策略：升到最新
            # 简化处理：直接使用目标版本（实际应该查询 PyPI 获取最新版）
            if target_ver < current_ver:
                return "downgrade", f"降级以满足 {requires} (激进模式)"
            elif target_ver > current_ver:
                return "upgrade", f"升级到最新 {target}"
            else:
                return "reinstall", f"重新安装 {package}"

        # 未知策略
        self.logger.warning(f"未知策略：{self.strategy}")
        return None, None

    def get_strategy_description(self) -> str:
        """
        获取策略描述

        返回:
            str: 策略描述文本
        """
        descriptions = {
            RepairStrategy.CONSERVATIVE: "保守策略 - 只降级，避免升级带来的新风险",
            RepairStrategy.BALANCED: "平衡策略 - 最小改动，按需升降级",
            RepairStrategy.AGGRESSIVE: "激进策略 - 升最新，获取最新功能和修复",
        }
        return descriptions.get(self.strategy, "未知策略")
