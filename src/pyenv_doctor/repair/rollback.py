# -*- coding: utf-8 -*-
"""
RollbackEngine - 回滚引擎

实现快照回滚功能，支持预览、执行、验证。

@skill 回滚引擎
"""

import logging
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from ..models.schemas import (
    PackageChange,
    RollbackResult,
    RollbackPreview,
    Snapshot,
    VerificationResult,
)
from ..snapshot.manager import SnapshotManager


class RollbackEngine:
    """
    回滚引擎

    提供快照回滚、预览、验证功能。

    属性:
        name: Agent 名称，固定值 "RollbackEngine"
        timeout: 单次安装超时时间
    """

    name: str = "RollbackEngine"

    def __init__(self, timeout: int = 60):
        """
        初始化 RollbackEngine

        参数:
            timeout: 单次安装超时时间（秒），默认 60 秒
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.snapshot_manager = SnapshotManager()
        self.logger.info("回滚引擎初始化完成")

    def rollback(self, snapshot_id: str, verify: bool = True) -> RollbackResult:
        """
        执行回滚

        流程:
        1. 加载快照
        2. 生成回滚计划
        3. 执行回滚
        4. 验证结果（可选）

        参数:
            snapshot_id: 快照 ID
            verify: 是否验证回滚结果，默认 True

        返回:
            RollbackResult: 回滚结果

        示例:
            >>> engine = RollbackEngine()
            >>> result = engine.rollback("20260424_143022_abc123")
        """
        start_time = time.time()
        packages_restored = 0

        self.logger.info(f"开始回滚到快照 {snapshot_id}")

        # 步骤 1: 加载快照
        try:
            snapshot = self.snapshot_manager.get(snapshot_id)
            if not snapshot:
                self.logger.error(f"快照不存在：{snapshot_id}")
                return RollbackResult(
                    success=False,
                    snapshot_id=snapshot_id,
                    packages_restored=0,
                    duration=time.time() - start_time,
                    verified=False,
                )
        except Exception as e:
            self.logger.error(f"加载快照失败：{e}")
            return RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                packages_restored=0,
                duration=time.time() - start_time,
                verified=False,
            )

        self.logger.info(f"加载快照成功：{snapshot.total_packages} 个包")

        # 步骤 2: 生成回滚计划
        target_packages = snapshot.packages
        self.logger.info(f"准备恢复 {len(target_packages)} 个包")

        # 步骤 3: 执行回滚
        success_count = 0
        failed_count = 0
        user_cancelled = False

        for package_name, target_version in target_packages.items():
            try:
                result = self._restore_package(package_name, target_version)
                if result:
                    success_count += 1
                    packages_restored += 1
                    self.logger.debug(f"恢复成功：{package_name}=={target_version}")
                else:
                    failed_count += 1
                    self.logger.warning(f"恢复失败：{package_name}")
            except KeyboardInterrupt:
                self.logger.warning("用户取消回滚")
                user_cancelled = True
                break
            except Exception as e:
                failed_count += 1
                self.logger.error(f"恢复异常 {package_name}: {e}")

        duration = time.time() - start_time
        # 用户取消时，success 应为 False
        success = (failed_count == 0) and (not user_cancelled)

        # 步骤 4: 验证结果
        verified = False
        if verify and success:
            self.logger.info("开始验证回滚结果...")
            verification = self._verify_snapshot(snapshot)
            verified = verification.passed
            self.logger.info(f"验证结果：{'通过' if verified else '失败'}")

        result = RollbackResult(
            success=success,
            snapshot_id=snapshot_id,
            packages_restored=packages_restored,
            duration=duration,
            verified=verified,
        )

        self.logger.info(result.to_report())
        return result

    def preview(self, snapshot_id: str) -> Optional[RollbackPreview]:
        """
        预览回滚

        显示回滚将影响的包列表。

        参数:
            snapshot_id: 快照 ID

        返回:
            RollbackPreview: 回滚预览，快照不存在时返回 None
        """
        self.logger.info(f"预览回滚到快照 {snapshot_id}")

        # 加载快照
        try:
            snapshot = self.snapshot_manager.get(snapshot_id)
            if not snapshot:
                self.logger.warning(f"快照不存在：{snapshot_id}")
                return None
        except Exception as e:
            self.logger.error(f"加载快照失败：{e}")
            return None

        # 获取当前已安装包版本
        current_packages = self._get_installed_packages()

        # 生成变更列表
        changes: List[PackageChange] = []
        for package_name, target_version in snapshot.packages.items():
            current_version = current_packages.get(package_name.lower())
            
            # 如果当前版本与快照版本不同，则记录变更
            if current_version != target_version:
                changes.append(PackageChange(
                    package_name=package_name,
                    current_version=current_version or "未安装",
                    target_version=target_version,
                ))

        preview = RollbackPreview(
            snapshot_id=snapshot_id,
            changes=changes,
            total_changes=len(changes),
        )

        self.logger.info(f"预览完成，{len(changes)} 个包将发生变化")
        return preview

    def _restore_package(self, package_name: str, version: str) -> bool:
        """
        恢复单个包到指定版本

        参数:
            package_name: 包名
            version: 目标版本

        返回:
            bool: 是否成功
        """
        try:
            command = ["pip", "install", f"{package_name}=={version}", "--quiet", "--force-reinstall"]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode == 0:
                self.logger.debug(f"恢复成功：{package_name}=={version}")
                return True
            else:
                self.logger.warning(f"恢复失败 {package_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"恢复超时 {package_name}")
            return False
        except Exception as e:
            self.logger.error(f"恢复异常 {package_name}: {e}")
            return False

    def _get_installed_packages(self) -> Dict[str, str]:
        """
        获取当前已安装包版本

        返回:
            Dict[str, str]: 包版本字典 {包名小写：版本号}
        """
        try:
            result = subprocess.run(
                ["pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            packages = {}
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    name, version = line.split("==")
                    packages[name.lower()] = version.strip()
            
            return packages
            
        except Exception as e:
            self.logger.error(f"获取已安装包失败：{e}")
            return {}

    def _verify_snapshot(self, snapshot: Snapshot) -> VerificationResult:
        """
        验证快照恢复结果

        参数:
            snapshot: 快照对象

        返回:
            VerificationResult: 验证结果
        """
        verified_packages = 0
        failed_packages: List[str] = []
        
        # 获取当前已安装包
        current_packages = self._get_installed_packages()
        
        # 验证每个包
        for package_name, expected_version in snapshot.packages.items():
            actual_version = current_packages.get(package_name.lower())
            
            if actual_version == expected_version:
                verified_packages += 1
            else:
                failed_packages.append(package_name)
                self.logger.warning(
                    f"验证失败 {package_name}: 期望 {expected_version}, 实际 {actual_version}"
                )
        
        checksum_valid = True  # 简化处理，暂不验证校验和
        
        passed = len(failed_packages) == 0
        
        return VerificationResult(
            passed=passed,
            verified_packages=verified_packages,
            failed_packages=failed_packages,
            checksum_valid=checksum_valid,
        )

    def get_latest_snapshot_id(self) -> Optional[str]:
        """
        获取最新的快照 ID

        返回:
            str: 最新快照 ID，无快照时返回 None
        """
        try:
            snapshots = self.snapshot_manager.list_snapshots()
            if snapshots:
                # 按时间排序，返回最新的
                sorted_snapshots = sorted(
                    snapshots,
                    key=lambda s: s.timestamp,
                    reverse=True,
                )
                latest_id = sorted_snapshots[0].id
                self.logger.debug(f"最新快照 ID: {latest_id}")
                return latest_id
            else:
                self.logger.debug("无可用快照")
                return None
        except Exception as e:
            self.logger.error(f"获取最新快照失败：{e}")
            return None
