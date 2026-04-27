# -*- coding: utf-8 -*-
"""
CLI 命令包

包含所有 CLI 命令组：
- diagnose: 诊断命令
- snapshot: 快照管理命令组
"""

# 从主模块导入 main 函数，以便入口点可以正常工作
from .main import main

__all__ = ["main"]
