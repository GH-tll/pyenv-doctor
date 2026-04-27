# -*- coding: utf-8 -*-
"""
ConflictSolver Agent - 冲突检测代理

职责: 检测依赖版本冲突

@skill 冲突检测
"""

import logging
from typing import List

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from ..models.schemas import Conflict, PackageInfo


class ConflictSolver:
    """
    冲突检测 Agent

    检测已安装包之间的依赖版本冲突。

    属性:
        name: Agent 名称，固定值 "ConflictSolver"
    """

    name: str = "ConflictSolver"

    def __init__(self):
        """初始化 ConflictSolver"""
        self.logger = logging.getLogger(__name__)

    def detect(self, packages: List[PackageInfo]) -> List[Conflict]:
        """
        检测依赖冲突

        分析已安装包的依赖关系，检测版本冲突。

        参数:
            packages: 包信息列表

        返回:
            List[Conflict]: 冲突列表

        示例:
            >>> solver = ConflictSolver()
            >>> conflicts = solver.detect(packages)
            >>> for conflict in conflicts:
            ...     print(f"{conflict.package} requires {conflict.requires}")
        """
        conflicts: List[Conflict] = []

        # 空列表直接返回
        if not packages:
            return conflicts

        # 构建已安装包的版本映射（包名小写作为键）
        installed = {}
        for pkg in packages:
            try:
                installed[pkg.name.lower()] = pkg.version
            except Exception as e:
                self.logger.warning(f"跳过无效包 {pkg.name}: {e}")
                continue

        # 遍历每个包的依赖
        for pkg in packages:
            for req_str in pkg.requires:
                try:
                    # 解析依赖声明
                    req = Requirement(req_str)
                    req_name = req.name.lower()

                    # 检查依赖是否已安装
                    if req_name not in installed:
                        # 缺失依赖，不在 MVP 范围内
                        continue

                    # 获取已安装版本
                    installed_version = Version(installed[req_name])

                    # 检查版本是否满足约束
                    if not req.specifier.contains(installed_version):
                        # 存在冲突，生成修复建议
                        suggestion = self._generate_suggestion(req_name, req.specifier)

                        conflict = Conflict(
                            package=pkg.name,
                            requires=req_str,
                            installed=installed[req_name],
                            suggestion=suggestion
                        )
                        conflicts.append(conflict)

                except Exception as e:
                    # 依赖声明格式错误，跳过该依赖
                    self.logger.warning(f"跳过无效依赖声明 {req_str}: {e}")
                    continue

        return conflicts

    def _generate_suggestion(self, name: str, specifier: SpecifierSet) -> str:
        """
        生成修复建议

        根据版本约束生成修复建议。

        参数:
            name: 包名称
            specifier: 版本约束集合

        返回:
            str: 修复建议，格式为 包名==版本号

        示例:
            >>> suggestion = solver._generate_suggestion("numpy", SpecifierSet("<1.24"))
            >>> print(suggestion)
            "numpy==1.23.5"
        """
        # FIX-版本范围解析：综合分析所有约束，找到满足条件的版本
        # 收集所有约束条件
        min_version = None  # 最低版本（>= 或 >）
        max_version = None  # 最高版本（<= 或 <）
        exact_version = None  # 精确版本（==）
        
        for spec in specifier:
            if spec.operator == ">=":
                if min_version is None or Version(spec.version) > min_version:
                    min_version = Version(spec.version)
            elif spec.operator == ">":
                # > 需要比该版本更高，所以最低版本是 spec.version + 微小增量
                # 简化处理：直接使用 spec.version 作为下限参考
                if min_version is None or Version(spec.version) >= min_version:
                    min_version = Version(spec.version)
            elif spec.operator == "<=":
                if max_version is None or Version(spec.version) < max_version:
                    max_version = Version(spec.version)
            elif spec.operator == "<":
                # < 需要比该版本更低，所以最高版本是 spec.version - 微小增量
                # 简化处理：直接使用 spec.version 作为上限参考
                if max_version is None or Version(spec.version) <= max_version:
                    max_version = Version(spec.version)
            elif spec.operator == "==":
                exact_version = Version(spec.version)
                break  # 精确约束优先级最高
            elif spec.operator == "~=":
                # ~= 是兼容版本约束，如 ~=1.4.2 等价于 >=1.4.2, ==1.4.*
                # 简化处理：使用该版本作为最低版本
                if min_version is None or Version(spec.version) > min_version:
                    min_version = Version(spec.version)
        
        # 根据收集的约束生成建议
        if exact_version:
            # 有精确约束，直接使用
            return f"{name}=={exact_version}"
        
        if min_version is not None and max_version is not None:
            # 同时有上下限约束
            if min_version < max_version:
                # 有效范围，使用最低版本（保守策略）
                return f"{name}=={min_version}"
            else:
                # 约束冲突，返回错误
                self.logger.warning(
                    f"约束冲突：{name} 需要 >={min_version} 且 <{max_version}"
                )
                return f"{name} (conflicting constraints)"
        
        if min_version is not None:
            # 只有最低约束，使用最低版本
            return f"{name}=={min_version}"
        
        if max_version is not None:
            # 只有最高约束，需要找一个低于最高版本的版本
            # 简化处理：返回 max_version - 0.0.1（如果可能）
            # 对于主要版本号，直接减 1
            try:
                version_parts = str(max_version).split('.')
                if len(version_parts) >= 1:
                    major = int(version_parts[0])
                    if major > 0:
                        # 构造一个低于 max 的版本
                        if len(version_parts) == 1:
                            return f"{name}=={major - 1}"
                        elif len(version_parts) == 2:
                            return f"{name}=={major - 1}.{version_parts[1]}"
                        else:
                            return f"{name}=={major - 1}.{version_parts[1]}.{version_parts[2]}"
            except Exception:
                pass
            return f"{name}<{max_version}"
        
        # 无有效约束，返回通用建议
        return f"{name} (compatible version)"
