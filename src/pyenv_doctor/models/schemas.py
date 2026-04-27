# -*- coding: utf-8 -*-
"""
数据结构定义模块

定义 PyEnv Doctor 的核心数据结构:
- PackageInfo: 包信息
- Conflict: 冲突信息
- SandboxResult: 沙箱预演结果
- Snapshot: 环境快照
- RepairPlan: 修复方案
- RepairResult: 修复结果
- RollbackResult: 回滚结果
- RepairStrategy: 修复策略枚举
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from packaging.requirements import Requirement
from packaging.version import Version


@dataclass
class PackageInfo:
    """
    包信息数据结构

    属性:
        name: 包名称，非空，长度 1-200，仅允许字母、数字、下划线、连字符
        version: 包版本号，符合 PEP 440 版本格式
        requires: 依赖列表，每项符合依赖声明格式
    """

    name: str
    version: str
    requires: List[str] = field(default_factory=list)

    def __post_init__(self):
        """字段校验"""
        # 校验包名格式
        if not self.name or len(self.name) > 200:
            raise ValueError("Invalid package name: length must be 1-200")
        # 支持包含点号的合法包名（如 pdfminer.six, ruamel.yaml）
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9_.-]*[a-zA-Z0-9])?$", self.name):
            raise ValueError(f"Invalid package name format: {self.name}")

        # 校验版本号格式
        try:
            Version(self.version)
        except Exception as e:
            raise ValueError(f"Invalid version format: {self.version}") from e

        # 校验依赖声明格式
        for req_str in self.requires:
            try:
                Requirement(req_str)
            except Exception as e:
                raise ValueError(f"Invalid requirement format: {req_str}") from e


@dataclass
class Conflict:
    """
    冲突信息数据结构

    属性:
        package: 存在冲突的包名称
        requires: 依赖要求字符串
        installed: 当前已安装版本
        suggestion: 修复建议，格式为 包名==版本号
    """

    package: str
    requires: str
    installed: str
    suggestion: str

    def __post_init__(self):
        """字段校验"""
        # 校验包名非空
        if not self.package:
            raise ValueError("Package name cannot be empty")

        # 校验依赖声明格式
        try:
            Requirement(self.requires)
        except Exception as e:
            raise ValueError(f"Invalid requirement format: {self.requires}") from e

        # 校验已安装版本格式
        try:
            Version(self.installed)
        except Exception as e:
            raise ValueError(f"Invalid installed version format: {self.installed}") from e

        # 校验修复建议格式
        if not re.match(r"^[a-zA-Z0-9_-]+==.+$", self.suggestion):
            raise ValueError(f"Invalid suggestion format: {self.suggestion}")


@dataclass
class SandboxResult:
    """
    沙箱预演结果数据结构

    属性:
        scheme: 修复方案，格式为 包名==版本号
        success: 预演是否成功
        error: 错误信息，成功时为 None
    """

    scheme: str
    success: bool
    error: Optional[str] = None

    def __post_init__(self):
        """字段校验"""
        # 校验修复方案格式
        if not re.match(r"^[a-zA-Z0-9_-]+==.+$", self.scheme):
            raise ValueError(f"Invalid scheme format: {self.scheme}")

        # 校验成功时 error 必须为 None
        if self.success and self.error is not None:
            raise ValueError("Error must be None when success is True")


# ============== Snapshot Layer 数据结构 ==============


class RepairStrategy(Enum):
    """
    修复策略枚举

    枚举值:
        CONSERVATIVE: 保守策略 - 只降级
        BALANCED: 平衡策略 - 最小改动（默认）
        AGGRESSIVE: 激进策略 - 升最新
    """
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class Snapshot:
    """
    环境快照数据结构

    属性:
        id: 快照 ID，格式：YYYYMMDD_HHMMSS_random(6)
        timestamp: 创建时间，datetime 对象
        label: 用户标签（可选），最大长度 50 字符
        python_version: Python 版本号，格式：主版本。次版本。补丁版本
        venv_path: 虚拟环境路径（可选），绝对路径
        packages: 包版本字典，{包名：版本}
        total_packages: 包总数
        checksum: SHA256 校验和，格式：sha256:hex(64)
        is_temporary: 是否为临时快照
    """

    id: str
    timestamp: datetime
    label: Optional[str]
    python_version: str
    venv_path: Optional[str]
    packages: Dict[str, str]
    total_packages: int
    checksum: str
    is_temporary: bool

    def __post_init__(self):
        """字段校验"""
        # 校验快照 ID 格式
        if not re.match(r"^\d{8}_\d{6}_[a-z0-9]{6}$", self.id):
            raise ValueError(f"Invalid snapshot ID format: {self.id}")

        # 校验标签格式（如果存在）
        if self.label is not None:
            if len(self.label) > 50:
                raise ValueError(f"Label too long: {len(self.label)} > 50")
            if not re.match(r"^[a-zA-Z0-9_-]{0,50}$", self.label):
                raise ValueError(f"Invalid label format: {self.label}")

        # 校验 Python 版本号格式
        if not re.match(r"^\d+\.\d+\.\d+$", self.python_version):
            raise ValueError(f"Invalid python version format: {self.python_version}")

        # 校验包总数
        if self.total_packages < 0:
            raise ValueError(f"Invalid total_packages: {self.total_packages}")

        # 校验校验和格式（允许空字符串，用于创建快照时）
        if self.checksum and not re.match(r"^sha256:[a-f0-9]{64}$", self.checksum):
            raise ValueError(f"Invalid checksum format: {self.checksum}")

    def to_dict(self) -> Dict:
        """转换为字典（用于 JSON 序列化）"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "label": self.label,
            "python_version": self.python_version,
            "venv_path": self.venv_path,
            "packages": self.packages,
            "total_packages": self.total_packages,
            "checksum": self.checksum,
            "is_temporary": self.is_temporary,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Snapshot":
        """从字典创建"""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            label=data.get("label"),
            python_version=data["python_version"],
            venv_path=data.get("venv_path"),
            packages=data["packages"],
            total_packages=data["total_packages"],
            checksum=data["checksum"],
            is_temporary=data["is_temporary"],
        )


