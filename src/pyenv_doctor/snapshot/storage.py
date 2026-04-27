# -*- coding: utf-8 -*-
"""
快照存储引擎

负责快照的持久化存储、读取、校验。
"""

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..models.schemas import Snapshot


class SnapshotStorageError(Exception):
    """存储操作异常基类"""

    pass


class SnapshotNotFoundError(SnapshotStorageError):
    """快照不存在异常"""

    pass


class ChecksumError(SnapshotStorageError):
    """校验和验证失败异常"""

    pass


class SnapshotStorage:
    """
    快照存储引擎

    职责：
    - 保存快照到磁盘
    - 从磁盘加载快照
    - 校验快照完整性
    - 删除快照
    - 列出所有快照
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化存储引擎

        Args:
            storage_dir: 存储目录，默认为 ~/.pyenv-doctor/snapshots
        """
        if storage_dir is None:
            # 使用默认目录
            home_dir = Path.home()
            storage_dir = home_dir / ".pyenv-doctor" / "snapshots"
        else:
            storage_dir = Path(storage_dir)

        self.storage_dir = storage_dir

        # 确保存储目录存在
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, snapshot: Snapshot) -> str:
        """
        保存快照到磁盘

        Args:
            snapshot: 快照对象

        Returns:
            保存的文件路径

        异常:
            SnapshotStorageError: 保存失败时抛出
        """
        try:
            # 构建文件路径
            file_path = self.storage_dir / f"{snapshot.id}.json"

            # 序列化为 JSON
            data = snapshot.to_dict()
            json_str = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)

            # 原子写入：先写临时文件，再重命名
            self._atomic_write(file_path, json_str)

            return str(file_path)

        except Exception as e:
            raise SnapshotStorageError(f"保存快照失败：{str(e)}") from e

    def load(self, snapshot_id: str) -> Snapshot:
        """
        从磁盘加载快照

        Args:
            snapshot_id: 快照 ID

        Returns:
            快照对象

        异常:
            SnapshotNotFoundError: 快照不存在
            ChecksumError: 校验和验证失败
        """
        try:
            # 构建文件路径
            file_path = self.storage_dir / f"{snapshot_id}.json"

            # 检查文件是否存在
            if not file_path.exists():
                raise SnapshotNotFoundError(f"快照 {snapshot_id} 不存在")

            # 读取文件
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 创建快照对象
            snapshot = Snapshot.from_dict(data)

            # 验证校验和
            if not self._verify_checksum(data):
                raise ChecksumError(f"快照 {snapshot_id} 校验和验证失败，可能已损坏")

            return snapshot

        except SnapshotNotFoundError:
            raise
        except ChecksumError:
            raise
        except json.JSONDecodeError as e:
            raise SnapshotStorageError(f"快照文件格式错误：{str(e)}") from e
        except Exception as e:
            raise SnapshotStorageError(f"加载快照失败：{str(e)}") from e

    def exists(self, snapshot_id: str) -> bool:
        """
        检查快照是否存在

        Args:
            snapshot_id: 快照 ID

        Returns:
            是否存在
        """
        file_path = self.storage_dir / f"{snapshot_id}.json"
        return file_path.exists()

    def delete(self, snapshot_id: str) -> None:
        """
        删除快照

        Args:
            snapshot_id: 快照 ID

        异常:
            SnapshotNotFoundError: 快照不存在
            SnapshotStorageError: 删除失败
        """
        try:
            file_path = self.storage_dir / f"{snapshot_id}.json"

            if not file_path.exists():
                raise SnapshotNotFoundError(f"快照 {snapshot_id} 不存在")

            file_path.unlink()

        except SnapshotNotFoundError:
            raise
        except Exception as e:
            raise SnapshotStorageError(f"删除快照失败：{str(e)}") from e

    def list_all(self) -> List[Snapshot]:
        """
        列出所有快照，按时间倒序

        Returns:
            快照列表

        异常:
            SnapshotStorageError: 列出失败
        """
        try:
            snapshots = []

            # 遍历所有快照文件
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    # 提取快照 ID
                    snapshot_id = file_path.stem

                    # 加载快照
                    snapshot = self.load(snapshot_id)
                    snapshots.append(snapshot)

                except (SnapshotNotFoundError, ChecksumError, SnapshotStorageError):
                    # 跳过损坏的快照
                    continue

            # 按时间倒序排序
            snapshots.sort(key=lambda s: s.timestamp, reverse=True)

            return snapshots

        except Exception as e:
            raise SnapshotStorageError(f"列出快照失败：{str(e)}") from e

    def calculate_checksum(self, data: Dict) -> str:
        """
        计算 SHA256 校验和

        Args:
            data: 快照字典数据

        Returns:
            SHA256 校验和字符串（格式：sha256:xxx）
        """
        # 序列化时按键排序，确保一致性
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        sha256_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
        return f"sha256:{sha256_hash}"

    def _verify_checksum(self, data: Dict) -> bool:
        """
        验证校验和

        Args:
            data: 快照字典数据（包含 checksum 字段）

        Returns:
            校验和是否有效
        """
        # 提取存储的校验和
        stored_checksum = data.get("checksum")
        if not stored_checksum:
            return False

        # 计算预期校验和（排除 checksum 字段）
        data_copy = data.copy()
        del data_copy["checksum"]
        expected_checksum = self.calculate_checksum(data_copy)

        return stored_checksum == expected_checksum

    def _atomic_write(self, file_path: Path, content: str):
        """
        原子写入文件

        先写临时文件，再重命名，确保写入的原子性

        Args:
            file_path: 目标文件路径
            content: 文件内容
        """
        # 创建临时文件
        fd, tmp_path = tempfile.mkstemp(dir=self.storage_dir, suffix=".tmp")

        try:
            # 写入临时文件
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)

            # 重命名为目标文件
            os.replace(tmp_path, file_path)

        except Exception:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def get_storage_info(self) -> Dict:
        """
        获取存储信息

        Returns:
            存储信息字典
        """
        # 统计快照数量和总大小
        total_size = 0
        snapshot_count = 0

        for file_path in self.storage_dir.glob("*.json"):
            total_size += file_path.stat().st_size
            snapshot_count += 1

        return {
            "storage_dir": str(self.storage_dir),
            "snapshot_count": snapshot_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
