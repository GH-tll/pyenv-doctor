# -*- coding: utf-8 -*-
"""
EnvScanner Agent - 环境扫描代理

职责: 扫描当前 Python 环境已安装包

@skill 环境扫描
"""

import logging
from typing import List

from importlib.metadata import distributions

from ..models.schemas import PackageInfo


class EnvScanner:
    """
    环境扫描 Agent

    扫描当前 Python 环境中已安装的所有包及其依赖关系。

    属性:
        name: Agent 名称，固定值 "EnvScanner"
    """

    name: str = "EnvScanner"

    def __init__(self):
        """初始化 EnvScanner"""
        self.logger = logging.getLogger(__name__)

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
            for dist in distributions():
                try:
                    # 获取包名
                    name = dist.metadata.get("Name")
                    if not name:
                        self.logger.warning(f"跳过无名称的包: {dist}")
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
