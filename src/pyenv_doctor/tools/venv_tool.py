# -*- coding: utf-8 -*-
"""
VenvTool - venv 操作封装

封装虚拟环境创建和管理。

@skill venv操作封装
"""

import venv
from pathlib import Path


class VenvTool:
    """
    venv 操作工具

    封装虚拟环境创建和管理。

    属性:
        name: 工具名称，固定值 "venv"
    """

    name: str = "venv"

    def __init__(self):
        """初始化 VenvTool"""
        pass

    def execute(self, path: str, with_pip: bool = True) -> str:
        """
        创建虚拟环境

        参数:
            path: 虚拟环境路径
            with_pip: 是否安装 pip

        返回:
            str: 操作结果

        示例:
            >>> tool = VenvTool()
            >>> result = tool.execute("/tmp/myenv")
        """
        try:
            venv.create(path, with_pip=with_pip)
            return f"Created venv at {path}"
        except Exception as e:
            return f"Error: {str(e)}"
