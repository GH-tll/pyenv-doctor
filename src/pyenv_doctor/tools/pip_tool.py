# -*- coding: utf-8 -*-
"""
PipTool - pip 命令封装

封装 pip 命令执行，提供统一的接口。

@skill pip命令封装
"""

import subprocess


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
