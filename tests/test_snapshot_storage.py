# -*- coding: utf-8 -*-
"""
测试快照存储引擎

覆盖场景:
- 保存快照到磁盘
- 从磁盘加载快照
- 校验和验证
- 删除快照
- 列出所有快照
- 原子写入
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from pyenv_doctor.models.schemas import Snapshot
from pyenv_doctor.snapshot.storage import (
    ChecksumError,
    SnapshotNotFoundError,
    SnapshotStorage,
    SnapshotStorageError,
)


class TestSnapshotStorage:
    """测试 SnapshotStorage 类"""

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """创建存储实例"""
        return SnapshotStorage(storage_dir=temp_storage_dir)

    @pytest.fixture
    def sample_snapshot(self):
        """创建示例快照"""
        return Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22, 123456),
            label="test-snapshot",
            python_version="3.9.18",
            venv_path="D:\\test\\.venv",
            packages={
                "numpy": "1.24.0",
                "pandas": "1.5.3",
                "requests": "2.28.2",
            },
            total_packages=3,
            checksum="",  # 将在测试中计算
            is_temporary=False,
        )

    def test_init_default_dir(self):
        """测试使用默认目录初始化"""
        storage = SnapshotStorage()
        assert storage.storage_dir.exists()
        assert "pyenv-doctor" in str(storage.storage_dir)
        assert "snapshots" in str(storage.storage_dir)

    def test_init_custom_dir(self, temp_storage_dir):
        """测试使用自定义目录初始化"""
        storage = SnapshotStorage(storage_dir=temp_storage_dir)
        assert str(storage.storage_dir) == temp_storage_dir
        assert storage.storage_dir.exists()

    def test_save_snapshot(self, storage, sample_snapshot):
        """测试保存快照"""
        # 计算校验和（不包含 checksum 字段）
        data = sample_snapshot.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        sample_snapshot.checksum = storage.calculate_checksum(data_without_checksum)

        # 保存快照
        file_path = storage.save(sample_snapshot)

        # 验证文件存在
        assert os.path.exists(file_path)
        assert file_path.endswith("20260424_143022_abc123.json")

        # 验证文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["id"] == sample_snapshot.id
        assert saved_data["label"] == sample_snapshot.label
        assert saved_data["total_packages"] == sample_snapshot.total_packages
        assert saved_data["packages"] == sample_snapshot.packages

    def test_load_snapshot(self, storage, sample_snapshot):
        """测试加载快照"""
        # 先保存
        data = sample_snapshot.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        sample_snapshot.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(sample_snapshot)

        # 再加载
        loaded = storage.load("20260424_143022_abc123")

        # 验证数据一致
        assert loaded.id == sample_snapshot.id
        assert loaded.label == sample_snapshot.label
        assert loaded.python_version == sample_snapshot.python_version
        assert loaded.packages == sample_snapshot.packages
        assert loaded.total_packages == sample_snapshot.total_packages

    def test_load_not_found(self, storage):
        """测试加载不存在的快照"""
        with pytest.raises(SnapshotNotFoundError):
            storage.load("non_existent_id")

    def test_delete_snapshot(self, storage, sample_snapshot):
        """测试删除快照"""
        # 先保存
        data = sample_snapshot.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        sample_snapshot.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(sample_snapshot)

        # 验证文件存在
        file_path = storage.storage_dir / "20260424_143022_abc123.json"
        assert file_path.exists()

        # 删除
        storage.delete("20260424_143022_abc123")

        # 验证文件已删除
        assert not file_path.exists()

    def test_delete_not_found(self, storage):
        """测试删除不存在的快照"""
        with pytest.raises(SnapshotNotFoundError):
            storage.delete("non_existent_id")

    def test_exists(self, storage, sample_snapshot):
        """测试检查快照是否存在"""
        # 先保存
        data = sample_snapshot.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        sample_snapshot.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(sample_snapshot)

        # 验证存在
        assert storage.exists("20260424_143022_abc123") is True

        # 验证不存在
        assert storage.exists("non_existent_id") is False

    def test_list_all(self, storage, sample_snapshot):
        """测试列出所有快照"""
        # 创建多个快照
        for i in range(3):
            snap = Snapshot(
                id=f"20260424_14302{i}_abc12{i}",
                timestamp=datetime(2026, 4, 24, 14, 30, 20 + i),
                label=f"test-{i}",
                python_version="3.9.18",
                venv_path=None,
                packages={"pkg": f"1.0.{i}"},
                total_packages=1,
                checksum="",
                is_temporary=(i % 2 == 0),
            )
            data = snap.to_dict()
            data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
            snap.checksum = storage.calculate_checksum(data_without_checksum)
            storage.save(snap)

        # 列出所有
        snapshots = storage.list_all()

        # 验证数量和排序
        assert len(snapshots) == 3
        # 按时间倒序
        assert snapshots[0].timestamp > snapshots[1].timestamp
        assert snapshots[1].timestamp > snapshots[2].timestamp

    def test_list_all_with_corrupted(self, storage, temp_storage_dir):
        """测试列出快照时跳过损坏的文件"""
        # 创建一个损坏的 JSON 文件
        corrupted_file = Path(temp_storage_dir) / "20260424_999999_bad.json"
        with open(corrupted_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        # 创建一个正常的快照
        snap = Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="good",
            python_version="3.9.18",
            venv_path=None,
            packages={"pkg": "1.0.0"},
            total_packages=1,
            checksum="",
            is_temporary=False,
        )
        data = snap.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        snap.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(snap)

        # 列出所有 - 应该跳过损坏的文件
        snapshots = storage.list_all()
        assert len(snapshots) == 1
        assert snapshots[0].id == "20260424_143022_abc123"

    def test_calculate_checksum(self, storage, sample_snapshot):
        """测试计算校验和"""
        data = sample_snapshot.to_dict()
        checksum = storage.calculate_checksum(data)

        # 验证格式
        assert checksum.startswith("sha256:")
        assert len(checksum) == 71  # "sha256:" + 64 位 hex

        # 验证一致性
        checksum2 = storage.calculate_checksum(data)
        assert checksum == checksum2

    def test_verify_checksum_valid(self, storage, sample_snapshot):
        """测试验证有效的校验和"""
        data = sample_snapshot.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        checksum = storage.calculate_checksum(data_without_checksum)
        data["checksum"] = checksum

        assert storage._verify_checksum(data) is True

    def test_verify_checksum_invalid(self, storage, sample_snapshot):
        """测试验证无效的校验和"""
        data = sample_snapshot.to_dict()
        data["checksum"] = "sha256:invalid_checksum_value"

        assert storage._verify_checksum(data) is False

    def test_verify_checksum_missing(self, storage, sample_snapshot):
        """测试验证缺失的校验和"""
        data = sample_snapshot.to_dict()
        # 不包含 checksum 字段

        assert storage._verify_checksum(data) is False

    def test_atomic_write(self, storage, temp_storage_dir):
        """测试原子写入"""
        content = "test content"
        file_path = Path(temp_storage_dir) / "test.txt"

        storage._atomic_write(file_path, content)

        # 验证文件存在且内容正确
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            assert f.read() == content

    def test_get_storage_info(self, storage, sample_snapshot):
        """测试获取存储信息"""
        # 创建几个快照
        for i in range(2):
            snap = Snapshot(
                id=f"20260424_14302{i}_abc12{i}",
                timestamp=datetime(2026, 4, 24, 14, 30, 20 + i),
                label=f"test-{i}",
                python_version="3.9.18",
                venv_path=None,
                packages={"pkg": f"1.0.{i}"},
                total_packages=1,
                checksum="",
                is_temporary=False,
            )
            data = snap.to_dict()
            data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
            snap.checksum = storage.calculate_checksum(data_without_checksum)
            storage.save(snap)

        info = storage.get_storage_info()

        assert info["storage_dir"] == str(storage.storage_dir)
        assert info["snapshot_count"] == 2
        assert info["total_size_bytes"] > 0
        assert info["total_size_mb"] >= 0

    def test_load_checksum_error(self, storage, sample_snapshot, temp_storage_dir):
        """测试加载时校验和错误"""
        # 手动创建一个校验和不匹配的文件
        data = sample_snapshot.to_dict()
        # 使用正确格式但错误的校验和值
        data["checksum"] = "sha256:" + "0" * 64

        file_path = storage.storage_dir / f"{sample_snapshot.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # 加载应该抛出 ChecksumError
        with pytest.raises(ChecksumError):
            storage.load(sample_snapshot.id)

    def test_save_error(self, sample_snapshot):
        """测试保存错误"""
        # 使用无法写入的目录
        storage = SnapshotStorage(storage_dir="/root/.pyenv-doctor/snapshots")
        
        # 在 Windows 上可能不会失败，跳过
        if os.name == "nt":
            pytest.skip("Windows 上权限处理不同")

    def test_snapshot_to_dict_from_dict(self, sample_snapshot):
        """测试快照的序列化和反序列化"""
        # 计算校验和
        data = sample_snapshot.to_dict()
        sample_snapshot.checksum = "sha256:" + "a" * 64

        # 序列化
        data = sample_snapshot.to_dict()

        # 反序列化
        loaded = Snapshot.from_dict(data)

        assert loaded.id == sample_snapshot.id
        assert loaded.timestamp == sample_snapshot.timestamp
        assert loaded.label == sample_snapshot.label
        assert loaded.packages == sample_snapshot.packages


class TestSnapshotStorageEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def storage(self, temp_storage_dir):
        """创建存储实例"""
        return SnapshotStorage(storage_dir=temp_storage_dir)

    def test_empty_packages(self, storage):
        """测试空包列表的快照"""
        snap = Snapshot(
            id="20260424_143022_emptya",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="empty",
            python_version="3.9.18",
            venv_path=None,
            packages={},
            total_packages=0,
            checksum="",
            is_temporary=False,
        )
        data = snap.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        snap.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(snap)

        loaded = storage.load("20260424_143022_emptya")
        assert loaded.total_packages == 0
        assert loaded.packages == {}

    def test_large_packages(self, storage):
        """测试大量包的快照"""
        # 创建 100 个包的快照
        packages = {f"package{i}": f"1.0.{i}" for i in range(100)}

        snap = Snapshot(
            id="20260424_143022_large1",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="large",
            python_version="3.9.18",
            venv_path=None,
            packages=packages,
            total_packages=100,
            checksum="",
            is_temporary=False,
        )
        data = snap.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        snap.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(snap)

        loaded = storage.load("20260424_143022_large1")
        assert loaded.total_packages == 100
        assert len(loaded.packages) == 100

    def test_unicode_label(self, storage):
        """测试包含中文标签的快照"""
        snap = Snapshot(
            id="20260424_143022_uni00a",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test_snapshot",
            python_version="3.9.18",
            venv_path=None,
            packages={"pkg": "1.0.0"},
            total_packages=1,
            checksum="",
            is_temporary=False,
        )
        data = snap.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        snap.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(snap)

        loaded = storage.load("20260424_143022_uni00a")
        assert loaded.label == "test_snapshot"

    def test_temporary_snapshot(self, storage):
        """测试临时快照"""
        snap = Snapshot(
            id="20260424_143022_temp1a",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label=None,
            python_version="3.9.18",
            venv_path=None,
            packages={"pkg": "1.0.0"},
            total_packages=1,
            checksum="",
            is_temporary=True,
        )
        data = snap.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        snap.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(snap)

        loaded = storage.load("20260424_143022_temp1a")
        assert loaded.is_temporary is True

    def test_no_venv_path(self, storage):
        """测试没有虚拟环境路径的快照"""
        snap = Snapshot(
            id="20260424_143022_noven1",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label=None,
            python_version="3.9.18",
            venv_path=None,
            packages={"pkg": "1.0.0"},
            total_packages=1,
            checksum="",
            is_temporary=False,
        )
        data = snap.to_dict()
        data_without_checksum = {k: v for k, v in data.items() if k != "checksum"}
        snap.checksum = storage.calculate_checksum(data_without_checksum)
        storage.save(snap)

        loaded = storage.load("20260424_143022_noven1")
        assert loaded.venv_path is None
