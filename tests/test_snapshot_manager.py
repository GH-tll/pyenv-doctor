# -*- coding: utf-8 -*-
"""
测试快照管理器

覆盖场景:
- 创建快照
- 获取快照
- 列出快照
- 回滚
- 删除
- 导出
- 清理临时快照
- 预览回滚
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pyenv_doctor.models.schemas import (
    PackageChange,
    RollbackPreview,
    RollbackResult,
    Snapshot,
)
from pyenv_doctor.snapshot.manager import (
    ExportError,
    RollbackError,
    SnapshotCreateError,
    SnapshotManager,
)
from pyenv_doctor.snapshot.storage import SnapshotStorage, SnapshotNotFoundError


class TestSnapshotManager:
    """测试 SnapshotManager 类"""

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_pip_tool(self):
        """模拟 pip_tool"""
        mock = MagicMock()
        mock.get_installed_packages.return_value = {
            "numpy": "1.24.0",
            "pandas": "1.5.3",
            "requests": "2.28.2",
        }
        mock.install_package.return_value = True
        return mock

    @pytest.fixture
    def manager(self, temp_storage_dir, mock_pip_tool):
        """创建管理器实例"""
        storage = SnapshotStorage(storage_dir=temp_storage_dir)
        manager = SnapshotManager(storage=storage)
        
        # Mock pip_tool
        with patch.object(manager, '_get_pip_tool', return_value=mock_pip_tool):
            yield manager

    def test_create_snapshot(self, manager, mock_pip_tool):
        """测试创建快照"""
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="test")

        assert snapshot.id is not None
        assert snapshot.label == "test"
        assert snapshot.python_version == sys.version.split()[0]
        assert snapshot.total_packages == 3
        assert snapshot.packages == {
            "numpy": "1.24.0",
            "pandas": "1.5.3",
            "requests": "2.28.2",
        }
        assert snapshot.checksum.startswith("sha256:")
        assert snapshot.is_temporary is False

    def test_create_temporary_snapshot(self, manager, mock_pip_tool):
        """测试创建临时快照"""
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="temp", temporary=True)

        assert snapshot.is_temporary is True
        assert snapshot.label == "temp"

    def test_create_snapshot_no_label(self, manager, mock_pip_tool):
        """测试创建无标签快照"""
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create()

        assert snapshot.label is None

    def test_create_snapshot_with_venv(self, manager, mock_pip_tool):
        """测试创建带虚拟环境路径的快照"""
        venv_path = "D:\\test\\.venv"
        with patch.object(manager, '_get_venv_path', return_value=venv_path):
            snapshot = manager.create()

        assert snapshot.venv_path == venv_path

    def test_create_snapshot_error(self, manager):
        """测试创建快照错误"""
        # 模拟 pip_tool 抛出异常
        with patch.object(manager, '_get_pip_tool') as mock_get_pip:
            mock_get_pip.side_effect = Exception("pip error")
            
            with pytest.raises(SnapshotCreateError):
                manager.create()

    def test_get_snapshot(self, manager, mock_pip_tool):
        """测试获取快照"""
        # 先创建
        with patch.object(manager, '_get_venv_path', return_value=None):
            created = manager.create(label="get-test")

        # 再获取
        retrieved = manager.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.label == "get-test"

    def test_get_not_found(self, manager):
        """测试获取不存在的快照"""
        result = manager.get("non_existent_id")
        assert result is None

    def test_list_snapshots(self, manager, mock_pip_tool):
        """测试列出快照"""
        # 创建多个快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            for i in range(3):
                manager.create(label=f"test-{i}")

        # 列出所有
        snapshots = manager.list_snapshots()

        assert len(snapshots) == 3
        # 验证按时间倒序
        assert snapshots[0].timestamp >= snapshots[1].timestamp
        assert snapshots[1].timestamp >= snapshots[2].timestamp

    def test_list_snapshots_with_limit(self, manager, mock_pip_tool):
        """测试限制数量列出快照"""
        # 创建多个快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            for i in range(5):
                manager.create(label=f"test-{i}")

        # 限制数量
        snapshots = manager.list_snapshots(limit=2)

        assert len(snapshots) == 2

    def test_rollback(self, manager, mock_pip_tool):
        """测试回滚"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="rollback-test")

        # 修改 mock 返回不同的包版本
        mock_pip_tool.get_installed_packages.return_value = {
            "numpy": "1.25.0",
            "pandas": "2.0.0",
            "requests": "2.29.0",
        }

        # 回滚
        def progress_callback(current, total, pkg_name):
            pass

        result = manager.rollback(
            snapshot.id,
            verify=False,
            progress_callback=progress_callback
        )

        assert isinstance(result, RollbackResult)
        assert result.success is True
        assert result.snapshot_id == snapshot.id
        assert result.packages_restored == 3

    def test_rollback_not_found(self, manager):
        """测试回滚不存在的快照"""
        with pytest.raises(SnapshotNotFoundError):
            manager.rollback("non_existent_id")

    def test_rollback_verification_failed(self, manager, mock_pip_tool):
        """测试回滚验证失败"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="verify-fail-test")

        # 模拟 pip_tool 安装失败
        mock_pip_tool.install_package.side_effect = lambda name, version: False

        with pytest.raises(RollbackError):
            manager.rollback(snapshot.id, verify=True)

    def test_delete_snapshot(self, manager, mock_pip_tool):
        """测试删除快照"""
        # 先创建
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="delete-test")

        # 删除
        manager.delete(snapshot.id)

        # 验证已删除
        assert manager.get(snapshot.id) is None

    def test_delete_not_found(self, manager):
        """测试删除不存在的快照"""
        with pytest.raises(SnapshotNotFoundError):
            manager.delete("non_existent_id")

    def test_export_requirements(self, manager, mock_pip_tool, temp_storage_dir):
        """测试导出为 requirements.txt"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="export-test")

        # 导出
        output_path = Path(temp_storage_dir) / "requirements.txt"
        result_path = manager.export(snapshot.id, str(output_path), format="requirements")

        # 验证
        assert Path(result_path).exists()
        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# PyEnv Doctor Snapshot Export" in content
        assert "numpy==1.24.0" in content
        assert "pandas==1.5.3" in content
        assert "requests==2.28.2" in content
        # 验证排序
        lines = [l for l in content.split("\n") if "==" in l]
        assert lines == sorted(lines)

    def test_export_json(self, manager, mock_pip_tool, temp_storage_dir):
        """测试导出为 JSON"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="export-json-test")

        # 导出
        output_path = Path(temp_storage_dir) / "snapshot.json"
        result_path = manager.export(snapshot.id, str(output_path), format="json")

        # 验证
        assert Path(result_path).exists()
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["id"] == snapshot.id
        assert data["label"] == "export-json-test"
        assert data["packages"] == snapshot.packages

    def test_export_invalid_format(self, manager, mock_pip_tool, temp_storage_dir):
        """测试导出无效格式"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create()

        # 导出无效格式
        output_path = Path(temp_storage_dir) / "invalid.txt"
        with pytest.raises(ExportError):
            manager.export(snapshot.id, str(output_path), format="invalid")

    def test_export_not_found(self, manager):
        """测试导出不存在的快照"""
        with pytest.raises(SnapshotNotFoundError):
            manager.export("non_existent_id", "output.txt")

    def test_cleanup_temporary(self, manager, mock_pip_tool):
        """测试清理临时快照"""
        # 创建混合快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            # 创建 2 个临时快照
            manager.create(label="temp-1", temporary=True)
            manager.create(label="temp-2", temporary=True)
            # 创建 1 个永久快照
            manager.create(label="permanent", temporary=False)

        # 清理临时快照
        count = manager.cleanup_temporary()

        assert count == 2

        # 验证只剩永久快照
        snapshots = manager.list_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0].is_temporary is False

    def test_get_latest(self, manager, mock_pip_tool):
        """测试获取最新快照"""
        # 创建多个快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            for i in range(3):
                manager.create(label=f"test-{i}")

        # 获取最新
        latest = manager.get_latest()

        assert latest is not None
        snapshots = manager.list_snapshots()
        assert latest.timestamp == max(s.timestamp for s in snapshots)

    def test_get_latest_no_snapshots(self, manager):
        """测试没有快照时获取最新"""
        latest = manager.get_latest()
        assert latest is None

    def test_preview_rollback(self, manager, mock_pip_tool):
        """测试预览回滚"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="preview-test")

        # 修改当前包版本
        mock_pip_tool.get_installed_packages.return_value = {
            "numpy": "1.25.0",  # 不同版本
            "pandas": "1.5.3",  # 相同版本
            "requests": "2.29.0",  # 不同版本
        }

        # 预览
        preview = manager.preview_rollback(snapshot.id)

        assert isinstance(preview, RollbackPreview)
        assert preview.snapshot_id == snapshot.id
        # 只有 2 个包发生变化（numpy 和 requests）
        assert preview.total_changes == 2

    def test_preview_rollback_no_changes(self, manager, mock_pip_tool):
        """测试预览回滚无变化"""
        # 先创建快照
        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create(label="no-change-test")

        # 当前版本与快照相同
        mock_pip_tool.get_installed_packages.return_value = snapshot.packages

        # 预览
        preview = manager.preview_rollback(snapshot.id)

        assert preview.total_changes == 0

    def test_preview_rollback_not_found(self, manager):
        """测试预览不存在的快照"""
        with pytest.raises(SnapshotNotFoundError):
            manager.preview_rollback("non_existent_id")

    def test_generate_snapshot_id(self, manager):
        """测试生成快照 ID"""
        snapshot_id = manager._generate_snapshot_id()

        # 验证格式：YYYYMMDD_HHMMSS_random(6)
        assert len(snapshot_id) == 22  # 8 + 1 + 6 + 1 + 6
        assert snapshot_id[8] == "_"
        assert snapshot_id[15] == "_"
        # 验证前 15 个字符是数字和下划线
        assert snapshot_id[:8].isdigit()
        assert snapshot_id[9:15].isdigit()
        # 验证随机部分是 6 位小写字母或数字
        import re
        assert re.match(r"^[a-z0-9]{6}$", snapshot_id[16:])

    def test_get_venv_path_in_venv(self, manager):
        """测试获取虚拟环境路径（在 venv 中）"""
        with patch.object(sys, 'prefix', 'D:\\test\\.venv'):
            with patch.object(sys, 'base_prefix', 'C:\\Python39'):
                venv_path = manager._get_venv_path()
                assert venv_path == 'D:\\test\\.venv'

    def test_get_venv_path_not_in_venv(self, manager):
        """测试获取虚拟环境路径（不在 venv 中）"""
        with patch.object(sys, 'prefix', 'C:\\Python39'):
            with patch.object(sys, 'base_prefix', 'C:\\Python39'):
                venv_path = manager._get_venv_path()
                assert venv_path is None

    def test_export_to_requirements(self, manager, mock_pip_tool):
        """测试导出为 requirements 格式"""
        snapshot = Snapshot(
            id="20260424_143022_test1a",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={
                "zebra": "3.0.0",
                "alpha": "1.0.0",
                "beta": "2.0.0",
            },
            total_packages=3,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

        content = manager._export_to_requirements(snapshot)

        lines = content.split("\n")
        # 验证注释头
        assert "# PyEnv Doctor Snapshot Export" in lines[0]
        assert "# Python: 3.9.18" in lines[2]
        assert "# Packages: 3" in lines[3]
        # 验证排序
        pkg_lines = [l for l in lines if "==" in l]
        assert pkg_lines[0] == "alpha==1.0.0"
        assert pkg_lines[1] == "beta==2.0.0"
        assert pkg_lines[2] == "zebra==3.0.0"

    def test_verify_rollback_pass(self, manager, mock_pip_tool):
        """测试验证回滚通过"""
        snapshot = Snapshot(
            id="20260424_143022_test1b",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={"pkg1": "1.0.0", "pkg2": "2.0.0"},
            total_packages=2,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

        mock_pip_tool.get_installed_packages.return_value = {
            "pkg1": "1.0.0",
            "pkg2": "2.0.0",
        }

        result = manager._verify_rollback(snapshot)

        assert result.passed is True
        assert result.verified_packages == 2
        assert len(result.failed_packages) == 0

    def test_verify_rollback_fail(self, manager, mock_pip_tool):
        """测试验证回滚失败"""
        snapshot = Snapshot(
            id="20260424_143022_test1c",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={"pkg1": "1.0.0", "pkg2": "2.0.0"},
            total_packages=2,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

        mock_pip_tool.get_installed_packages.return_value = {
            "pkg1": "1.0.0",
            "pkg2": "3.0.0",  # 版本不匹配
        }

        result = manager._verify_rollback(snapshot)

        assert result.passed is False
        assert "pkg2" in result.failed_packages


class TestSnapshotManagerEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_pip_tool(self):
        """模拟 pip_tool"""
        mock = MagicMock()
        mock.get_installed_packages.return_value = {}
        mock.install_package.return_value = True
        return mock

    @pytest.fixture
    def manager(self, temp_storage_dir, mock_pip_tool):
        """创建管理器实例"""
        storage = SnapshotStorage(storage_dir=temp_storage_dir)
        manager = SnapshotManager(storage=storage)
        
        with patch.object(manager, '_get_pip_tool', return_value=mock_pip_tool):
            yield manager

    def test_create_empty_environment(self, manager, mock_pip_tool):
        """测试空环境创建快照"""
        mock_pip_tool.get_installed_packages.return_value = {}

        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create()

        assert snapshot.total_packages == 0
        assert snapshot.packages == {}

    def test_rollback_empty_snapshot(self, manager, mock_pip_tool):
        """测试回滚空快照"""
        mock_pip_tool.get_installed_packages.return_value = {}

        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create()

        result = manager.rollback(snapshot.id, verify=False)

        assert result.success is True
        assert result.packages_restored == 0

    def test_export_empty_snapshot(self, manager, mock_pip_tool, temp_storage_dir):
        """测试导出空快照"""
        mock_pip_tool.get_installed_packages.return_value = {}

        with patch.object(manager, '_get_venv_path', return_value=None):
            snapshot = manager.create()

        output_path = Path(temp_storage_dir) / "empty.txt"
        result_path = manager.export(snapshot.id, str(output_path))

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 应该只有注释，没有包
        assert "# PyEnv Doctor Snapshot Export" in content
        assert "==" not in content
