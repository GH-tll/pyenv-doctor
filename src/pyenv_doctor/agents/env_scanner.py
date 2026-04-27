# -*- coding: utf-8 -*-
"""
EnvScanner Agent - 环境扫描代理

职责: 扫描当前 Python 环境已安装包

@skill 环境扫描
"""

import logging
import sys
import site
from typing import List, Set
from pathlib import Path
from importlib.metadata import distributions, DistributionFinder

from ..models.schemas import PackageInfo


class EnvScanner:
    """
    环境扫描 Agent

    扫描当前 Python 环境中已安装的所有包及其依赖关系。

    属性:
        name: Agent 名称，固定值 "EnvScanner"
    """

    # FIX-基础包过滤: 定义需要排除的基础包集合
    BASE_PACKAGES = {"pip", "setuptools", "wheel", "pkg_resources"}

    name: str = "EnvScanner"

    def __init__(self, include_base: bool = True, only_user: bool = False):
        """
        初始化 EnvScanner

        参数:
            include_base: 是否包含基础包，默认 True
            only_user: 是否仅扫描用户安装的包（快速模式），默认 False
        """
        self.logger = logging.getLogger(__name__)
        self.include_base = include_base
        self.only_user = only_user

    def _get_current_env_paths(self) -> Set[str]:
        """
        获取当前 Python 环境的包路径

        返回:
            当前环境的包路径集合（标准化为小写字符串）
        """
        paths = set()

        if sys.prefix != sys.base_prefix:
            # 虚拟环境：优先使用虚拟环境的路径
            venv_site = str((Path(sys.prefix) / "Lib" / "site-packages").resolve())
            paths.add(venv_site.lower())
            # 也包含用户 site-packages
            user_site = site.getusersitepackages()
            if user_site:
                paths.add(str(Path(user_site).resolve()).lower())
        else:
            # 全局环境：使用 site-packages
            for p in site.getsitepackages():
                paths.add(str(Path(p).resolve()).lower())
            # 包含用户 site-packages
            user_site = site.getusersitepackages()
            if user_site:
                paths.add(str(Path(user_site).resolve()).lower())

        self.logger.debug(f"当前环境路径：{paths}")
        return paths

    def _is_in_current_env(self, dist) -> bool:
        """
        检查包是否属于当前环境

        参数:
            dist: Distribution 对象

        返回:
            是否在当前环境中
        """
        # 获取包的父目录
        parent = dist._path.parent if hasattr(dist, '_path') and dist._path else None
        if not parent:
            return True  # 无法确定，默认包含

        parent_str = str(parent.resolve()).lower()
        env_paths = self._get_current_env_paths()

        # 检查包的父目录是否在当前环境路径中
        return any(parent_str.startswith(p) for p in env_paths)

    def scan(self) -> List[PackageInfo]:
        """
        扫描当前环境已安装包

        返回当前环境中所有已安装包的列表，包含包名、版本和依赖信息。

        返回:
            List[PackageInfo]: 包信息列表

        异常:
            PermissionError: 权限不足时抛出

        示例:
            >>> scanner = EnvScanner()
            >>> packages = scanner.scan()
            >>> for pkg in packages:
            ...     print(f"{pkg.name}=={pkg.version}")
        """
        packages: List[PackageInfo] = []

        try:
            # 遍历所有已安装的分发包
            seen_names = set()
            for dist in distributions():
                try:
                    # 获取包名
                    name = dist.metadata.get("Name")
                    if not name:
                        self.logger.warning(f"跳过无名称的包: {dist}")
                        continue

                    # 统一转换为小写用于匹配
                    name_lower = name.lower()

                    # 去重
                    if name_lower in seen_names:
                        continue
                    seen_names.add(name_lower)

                    # FIX-快速模式支持: 仅扫描当前环境的包
                    if self.only_user and not self._is_in_current_env(dist):
                        self.logger.debug(f"跳过外部环境的包: {name}")
                        continue

                    # FIX-基础包过滤: 排除基础包（快速模式或仅用户模式）
                    if (self.only_user or not self.include_base) and name_lower in self.BASE_PACKAGES:
                        self.logger.debug(f"跳过基础包: {name}")
                        continue

                    # 获取版本号
                    version = dist.version
                    if not version:
                        self.logger.warning(f"跳过无版本的包: {name}")
                        continue

                    # 获取依赖列表
                    requires = []
                    if dist.requires:
                        for req in dist.requires:
                            # 将 Requirement 对象转换为字符串
                            requires.append(str(req))

                    # 创建 PackageInfo 对象
                    package_info = PackageInfo(
                        name=name,
                        version=version,
                        requires=requires
                    )
                    packages.append(package_info)

                except Exception as e:
                    # 元数据读取失败，跳过该包
                    self.logger.warning(f"跳过损坏的包: {e}")
                    continue

        except PermissionError as e:
            # 权限不足，抛出异常
            self.logger.error(f"权限不足: {e}")
            raise
        except Exception as e:
            # 其他异常，记录日志并返回已扫描的包
            self.logger.error(f"扫描环境时发生错误: {e}")

        return packages