@dataclass
class RepairPlan:
    """
    单个包的修复方案

    属性:
        package_name: 包名
        current_version: 当前版本
        target_version: 目标版本
        action: 操作类型 [upgrade|downgrade|reinstall]
        reason: 修复原因
        dependencies: 依赖的包列表（用于拓扑排序）
    """

    package_name: str
    current_version: str
    target_version: str
    action: str
    reason: str
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        """字段校验"""
        # 校验包名格式
        if not self.package_name:
            raise ValueError("Package name cannot be empty")

        # 校验版本号格式
        try:
            Version(self.current_version)
            Version(self.target_version)
        except Exception as e:
            raise ValueError(f"Invalid version format") from e

        # 校验操作类型
        if self.action not in ["upgrade", "downgrade", "reinstall"]:
            raise ValueError(f"Invalid action: {self.action}")

    def to_command(self) -> str:
        """生成 pip 命令"""
        return f"pip install {self.package_name}=={self.target_version}"


@dataclass
class RepairResult:
    """
    修复结果数据结构

    属性:
        success: 是否成功
        repaired: 成功修复的包列表
        failed: 修复失败的包列表
        snapshot_id: 关联的快照 ID
        duration: 耗时（秒）
        strategy: 使用的策略
        rollback_available: 是否可回滚
        cancelled_by_user: 是否被用户取消
    """

    success: bool
    repaired: List[str]
    failed: List[str]
    snapshot_id: str
    duration: float
    strategy: str
    rollback_available: bool
    cancelled_by_user: bool = False

    def __post_init__(self):
        """字段校验"""
        # 校验策略值
        if self.strategy not in ["conservative", "balanced", "aggressive"]:
            raise ValueError(f"Invalid strategy: {self.strategy}")

        # 校验耗时
        if self.duration < 0:
            raise ValueError(f"Invalid duration: {self.duration}")

    def to_report(self) -> str:
        """生成人类可读的报告"""
        if self.cancelled_by_user:
            return "[CANCELLED] 用户取消修复"

        if self.success:
            lines = [
                "[SUCCESS] 修复完成！",
                f"  - 修复了 {len(self.repaired)} 个冲突",
                f"  - 耗时：{self.duration:.1f}秒",
                f"  - 策略：{self.strategy}",
                f"  - 快照 ID: {self.snapshot_id}",
                f"  - 回滚命令：pyenv-doctor snapshot rollback {self.snapshot_id}",
            ]
            return "\n".join(lines)
        else:
            lines = [
                "[FAILED] 修复失败",
                f"  - 成功：{len(self.repaired)} 个",
                f"  - 失败：{len(self.failed)} 个",
                f"  - 已自动回滚到快照 {self.snapshot_id}",
            ]
            return "\n".join(lines)


