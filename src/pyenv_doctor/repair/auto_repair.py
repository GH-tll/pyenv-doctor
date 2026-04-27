# -*- coding: utf-8 -*-
"""
AutoRepair - 一键修复执行器

实现一键修复功能，集成策略引擎、沙箱预演、冲突检测。

@skill 一键修复
"""

import logging
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

from ..agents.sandbox_executor import SandboxExecutor
from ..models.schemas import (
    Conflict,
    RepairPlan,
    RepairResult,
    RepairStrategy,
    SandboxResult,
)
from .strategy import StrategyEngine


class AutoRepair:
    """
    一键修复执行器

    自动执行修复流程：生成方案 -> 沙箱预演 -> 执行修复 -> 验证结果。

    属性:
        name: Agent 名称，固定值 "AutoRepair"
        strategy: 修复策略
        dry_run: 是否仅预演不执行
        timeout: 单次安装超时时间
    """

    name: str = "AutoRepair"

    def __init__(
        self,
        strategy: RepairStrategy = RepairStrategy.BALANCED,
        dry_run: bool = False,
        timeout: int = 60,
    ):
        """
        初始化 AutoRepair

        参数:
            strategy: 修复策略，默认平衡策略
            dry_run: 是否仅预演，默认 False
            timeout: 单次安装超时时间（秒），默认 60 秒
        """
        self.strategy = strategy
        self.dry_run = dry_run
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # 初始化子组件
        self.strategy_engine = StrategyEngine(strategy)
        self.sandbox_executor = SandboxExecutor(timeout=timeout)
        
        self.logger.info(f"AutoRepair 初始化完成，策略：{strategy.value}, 预演模式：{dry_run}")

    def execute(
        self,
        conflicts: List[Conflict],
        current_versions: Dict[str, str],
        snapshot_id: Optional[str] = None,
    ) -> RepairResult:
        """
        执行一键修复

        流程:
        1. 生成修复方案
        2. 沙箱预演
        3. 执行修复
        4. 验证结果

        参数:
            conflicts: 冲突列表
            current_versions: 当前版本字典 {包名：版本号}
            snapshot_id: 关联的快照 ID（可选）

        返回:
            RepairResult: 修复结果

        示例:
            >>> repair = AutoRepair()
            >>> result = repair.execute(conflicts, current_versions, snapshot_id)
        """
        start_time = time.time()
        repaired: List[str] = []
        failed: List[str] = []
        cancelled = False

        self.logger.info(f"开始一键修复，冲突数：{len(conflicts)}, 快照 ID: {snapshot_id}")

        # 步骤 1: 生成修复方案
        self._log_progress("生成修复方案", 1, 4)
        plans = self.strategy_engine.generate_plans(conflicts, current_versions)
        if not plans:
            self.logger.info("无需修复或无法生成修复方案")
            return RepairResult(
                success=True,
                repaired=[],
                failed=[],
                snapshot_id=snapshot_id or "N/A",
                duration=time.time() - start_time,
                strategy=self.strategy.value,
                rollback_available=False,
                cancelled_by_user=False,
            )

        self.logger.info(f"生成 {len(plans)} 个修复方案")

        # 步骤 2: 沙箱预演
        self._log_progress("沙箱预演", 2, 4)
        preview_results = self.sandbox_executor.preview(plans, parallel=True)
        
        # 过滤预演失败的方案
        valid_plans = []
        for plan, result in zip(plans, preview_results):
            if result.success:
                valid_plans.append(plan)
                self.logger.debug(f"预演成功：{plan.package_name}=={plan.target_version}")
            else:
                failed.append(plan.package_name)
                self.logger.warning(
                    f"预演失败：{plan.package_name}, 错误：{result.error}"
                )

        if not valid_plans:
            self.logger.error("所有方案预演失败，终止修复")
            return RepairResult(
                success=False,
                repaired=[],
                failed=[p.package_name for p in plans],
                snapshot_id=snapshot_id or "N/A",
                duration=time.time() - start_time,
                strategy=self.strategy.value,
                rollback_available=False,
                cancelled_by_user=False,
            )

        # 步骤 3: 执行修复
        self._log_progress("执行修复", 3, 4)
        if self.dry_run:
            self.logger.info("[DRY-RUN] 跳过实际修复")
            for plan in valid_plans:
                self.logger.info(f"  - {plan.to_command()}")
                repaired.append(plan.package_name)
        else:
            # 实际执行修复
            for plan in valid_plans:
                try:
                    success = self._execute_plan(plan)
                    if success:
                        repaired.append(plan.package_name)
                        self.logger.info(f"修复成功：{plan.package_name}")
                    else:
                        failed.append(plan.package_name)
                        self.logger.error(f"修复失败：{plan.package_name}")
                except KeyboardInterrupt:
                    self.logger.warning("用户取消修复")
                    cancelled = True
                    break
                except Exception as e:
                    self.logger.error(f"修复异常 {plan.package_name}: {e}")
                    failed.append(plan.package_name)

        # 步骤 4: 生成结果
        self._log_progress("生成结果", 4, 4)
        duration = time.time() - start_time
        success = len(failed) == 0 and not cancelled

        result = RepairResult(
            success=success,
            repaired=repaired,
            failed=failed,
            snapshot_id=snapshot_id or "N/A",
            duration=duration,
            strategy=self.strategy.value,
            rollback_available=success and snapshot_id is not None,
            cancelled_by_user=cancelled,
        )

        self.logger.info(result.to_report())
        return result

    def _execute_plan(self, plan: RepairPlan) -> bool:
        """
        执行单个修复方案

        参数:
            plan: 修复方案

        返回:
            bool: 是否成功
        """
        try:
            command = ["pip", "install", f"{plan.package_name}=={plan.target_version}", "--quiet"]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode == 0:
                self.logger.debug(f"pip 安装成功：{plan.package_name}=={plan.target_version}")
                return True
            else:
                self.logger.error(
                    f"pip 安装失败 {plan.package_name}: {result.stderr}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"安装超时 {plan.package_name}")
            return False
        except Exception as e:
            self.logger.error(f"安装异常 {plan.package_name}: {e}")
            return False

    def _log_progress(self, step_name: str, step_num: int, total_steps: int):
        """
        记录进度日志

        参数:
            step_name: 步骤名称
            step_num: 当前步骤编号
            total_steps: 总步骤数
        """
        self.logger.info(f"[{step_num}/{total_steps}] {step_name}...")

    def preview_repairs(
        self,
        conflicts: List[Conflict],
        current_versions: Dict[str, str],
    ) -> List[SandboxResult]:
        """
        预览修复方案（不执行）

        参数:
            conflicts: 冲突列表
            current_versions: 当前版本字典

        返回:
            List[SandboxResult]: 沙箱预演结果列表
        """
        self.logger.info("预览修复方案...")
        
        # 生成方案
        plans = self.strategy_engine.generate_plans(conflicts, current_versions)
        if not plans:
            return []
        
        # 沙箱预演
        results = self.sandbox_executor.preview(plans, parallel=True)
        
        self.logger.info(f"预览完成，{len(results)} 个方案")
        return results
