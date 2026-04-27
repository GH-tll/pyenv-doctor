# -*- coding: utf-8 -*-
"""
Snapshot 模块

提供环境快照的创建、存储、管理、回滚功能。

核心组件:
- SnapshotStorage: 快照存储引擎，负责持久化、校验
- SnapshotManager: 快照管理器，负责业务逻辑
"""

from .manager import SnapshotManager
from .storage import SnapshotStorage

__all__ = ["SnapshotManager", "SnapshotStorage"]