@dataclass
class RollbackResult:
    """
    回滚结果数据结构

    属性:
        success: 是否成功
        snapshot_id: 回滚的快照 ID
        packages_restored: 恢复的包数量
        duration: 耗时（秒）
        verified: 是否验证通过
    """

    success: bool
    snapshot_id: str
    packages_restored: int
    duration: float
    verified: bool

    def __post_init__(self):
        """字段校验"""
        # 校验恢复包数量
        if self.packages_restored < 0:
            raise ValueError(f"Invalid packages_restored: {self.packages_restored}")

        # 校验耗时
        if self.duration < 0:
            raise ValueError(f"Invalid duration: {self.duration}")

    def to_report(self) -> str:
        """生成报告"""
        if self.success:
            return (
                f"[OK] 回滚成功！\n"
                f"  - 恢复 {self.packages_restored} 个包\n"
                f"  - 耗时：{self.duration:.1f}秒\n"
                f"  - 验证：{'通过' if self.verified else '未验证'}"
            )
        else:
            return f"[FAILED] 回滚失败"


@dataclass
class RollbackPreview:
    """
    回滚预览数据结构

    属性:
        snapshot_id: 快照 ID
        changes: 包变更列表
        total_changes: 变更总数
    """

    snapshot_id: str
    changes: List["PackageChange"]
    total_changes: int

    def to_text(self) -> str:
        """生成预览文本"""
        lines = [
            f"[DRY-RUN] 回滚预览:",
            f"将恢复以下包 ({self.total_changes} 个):",
        ]
        for change in self.changes:
            lines.append(
                f"  - {change.package_name}: {change.current_version} → {change.target_version}"
            )
        return "\n".join(lines)


@dataclass
class PackageChange:
    """
    包变更数据结构

    属性:
        package_name: 包名
        current_version: 当前版本
        target_version: 目标版本
    """

    package_name: str
    current_version: str
    target_version: str


@dataclass
class VerificationResult:
    """
    验证结果数据结构

    属性:
        passed: 是否通过
        verified_packages: 验证的包数量
        failed_packages: 验证失败的包列表
        checksum_valid: 校验和是否有效
    """

    passed: bool
    verified_packages: int
    failed_packages: List[str]
    checksum_valid: bool

    def __post_init__(self):
        """字段校验"""
        # 校验包数量
        if self.verified_packages < 0:
            raise ValueError(f"Invalid verified_packages: {self.verified_packages}")

    def to_report(self) -> str:
        """生成报告"""
        if self.passed:
            return f"[VERIFY] 验证通过 ({self.verified_packages} 个包)"
        else:
            return (
                f"[VERIFY] 验证失败\n"
                f"  - 验证：{self.verified_packages} 个包\n"
                f"  - 失败：{self.failed_packages}"
            )
