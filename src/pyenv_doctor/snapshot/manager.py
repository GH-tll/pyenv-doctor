# -*- coding: utf-8 -*-
"""
快照管理器

负责快照的业务逻辑：创建、列表、回滚、删除、导出。
"""

import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..models.schemas import (
    PackageChange,
    RepairPlan,
    RepairStrategy,
    RollbackPreview,
    RollbackResult,
    Snapshot,
    VerificationResult,
)
from .storage import SnapshotStorage, SnapshotNotFoundError

# 配置日志
logger = logging.getLogger(__name__)


class SnapshotError(Exception):
    """快照操作异常基类"""

    pass


class SnapshotCreateError(SnapshotError):
    """创建快照失败异常"""

    pass


class RollbackError(SnapshotError):
    """回滚失败异常"""

    pass


class ExportError(SnapshotError):
    """导出失败异常"""

    pass


class SnapshotManager:
    """
    快照管理器

    职责：
    - 创建快照
    - 列出快照
    - 回滚到指定快照
    - 删除快照
    - 导出快照
    - 清理临时快照
    """

    def __init__(self, storage: Optional[SnapshotStorage] = None):
        """
        初始化快照管理器

        Args:
            storage: 存储引擎，默认创建实例
        """
        self.storage = storage or SnapshotStorage()
        self._pip_tool = None

    def _get_pip_tool(self):
        """懒加载 pip_tool"""
        if self._pip_tool is None:
            from ..tools.pip_tool import PipTool

            self._pip_tool = PipTool()
        return self._pip_tool

    def create(
        self,
        label: Optional[str] = None,
        temporary: bool = False,
        timeout: int = 30
    ) -> Snapshot:
        """
        创建快照

        Args:
            label: 用户标签（可选）
            temporary: 是否为临时快照
            timeout: 超时时间（秒），默认 30 秒

        Returns:
            创建的快照对象

        异常:
            SnapshotCreateError: 创建失败时抛出
        """
        import signal
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
        
        def _do_create():
            """内部创建函数"""
            logger.debug("开始创建快照...")
            
            # 1. 获取 Python 版本
            python_version = sys.version.split()[0]
            logger.debug(f"Python 版本：{python_version}")

            # 2. 获取虚拟环境路径（如果在 venv 中）
            venv_path = self._get_venv_path()
            logger.debug(f"虚拟环境路径：{venv_path}")

            # 3. 获取包列表（带超时保护）
            logger.debug("正在获取包列表...")
            pip_tool = self._get_pip_tool()
            packages = pip_tool.get_installed_packages()
            logger.debug(f"获取到 {len(packages)} 个包")
            
            # FIX-验证包列表是否获取成功
            if not packages:
                logger.warning("未获取到包列表，使用空列表")
                packages = {}

            # 4. 生成快照 ID
            snapshot_id = self._generate_snapshot_id()
            logger.debug(f"生成快照 ID: {snapshot_id}")

            # 5. 创建快照对象
            snapshot = Snapshot(
                id=snapshot_id,
                timestamp=datetime.now(),
                label=label,
                python_version=python_version,
                venv_path=venv_path,
                packages=packages,
                total_packages=len(packages),
                checksum="",  # 待计算
                is_temporary=temporary,
            )
            logger.debug("快照对象创建完成")

            # 6. 计算校验和（不包含 checksum 字段）
            logger.debug("正在计算校验和...")
            data = snapshot.to_dict()
            data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
            snapshot.checksum = self.storage.calculate_checksum(data_without_checksum)
            logger.debug(f"校验和计算完成：{snapshot.checksum[:20]}...")

            # 7. 保存到磁盘（带超时保护）
            logger.debug(f"正在保存快照到：{self.storage.storage_dir}")
            try:
                self.storage.save(snapshot, timeout=10)
            except TypeError:
                # 兼容旧版本 save 方法（无 timeout 参数）
                self.storage.save(snapshot)
            logger.debug("快照保存完成")

            logger.info(f"创建快照成功：{snapshot_id}, 标签：{label}, 包数量：{len(packages)}")
            return snapshot
        
        # 使用线程池实现跨平台超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_create)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeoutError:
                msg = f"快照创建超时（{timeout}秒）"
                logger.error(msg)
                raise SnapshotCreateError(msg)
            except Exception as e:
                logger.error(f"创建快照失败：{str(e)}", exc_info=True)
                raise SnapshotCreateError(f"创建快照失败：{str(e)}") from e

    def get(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        获取指定快照

        Args:
            snapshot_id: 快照 ID

        Returns:
            快照对象，不存在返回 None
        """
        try:
            snapshot = self.storage.load(snapshot_id)
            logger.info(f"获取快照成功：{snapshot_id}")
            return snapshot
        except SnapshotNotFoundError:
            logger.warning(f"快照不存在：{snapshot_id}")
            return None
        except Exception as e:
            logger.error(f"获取快照失败：{str(e)}")
            return None

    def list_snapshots(self, limit: Optional[int] = None) -> List[Snapshot]:
        """
        列出快照

        Args:
            limit: 限制数量，None 表示全部

        Returns:
            快照列表，按时间倒序
        """
        try:
            snapshots = self.storage.list_all()

            if limit is not None and limit > 0:
                snapshots = snapshots[:limit]

            logger.info(f"列出快照，共 {len(snapshots)} 个")

            return snapshots

        except Exception as e:
            logger.error(f"列出快照失败：{str(e)}")
            raise

    def rollback(
        self,
        snapshot_id: str,
        verify: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> RollbackResult:
        """
        回滚到指定快照

        Args:
            snapshot_id: 快照 ID
            verify: 是否回滚后验证
            progress_callback: 进度回调函数 (current, total, package_name)

        Returns:
            回滚结果对象

        异常:
            SnapshotNotFoundError: 快照不存在
            RollbackError: 回滚失败
        """
        start_time = time.time()

        try:
            # 1. 加载快照
            snapshot = self.storage.load(snapshot_id)
            logger.info(f"开始回滚到快照：{snapshot_id}")

            # 2. 恢复包版本
            pip_tool = self._get_pip_tool()
            packages = snapshot.packages
            total = len(packages)

            for i, (pkg_name, pkg_version) in enumerate(packages.items(), 1):
                # 调用进度回调
                if progress_callback:
                    progress_callback(i, total, pkg_name)

                # 安装包
                success = pip_tool.install_package(pkg_name, pkg_version)
                if not success:
                    raise RollbackError(f"回滚失败：无法安装 {pkg_name}=={pkg_version}")

            # 3. 验证回滚
            if verify:
                verification = self._verify_rollback(snapshot)
                if not verification.passed:
                    raise RollbackError(f"回滚验证失败：{verification.failed_packages}")

            duration = time.time() - start_time

            result = RollbackResult(
                success=True,
                snapshot_id=snapshot_id,
                packages_restored=total,
                duration=duration,
                verified=verify,
            )

            logger.info(f"回滚成功：{snapshot_id}, 恢复 {total} 个包，耗时 {duration:.1f}秒")

            return result

        except SnapshotNotFoundError:
            raise
        except RollbackError:
            raise
        except Exception as e:
            logger.error(f"回滚失败：{str(e)}")
            raise RollbackError(f"回滚失败：{str(e)}") from e

    def delete(
        self,
        snapshot_id: str,
        force: bool = False,
    ) -> None:
        """
        删除快照

        Args:
            snapshot_id: 快照 ID
            force: 强制删除，不验证

        异常:
            SnapshotNotFoundError: 快照不存在
        """
        try:
            self.storage.delete(snapshot_id)
            logger.info(f"删除快照：{snapshot_id}")

        except SnapshotNotFoundError:
            raise
        except Exception as e:
            logger.error(f"删除快照失败：{str(e)}")
            raise

    def export(
        self,
        snapshot_id: str,
        output_path: str,
        format: str = "requirements",
    ) -> str:
        """
        导出快照

        Args:
            snapshot_id: 快照 ID
            output_path: 输出文件路径
            format: 导出格式 [requirements|json]

        Returns:
            实际输出路径

        异常:
            SnapshotNotFoundError: 快照不存在
            ExportError: 导出失败
        """
        try:
            # 1. 加载快照
            snapshot = self.storage.load(snapshot_id)

            # 2. 根据格式生成内容
            if format == "requirements":
                content = self._export_to_requirements(snapshot)
            elif format == "json":
                import json

                content = json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False)
            else:
                raise ExportError(f"不支持的导出格式：{format}")

            # 3. 写入文件
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"导出快照成功：{snapshot_id} -> {output_path}")

            return str(output_path)

        except SnapshotNotFoundError:
            raise
        except ExportError:
            raise
        except Exception as e:
            logger.error(f"导出快照失败：{str(e)}")
            raise ExportError(f"导出快照失败：{str(e)}") from e

    def cleanup_temporary(self) -> int:
        """
        清理所有临时快照

        Returns:
            删除的快照数量
        """
        try:
            snapshots = self.storage.list_all()
            count = 0

            for snapshot in snapshots:
                if snapshot.is_temporary:
                    self.storage.delete(snapshot.id)
                    count += 1

            logger.info(f"清理临时快照：{count} 个")

            return count

        except Exception as e:
            logger.error(f"清理临时快照失败：{str(e)}")
            raise

    def get_latest(self) -> Optional[Snapshot]:
        """
        获取最新快照

        Returns:
            最新快照，无快照返回 None
        """
        try:
            snapshots = self.list_snapshots(limit=1)
            return snapshots[0] if snapshots else None

        except Exception as e:
            logger.error(f"获取最新快照失败：{str(e)}")
            return None

    def preview_rollback(self, snapshot_id: str) -> RollbackPreview:
        """
        预览回滚影响

        Args:
            snapshot_id: 快照 ID

        Returns:
            回滚预览对象

        异常:
            SnapshotNotFoundError: 快照不存在
        """
        # 加载快照
        snapshot = self.storage.load(snapshot_id)

        # 获取当前包版本
        pip_tool = self._get_pip_tool()
        current_packages = pip_tool.get_installed_packages()

        # 构建变更列表
        changes = []
        for pkg_name, target_version in snapshot.packages.items():
            current_version = current_packages.get(pkg_name, "未安装")
            if current_version != target_version:
                changes.append(
                    PackageChange(
                        package_name=pkg_name,
                        current_version=current_version,
                        target_version=target_version,
                    )
                )

        return RollbackPreview(
            snapshot_id=snapshot_id,
            changes=changes,
            total_changes=len(changes),
        )

    def _generate_snapshot_id(self) -> str:
        """
        生成快照 ID

        格式：YYYYMMDD_HHMMSS_random(6)

        Returns:
            快照 ID
        """
        timestamp = datetime.now()
        random_str = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6)
        )
        return f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{random_str}"

    def _get_venv_path(self) -> Optional[str]:
        """
        获取虚拟环境路径

        Returns:
            虚拟环境路径，不在 venv 中返回 None
        """
        # 检查是否在虚拟环境中
        if (
            hasattr(sys, "real_prefix")
            or (
                hasattr(sys, "base_prefix")
                and sys.base_prefix != sys.prefix
            )
        ):
            return sys.prefix
        return None

    def _export_to_requirements(self, snapshot: Snapshot) -> str:
        """
        导出为 requirements.txt 格式

        Args:
            snapshot: 快照对象

        Returns:
            requirements.txt 内容
        """
        lines = [
            "# PyEnv Doctor Snapshot Export",
            f"# Created: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Python: {snapshot.python_version}",
            f"# Packages: {snapshot.total_packages}",
            f"# Snapshot ID: {snapshot.id}",
            "# -------------------------",
        ]

        # 按包名排序
        for pkg_name in sorted(snapshot.packages.keys()):
            pkg_version = snapshot.packages[pkg_name]
            lines.append(f"{pkg_name}=={pkg_version}")

        return "\n".join(lines)

    def _verify_rollback(self, snapshot: Snapshot) -> VerificationResult:
        """
        验证回滚结果

        Args:
            snapshot: 快照对象

        Returns:
            验证结果
        """
        pip_tool = self._get_pip_tool()
        current_packages = pip_tool.get_installed_packages()

        failed_packages = []

        # 验证每个包的版本
        for pkg_name, expected_version in snapshot.packages.items():
            actual_version = current_packages.get(pkg_name)
            if actual_version != expected_version:
                failed_packages.append(pkg_name)

        passed = len(failed_packages) == 0

        return VerificationResult(
            passed=passed,
            verified_packages=len(snapshot.packages),
            failed_packages=failed_packages,
            checksum_valid=True,  # 加载时已验证
        )

    def generate_solution(
        self,
        conflicts: List,
        strategy: RepairStrategy = RepairStrategy.BALANCED,
    ) -> List[RepairPlan]:
        """
        生成修复方案（简化版）

        Args:
            conflicts: 冲突列表（Conflict 对象或 RepairPlan 对象）
            strategy: 修复策略

        Returns:
            修复方案列表
        """
        # 注：完整的策略实现在 StrategyEngine 中
        # 这里提供简化版本用于基础功能
        plans = []

        for conflict in conflicts:
            # FIX-支持两种对象类型：Conflict 和 RepairPlan
            if hasattr(conflict, 'package_name') and hasattr(conflict, 'target_version'):
                # RepairPlan 对象：直接使用
                plans.append(conflict)
            elif hasattr(conflict, 'suggestion'):
                # Conflict 对象：转换为 RepairPlan
                target_version = conflict.suggestion.split("==")[1]

                # 判断操作类型
                from packaging.version import Version

                current = Version(conflict.installed)
                target = Version(target_version)

                if target > current:
                    action = "upgrade"
                elif target < current:
                    action = "downgrade"
                else:
                    action = "reinstall"

                plan = RepairPlan(
                    package_name=conflict.package,
                    current_version=conflict.installed,
                    target_version=target_version,
                    action=action,
                    reason=conflict.requires,
                    dependencies=[],
                )
                plans.append(plan)
            else:
                self.logger.warning(f"未知对象类型：{type(conflict)}, 跳过")
                continue

        return plans
