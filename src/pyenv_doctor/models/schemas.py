# -*- coding: utf-8 -*-
"""
数据结构定义模块

定义 PyEnv Doctor 的核心数据结构:
- PackageInfo: 包信息
- Conflict: 冲突信息
- SandboxResult: 沙箱预演结果
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

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
