# -*- coding: utf-8 -*-
"""
测试 Snapshot CLI 命令

覆盖场景:
- snapshot create
- snapshot list
- snapshot rollback
- snapshot delete
- snapshot export
- snapshot cleanup
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from pyenv_doctor.cli.snapshot import snapshot
from pyenv_doctor.models.schemas import Snapshot
from datetime import datetime


class TestSnapshotCli:
    """测试 Snapshot CLI 命令"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_snapshot_manager(self, temp_storage_dir):
        """模拟快照管理器"""
        from pyenv_doctor.snapshot.storage import SnapshotStorage
        from pyenv_doctor.snapshot.manager import SnapshotManager
        
        storage = SnapshotStorage(storage_dir=temp_storage_dir)
        manager = SnapshotManager(storage=storage)
        
        # Mock pip_tool
        mock_pip = MagicMock()
        mock_pip.get_installed_packages.return_value = {
            "numpy": "1.24.0",
            "pandas": "1.5.3",
        }
        mock_pip.install_package.return_value = True
        
        with patch.object(manager, '_get_pip_tool', return_value=mock_pip):
            yield manager

    def test_snapshot_list_empty(self, runner, mock_snapshot_manager):
        """测试列出空快照列表"""
        with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
            result = runner.invoke(snapshot, ['list'])

        assert result.exit_code == 0
        assert "暂无快照" in result.output

    def test_snapshot_create(self, runner, mock_snapshot_manager):
        """测试创建快照"""
        with patch.object(mock_snapshot_manager, 'create') as mock_create:
            mock_create.return_value = Snapshot(
                id="20260424_143022_abc123",
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label="test",
                python_version="3.9.18",
                venv_path=None,
                packages={"numpy": "1.24.0"},
                total_packages=1,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            )
            
            with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                result = runner.invoke(snapshot, ['create', '-l', 'test'])

        assert result.exit_code == 0
        assert "快照创建成功" in result.output
        assert "20260424_143022_abc123" in result.output

    def test_snapshot_create_temporary(self, runner, mock_snapshot_manager):
        """测试创建临时快照"""
        with patch.object(mock_snapshot_manager, 'create') as mock_create:
            mock_create.return_value = Snapshot(
                id="20260424_143022_tmp0001",
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label=None,
                python_version="3.9.18",
                venv_path=None,
                packages={},
                total_packages=0,
                checksum="sha256:" + "a" * 64,
                is_temporary=True,
            )
            
            with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                result = runner.invoke(snapshot, ['create', '--temporary'])

        assert result.exit_code == 0
        assert "临时快照" in result.output

    def test_snapshot_list_with_snapshots(self, runner, mock_snapshot_manager):
        """测试列出有快照"""
        snapshots = [
            Snapshot(
                id="20260424_143022_abc123",
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label="test-1",
                python_version="3.9.18",
                venv_path=None,
                packages={"numpy": "1.24.0"},
                total_packages=1,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            ),
            Snapshot(
                id="20260424_120000_xyz789",
                timestamp=datetime(2026, 4, 24, 12, 0, 0),
                label="test-2",
                python_version="3.9.18",
                venv_path=None,
                packages={"pandas": "1.5.3"},
                total_packages=1,
                checksum="sha256:" + "b" * 64,
                is_temporary=True,
            ),
        ]
        
        with patch.object(mock_snapshot_manager, 'list_snapshots', return_value=snapshots):
            with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                result = runner.invoke(snapshot, ['list'])

        assert result.exit_code == 0
        assert "test-1" in result.output
        assert "test-2" in result.output
        assert "共 2 个快照" in result.output

    def test_snapshot_list_json(self, runner, mock_snapshot_manager):
        """测试 JSON 格式列出快照"""
        snapshots = [
            Snapshot(
                id="20260424_143022_abc123",
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label="test",
                python_version="3.9.18",
                venv_path=None,
                packages={"numpy": "1.24.0"},
                total_packages=1,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            )
        ]
        
        with patch.object(mock_snapshot_manager, 'list_snapshots', return_value=snapshots):
            with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                result = runner.invoke(snapshot, ['list', '--json'])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "20260424_143022_abc123"

    def test_snapshot_rollback_missing_id(self, runner):
        """测试回滚缺少快照 ID"""
        result = runner.invoke(snapshot, ['rollback'])

        assert result.exit_code == 1
        assert "请指定快照 ID" in result.output

    def test_snapshot_rollback_dry_run(self, runner, mock_snapshot_manager):
        """测试回滚预演"""
        snapshot_obj = Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={"numpy": "1.23.5"},
            total_packages=1,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )
        
        with patch.object(mock_snapshot_manager, 'get', return_value=snapshot_obj):
            with patch.object(mock_snapshot_manager, 'preview_rollback') as mock_preview:
                from pyenv_doctor.models.schemas import RollbackPreview
                mock_preview.return_value = RollbackPreview(
                    snapshot_id="20260424_143022_abc123",
                    changes=[],
                    total_changes=0,
                )
                
                with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                    with patch('pyenv_doctor.cli.snapshot.RollbackEngine'):
                        result = runner.invoke(snapshot, ['rollback', '20260424_143022_abc123', '--dry-run'])

        assert result.exit_code == 0
        assert "回滚预览" in result.output
        assert "DRY-RUN" in result.output

    def test_snapshot_delete(self, runner, mock_snapshot_manager):
        """测试删除快照"""
        snapshot_obj = Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={},
            total_packages=0,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )
        
        with patch.object(mock_snapshot_manager, 'get', return_value=snapshot_obj):
            with patch.object(mock_snapshot_manager, 'delete') as mock_delete:
                with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                    # 使用 --yes 跳过确认
                    result = runner.invoke(snapshot, ['delete', '20260424_143022_abc123', '--yes'])

        assert result.exit_code == 0
        assert "成功删除" in result.output

    def test_snapshot_export(self, runner, mock_snapshot_manager, temp_storage_dir):
        """测试导出快照"""
        snapshot_obj = Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={"numpy": "1.24.0", "pandas": "1.5.3"},
            total_packages=2,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )
        
        output_path = Path(temp_storage_dir) / "requirements.txt"
        
        with patch.object(mock_snapshot_manager, 'get', return_value=snapshot_obj):
            with patch.object(mock_snapshot_manager, 'export', return_value=str(output_path)) as mock_export:
                with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                    result = runner.invoke(snapshot, ['export', '20260424_143022_abc123', '-o', str(output_path)])

        assert result.exit_code == 0
        assert "导出成功" in result.output

    def test_snapshot_export_not_found(self, runner, mock_snapshot_manager):
        """测试导出不存在的快照"""
        with patch.object(mock_snapshot_manager, 'get', return_value=None):
            with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                result = runner.invoke(snapshot, ['export', 'non_existent_id'])

        assert result.exit_code == 1
        assert "快照不存在" in result.output

    def test_snapshot_cleanup(self, runner, mock_snapshot_manager):
        """测试清理快照"""
        snapshots = [
            Snapshot(
                id="20260424_143022_tmp0001",
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label=None,
                python_version="3.9.18",
                venv_path=None,
                packages={},
                total_packages=0,
                checksum="sha256:" + "a" * 64,
                is_temporary=True,
            )
        ]
        
        with patch.object(mock_snapshot_manager, 'list_snapshots', return_value=snapshots):
            with patch.object(mock_snapshot_manager, 'delete') as mock_delete:
                with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                    result = runner.invoke(snapshot, ['cleanup', '--temporary', '--yes'])

        assert result.exit_code == 0
        assert "成功删除" in result.output

    def test_snapshot_rollback_latest(self, runner, mock_snapshot_manager):
        """测试回滚到最新快照"""
        snapshot_obj = Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="latest",
            python_version="3.9.18",
            venv_path=None,
            packages={},
            total_packages=0,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )
        
        with patch.object(mock_snapshot_manager, 'get', return_value=snapshot_obj):
            with patch.object(mock_snapshot_manager, 'preview_rollback') as mock_preview:
                from pyenv_doctor.models.schemas import RollbackPreview
                mock_preview.return_value = RollbackPreview(
                    snapshot_id="20260424_143022_abc123",
                    changes=[],
                    total_changes=0,
                )
                
                with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                    with patch('pyenv_doctor.cli.snapshot.RollbackEngine') as MockEngine:
                        mock_engine = MagicMock()
                        mock_engine.get_latest_snapshot_id.return_value = "20260424_143022_abc123"
                        mock_engine.rollback.return_value = MagicMock(
                            success=True,
                            packages_restored=0,
                            duration=0.1,
                            verified=True,
                        )
                        MockEngine.return_value = mock_engine
                        
                        result = runner.invoke(snapshot, ['rollback', '--latest', '--yes'])

        assert result.exit_code == 0
        assert "回滚成功" in result.output

    def test_snapshot_create_error(self, runner, mock_snapshot_manager):
        """测试创建快照错误"""
        with patch.object(mock_snapshot_manager, 'create', side_effect=Exception("Create error")):
            with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                result = runner.invoke(snapshot, ['create'])

        assert result.exit_code == 1
        assert "创建快照失败" in result.output

    def test_snapshot_rollback_error(self, runner, mock_snapshot_manager):
        """测试回滚错误"""
        snapshot_obj = Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={},
            total_packages=0,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )
        
        with patch.object(mock_snapshot_manager, 'get', return_value=snapshot_obj):
            with patch.object(mock_snapshot_manager, 'preview_rollback') as mock_preview:
                from pyenv_doctor.models.schemas import RollbackPreview
                mock_preview.return_value = RollbackPreview(
                    snapshot_id="20260424_143022_abc123",
                    changes=[],
                    total_changes=0,
                )
                
                with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_snapshot_manager):
                    with patch('pyenv_doctor.cli.snapshot.RollbackEngine') as MockEngine:
                        mock_engine = MagicMock()
                        mock_engine.rollback.side_effect = Exception("Rollback error")
                        MockEngine.return_value = mock_engine
                        
                        result = runner.invoke(snapshot, ['rollback', '20260424_143022_abc123', '--yes'])

        assert result.exit_code == 1
        assert "回滚失败" in result.output


