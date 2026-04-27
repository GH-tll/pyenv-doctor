# -*- coding: utf-8 -*-
"""
测试回滚引擎

覆盖场景:
- 执行回滚
- 预览回滚
- 验证结果
- 获取最新快照
- 失败处理
"""

from unittest.mock import MagicMock, patch

import pytest

from pyenv_doctor.models.schemas import PackageChange, RollbackPreview, RollbackResult, Snapshot
from pyenv_doctor.repair.rollback import RollbackEngine
from datetime import datetime


class TestRollbackEngine:
    """测试 RollbackEngine 类"""

    @pytest.fixture
    def mock_snapshot_manager(self):
        """模拟快照管理器"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def sample_snapshot(self):
        """创建示例快照"""
        return Snapshot(
            id="20260424_143022_abc123",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test-snapshot",
            python_version="3.9.18",
            venv_path="D:\\test\\.venv",
            packages={
                "numpy": "1.23.5",
                "pandas": "1.5.3",
                "requests": "2.27.1",
            },
            total_packages=3,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

    def test_init_default(self):
        """测试默认初始化"""
        engine = RollbackEngine()
        assert engine.timeout == 60

    def test_init_custom_timeout(self):
        """测试自定义超时"""
        engine = RollbackEngine(timeout=30)
        assert engine.timeout == 30

    def test_rollback_success(self, mock_snapshot_manager, sample_snapshot):
        """测试回滚成功"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # Mock pip 安装成功
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            # Mock 获取已安装包
            with patch.object(engine, '_get_installed_packages', return_value=sample_snapshot.packages):
                result = engine.rollback(sample_snapshot.id, verify=True)

        assert isinstance(result, RollbackResult)
        assert result.success is True
        assert result.snapshot_id == sample_snapshot.id
        assert result.packages_restored == 3
        assert result.verified is True

    def test_rollback_no_verify(self, mock_snapshot_manager, sample_snapshot):
        """测试不回滚验证"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = engine.rollback(sample_snapshot.id, verify=False)

        assert result.success is True
        assert result.verified is False

    def test_rollback_snapshot_not_found(self, mock_snapshot_manager):
        """测试回滚不存在的快照"""
        mock_snapshot_manager.get.return_value = None

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        result = engine.rollback("non_existent_id")

        assert result.success is False
        assert result.packages_restored == 0

    def test_rollback_partial_failure(self, mock_snapshot_manager, sample_snapshot):
        """测试部分回滚失败"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # Mock pip 安装部分失败
        call_count = [0]

        def mock_install(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            # 第一个成功，后面失败
            mock_result.returncode = 0 if call_count[0] == 1 else 1
            return mock_result

        with patch('subprocess.run', side_effect=mock_install):
            result = engine.rollback(sample_snapshot.id, verify=False)

        assert result.success is False  # 有失败

    def test_rollback_user_cancel(self, mock_snapshot_manager, sample_snapshot):
        """测试用户取消回滚"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # Mock 用户取消
        with patch('subprocess.run', side_effect=KeyboardInterrupt()):
            result = engine.rollback(sample_snapshot.id, verify=False)

        # 用户取消，success 应为 False
        assert result.success is False

    def test_rollback_timeout(self, mock_snapshot_manager, sample_snapshot):
        """测试回滚超时"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine(timeout=1)
        engine.snapshot_manager = mock_snapshot_manager

        import subprocess

        # Mock 超时
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd="pip", timeout=1)):
            result = engine.rollback(sample_snapshot.id, verify=False)

        # 超时导致失败
        assert result.success is False

    def test_preview_success(self, mock_snapshot_manager, sample_snapshot):
        """测试预览成功"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # Mock 当前包版本（与快照不同）
        current_packages = {
            "numpy": "1.24.0",
            "pandas": "1.5.3",  # 相同
            "requests": "2.28.2",
        }

        with patch.object(engine, '_get_installed_packages', return_value=current_packages):
            preview = engine.preview(sample_snapshot.id)

        assert isinstance(preview, RollbackPreview)
        assert preview.snapshot_id == sample_snapshot.id
        # numpy 和 requests 需要变更
        assert preview.total_changes == 2

    def test_preview_no_changes(self, mock_snapshot_manager, sample_snapshot):
        """测试预览无变化"""
        mock_snapshot_manager.get.return_value = sample_snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # 当前版本与快照相同
        with patch.object(engine, '_get_installed_packages', return_value=sample_snapshot.packages):
            preview = engine.preview(sample_snapshot.id)

        assert preview.total_changes == 0

    def test_preview_snapshot_not_found(self, mock_snapshot_manager):
        """测试预览不存在的快照"""
        mock_snapshot_manager.get.return_value = None

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        preview = engine.preview("non_existent_id")

        assert preview is None

    def test_restore_package_success(self):
        """测试恢复单个包成功"""
        engine = RollbackEngine()

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result) as mock_run:
            success = engine._restore_package("numpy", "1.23.5")

        assert success is True
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "numpy==1.23.5" in call_args

    def test_restore_package_failure(self):
        """测试恢复单个包失败"""
        engine = RollbackEngine()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error"

        with patch('subprocess.run', return_value=mock_result):
            success = engine._restore_package("numpy", "1.23.5")

        assert success is False

    def test_restore_package_timeout(self):
        """测试恢复单个包超时"""
        engine = RollbackEngine(timeout=1)

        import subprocess

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(cmd="pip", timeout=1)):
            success = engine._restore_package("numpy", "1.23.5")

        assert success is False

    def test_get_installed_packages(self):
        """测试获取已安装包"""
        engine = RollbackEngine()

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "numpy==1.23.5\npandas==1.5.3\nrequests==2.27.1\n"

        with patch('subprocess.run', return_value=mock_result):
            packages = engine._get_installed_packages()

        assert len(packages) == 3
        assert packages["numpy"] == "1.23.5"
        assert packages["pandas"] == "1.5.3"
        assert packages["requests"] == "2.27.1"

    def test_get_installed_packages_failure(self):
        """测试获取已安装包失败"""
        engine = RollbackEngine()

        with patch('subprocess.run', side_effect=Exception("pip error")):
            packages = engine._get_installed_packages()

        assert packages == {}

    def test_verify_snapshot_pass(self, sample_snapshot):
        """测试验证快照通过"""
        engine = RollbackEngine()

        # Mock 当前包版本与快照一致
        with patch.object(engine, '_get_installed_packages', return_value=sample_snapshot.packages):
            result = engine._verify_snapshot(sample_snapshot)

        assert result.passed is True
        assert result.verified_packages == 3
        assert len(result.failed_packages) == 0

    def test_verify_snapshot_fail(self, sample_snapshot):
        """测试验证快照失败"""
        engine = RollbackEngine()

        # Mock 当前包版本不一致
        current_packages = {
            "numpy": "1.24.0",  # 不同
            "pandas": "1.5.3",
            "requests": "2.27.1",
        }

        with patch.object(engine, '_get_installed_packages', return_value=current_packages):
            result = engine._verify_snapshot(sample_snapshot)

        assert result.passed is False
        assert "numpy" in result.failed_packages

    def test_get_latest_snapshot_id(self, mock_snapshot_manager):
        """测试获取最新快照 ID"""
        snapshots = [
            Snapshot(
                id="20260424_143022_abc123",
                timestamp=datetime(2026, 4, 24, 14, 30, 22),
                label="latest",
                python_version="3.9.18",
                venv_path=None,
                packages={},
                total_packages=0,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            ),
            Snapshot(
                id="20260424_120000_xyz789",
                timestamp=datetime(2026, 4, 24, 12, 0, 0),
                label="older",
                python_version="3.9.18",
                venv_path=None,
                packages={},
                total_packages=0,
                checksum="sha256:" + "a" * 64,
                is_temporary=False,
            ),
        ]

        mock_snapshot_manager.list_snapshots.return_value = snapshots

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        latest_id = engine.get_latest_snapshot_id()

        assert latest_id == "20260424_143022_abc123"

    def test_get_latest_snapshot_id_no_snapshots(self, mock_snapshot_manager):
        """测试没有快照时获取最新"""
        mock_snapshot_manager.list_snapshots.return_value = []

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        latest_id = engine.get_latest_snapshot_id()

        assert latest_id is None

    def test_get_latest_snapshot_id_error(self, mock_snapshot_manager):
        """测试获取最新快照错误"""
        mock_snapshot_manager.list_snapshots.side_effect = Exception("Error")

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        latest_id = engine.get_latest_snapshot_id()

        assert latest_id is None


class TestRollbackEngineEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def mock_snapshot_manager(self):
        """模拟快照管理器"""
        mock = MagicMock()
        return mock

    def test_rollback_empty_snapshot(self, mock_snapshot_manager):
        """测试回滚空快照"""
        snapshot = Snapshot(
            id="20260424_143022_emptya",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="empty",
            python_version="3.9.18",
            venv_path=None,
            packages={},
            total_packages=0,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

        mock_snapshot_manager.get.return_value = snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        result = engine.rollback(snapshot.id, verify=False)

        assert result.success is True
        assert result.packages_restored == 0

    def test_preview_snapshot_load_error(self, mock_snapshot_manager):
        """测试预览快照加载错误"""
        mock_snapshot_manager.get.side_effect = Exception("Load error")

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        preview = engine.preview("some_id")

        assert preview is None

    def test_rollback_large_snapshot(self, mock_snapshot_manager):
        """测试回滚大量包"""
        # 创建 100 个包的快照
        packages = {f"package{i}": f"1.0.{i}" for i in range(100)}

        snapshot = Snapshot(
            id="20260424_143022_largea",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="large",
            python_version="3.9.18",
            venv_path=None,
            packages=packages,
            total_packages=100,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

        mock_snapshot_manager.get.return_value = snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # Mock 全部成功
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            with patch.object(engine, '_get_installed_packages', return_value=packages):
                result = engine.rollback(snapshot.id, verify=False)

        assert result.success is True
        assert result.packages_restored == 100

    def test_preview_package_not_installed(self, mock_snapshot_manager):
        """测试预览时包未安装"""
        snapshot = Snapshot(
            id="20260424_143022_test1a",
            timestamp=datetime(2026, 4, 24, 14, 30, 22),
            label="test",
            python_version="3.9.18",
            venv_path=None,
            packages={"new-pkg": "1.0.0"},
            total_packages=1,
            checksum="sha256:" + "a" * 64,
            is_temporary=False,
        )

        mock_snapshot_manager.get.return_value = snapshot

        engine = RollbackEngine()
        engine.snapshot_manager = mock_snapshot_manager

        # Mock 当前未安装该包
        with patch.object(engine, '_get_installed_packages', return_value={}):
            preview = engine.preview(snapshot.id)

        assert preview.total_changes == 1
        assert preview.changes[0].current_version == "未安装"
        assert preview.changes[0].target_version == "1.0.0"
