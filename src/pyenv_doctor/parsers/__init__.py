# -*- coding: utf-8 -*-
"""
文件依赖解析模块

提供从依赖文件解析依赖声明的功能：
- requirements.txt 解析
- pyproject.toml 解析
"""

from .requirements_parser import RequirementsParser
from .pyproject_parser import PyProjectParser

__all__ = ["RequirementsParser", "PyProjectParser"]