class TestSnapshotCliEdgeCases:
    """测试 CLI 边界情况"""

    @pytest.fixture
    def runner(self):
        """创建 CLI 测试运行器"""
        return CliRunner()

    def test_snapshot_list_limit(self, runner):
        """测试限制显示数量"""
        from pyenv_doctor.snapshot.manager import SnapshotManager
        from pyenv_doctor.models.schemas import Snapshot
        
        snapshots = [
            Snapshot(
                id=f"20260424_14302{i}_abc12{i}",
                timestamp=datetime(2026, 4, 24, 14, 30, 20 + i),
                label=f"test-{i}",
                python_version="3.9.18",
                venv_path=None,
                packages={},
                total_packages=0,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            )
            for i in range(5)
        ]
        
        mock_manager = MagicMock()
        mock_manager.list_snapshots.return_value = snapshots
        
        with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_manager):
            result = runner.invoke(snapshot, ['list', '-n', '2'])

        # 验证调用了 list_snapshots 并传入 limit=2
        mock_manager.list_snapshots.assert_called_with(limit=2)

    def test_snapshot_delete_multiple(self, runner):
        """测试批量删除"""
        from pyenv_doctor.models.schemas import Snapshot
        
        def get_snapshot(sid):
            return Snapshot(
                id=sid,
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label="test",
                python_version="3.9.18",
                venv_path=None,
                packages={},
                total_packages=0,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            )
        
        mock_manager = MagicMock()
        mock_manager.get.side_effect = get_snapshot
        mock_manager.delete.return_value = None
        
        with patch('pyenv_doctor.cli.snapshot.SnapshotManager', return_value=mock_manager):
            result = runner.invoke(snapshot, ['delete', 'id1', 'id2', 'id3', '--yes'])

        assert result.exit_code == 0
        assert mock_manager.delete.call_count == 3
