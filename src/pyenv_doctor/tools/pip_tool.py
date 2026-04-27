# -*- coding: utf-8 -*-
"""
PipTool - pip 命令封装

封装 pip 命令执行，提供统一的接口。

@skill pip 命令封装
"""

import logging
import subprocess

# 配置日志
logger = logging.getLogger(__name__)


class PipTool:
    """
    pip 命令工具

    封装 pip 命令执行。

    属性:
        name: 工具名称，固定值 "pip"
    """

    name: str = "pip"

    def __init__(self):
        """初始化 PipTool"""
        pass

    def execute(self, command: str) -> str:
        """
        执行 pip 命令

        参数:
            command: pip 命令参数

        返回:
            str: 命令输出

        示例:
            >>> tool = PipTool()
            >>> output = tool.execute("list")
        """
        try:
            result = subprocess.run(
                ["pip"] + command.split(),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"

    def get_installed_packages(self) -> dict:
        """
        获取当前已安装的包

        返回:
            dict: 包名到版本的字典 {包名：版本号}

        示例:
            >>> tool = PipTool()
            >>> packages = tool.get_installed_packages()
            >>> print(packages.get("numpy"))
        """
        try:
            # FIX-添加超时保护：避免 pip list 卡住
            result = subprocess.run(
                ["pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 30 秒超时
            )
            
            packages = {}
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    name, version = line.split("==")
                    packages[name.lower()] = version.strip()
            
            return packages
        except subprocess.TimeoutExpired:
            # 超时回退方案：使用 pip freeze
            try:
                result = subprocess.run(
                    ["pip", "freeze"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30
                )
                packages = {}
                for line in result.stdout.strip().split("\n"):
                    if "==" in line:
                        name, version = line.split("==")
                        packages[name.lower()] = version.strip()
                return packages
            except Exception:
                return {}
        except subprocess.CalledProcessError as e:
            logger.debug(f"pip list 失败：{e.stderr}")
            return {}
        except Exception as e:
            logger.debug(f"获取包列表异常：{e}")
            return {}

    def install_package(self, package_name: str, version: str = None) -> bool:
        """
        安装包

        参数:
            package_name: 包名
            version: 版本号（可选）

        返回:
            bool: 安装是否成功

        示例:
            >>> tool = PipTool()
            >>> success = tool.install_package("numpy", "1.24.0")
        """
        try:
            spec = f"{package_name}=={version}" if version else package_name
            result = subprocess.run(
                ["pip", "install", spec],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
        except Exception:
            return False
