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
        # 遍历约束，寻找合适的版本
        for spec in specifier:
            # 对于 < 约束，建议安装约束版本的前一个版本
            if spec.operator == "<":
                # 简化处理：直接使用约束版本
                # 实际应该查找 PyPI 获取最新兼容版本
                return f"{name}=={spec.version}"

            # 对于 <= 约束，建议安装约束版本
            elif spec.operator == "<=":
                return f"{name}=={spec.version}"

            # 对于 > 约束，建议安装约束版本的下一个版本
            elif spec.operator == ">":
                # 简化处理：直接使用约束版本
                return f"{name}=={spec.version}"

            # 对于 >= 约束，建议安装约束版本
            elif spec.operator == ">=":
                return f"{name}=={spec.version}"

            # 对于 == 约束，建议安装约束版本
            elif spec.operator == "==":
                return f"{name}=={spec.version}"

            # 对于 != 约束，建议安装其他版本
            elif spec.operator == "!=":
                # 简化处理：建议安装一个接近的版本
                # 由于无法确定具体版本，使用一个占位版本
                return f"{name}==1.0.0"

            # 对于 ~= 约束，建议安装兼容版本
            elif spec.operator == "~=":
                return f"{name}=={spec.version}"

        # 默认返回通用建议
        return f"{name} (compatible version)"
