# -*- coding: utf-8 -*-
"""
EnvScanner 单元测试

测试用例覆盖:
- 功能测试: ES-001 至 ES-005
- 边界测试: ES-B01 至 ES-B03
- 异常测试: ES-E01 至 ES-E02
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyenv_doctor.agents.env_scanner import EnvScanner
from pyenv_doctor.models.schemas import PackageInfo


class TestEnvScanner:
    """EnvScanner 测试类"""

    def test_scan_empty_environment(self):
        """
        ES-001: 空环境扫描

        前置条件: 新建空 venv
        预期结果: 返回空列表 []
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_distributions.return_value = []

            scanner = EnvScanner()
            result = scanner.scan()
            assert result == []

    def test_scan_single_package(self):
        """
        ES-002: 单包环境扫描

        前置条件: 安装 numpy==1.24.0
        预期结果: 返回包含 1 个元素的列表，name="numpy", version="1.24.0"
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            # 模拟单个包
            mock_dist = MagicMock()
            mock_dist.metadata = {"Name": "numpy"}
            mock_dist.version = "1.24.0"
            mock_dist.requires = []
            mock_distributions.return_value = [mock_dist]

            scanner = EnvScanner()
            result = scanner.scan()
            assert len(result) == 1
            assert result[0].name == "numpy"
            assert result[0].version == "1.24.0"

    def test_scan_multiple_packages(self):
        """
        ES-003: 多包环境扫描

        前置条件: 安装 numpy==1.24.0, pandas==1.5.3
        预期结果: 返回包含 2 个元素的列表
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            # 模拟多个包
            mock_dist1 = MagicMock()
            mock_dist1.metadata = {"Name": "numpy"}
            mock_dist1.version = "1.24.0"
            mock_dist1.requires = []

            mock_dist2 = MagicMock()
            mock_dist2.metadata = {"Name": "pandas"}
            mock_dist2.version = "1.5.3"
            mock_dist2.requires = []

            mock_distributions.return_value = [mock_dist1, mock_dist2]

            scanner = EnvScanner()
            result = scanner.scan()
            assert len(result) == 2

    def test_scan_package_with_dependencies(self):
        """
        ES-004: 包含依赖的包扫描

        前置条件: 安装 pandas==1.5.3
        预期结果: pandas 的 requires 包含依赖声明
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            # 模拟带依赖的包
            mock_dist = MagicMock()
            mock_dist.metadata = {"Name": "pandas"}
            mock_dist.version = "1.5.3"
            mock_dist.requires = [MagicMock(__str__=lambda self: "numpy<1.24")]

            mock_distributions.return_value = [mock_dist]

            scanner = EnvScanner()
            result = scanner.scan()
            assert len(result) == 1
            assert result[0].name == "pandas"
            assert len(result[0].requires) > 0

    def test_scan_large_environment(self):
        """
        ES-005: 大量包扫描

        前置条件: 安装 100+ 个包
        预期结果: 耗时 < 3 秒，返回完整列表
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            # 模拟 100 个包
            mock_dists = []
            for i in range(100):
                mock_dist = MagicMock()
                mock_dist.metadata = {"Name": f"package_{i}"}
                mock_dist.version = "1.0.0"
                mock_dist.requires = []
                mock_dists.append(mock_dist)

            mock_distributions.return_value = mock_dists

            scanner = EnvScanner()
            start_time = time.time()
            result = scanner.scan()
            end_time = time.time()
            assert len(result) == 100
            assert (end_time - start_time) < 3.0

    def test_scan_package_with_special_characters(self):
        """
        ES-B01: 包名含特殊字符

        前置条件: 安装包名含连字符的包
        测试数据: python-dateutil
        预期结果: 正确返回包名
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_dist = MagicMock()
            mock_dist.metadata = {"Name": "python-dateutil"}
            mock_dist.version = "2.8.2"
            mock_dist.requires = []
            mock_distributions.return_value = [mock_dist]

            scanner = EnvScanner()
            result = scanner.scan()
            assert len(result) == 1
            assert result[0].name == "python-dateutil"

    def test_scan_prerelease_version(self):
        """
        ES-B02: 版本号含预发布标识

        前置条件: 安装预发布版本
        测试数据: numpy==1.24.0rc1
        预期结果: 正确返回版本号
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_dist = MagicMock()
            mock_dist.metadata = {"Name": "numpy"}
            mock_dist.version = "1.24.0rc1"
            mock_dist.requires = []
            mock_distributions.return_value = [mock_dist]

            scanner = EnvScanner()
            result = scanner.scan()
            assert len(result) == 1
            assert result[0].version == "1.24.0rc1"

    def test_scan_local_package(self):
        """
        ES-B03: 本地包扫描

        前置条件: 通过 pip install -e . 安装本地包
        预期结果: 正确返回本地包信息
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_dist = MagicMock()
            mock_dist.metadata = {"Name": "pyenv-doctor"}
            mock_dist.version = "0.1.0"
            mock_dist.requires = []
            mock_distributions.return_value = [mock_dist]

            scanner = EnvScanner()
            result = scanner.scan()
            assert len(result) == 1
            assert result[0].name == "pyenv-doctor"

    def test_scan_corrupted_metadata(self):
        """
        ES-E01: 元数据损坏

        前置条件：包元数据损坏
        预期结果：跳过损坏包，返回其他包列表
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            # 模拟损坏的包
            mock_dist1 = MagicMock()
            mock_dist1.metadata = {"Name": "corrupted_package"}
            mock_dist1.version = MagicMock(side_effect=Exception("Metadata corrupted"))

            # 模拟正常的包
            mock_dist2 = MagicMock()
            mock_dist2.metadata = {"Name": "normal_package"}
            mock_dist2.version = "1.0.0"
            mock_dist2.requires = []

            mock_distributions.return_value = [mock_dist1, mock_dist2]

            scanner = EnvScanner()
            result = scanner.scan()
            # 应该跳过损坏的包，只返回正常的包
            # 注意：mock_dist1 会因为 version 抛出异常而被跳过
            assert len(result) == 1
            assert result[0].name == "normal_package"

    def test_scan_permission_denied(self):
        """
        ES-E02: 权限不足

        前置条件: 无读取权限
        预期结果: 抛出 PermissionError
        """
        with patch("pyenv_doctor.agents.env_scanner.distributions") as mock_distributions:
            mock_distributions.side_effect = PermissionError("Permission denied")

            scanner = EnvScanner()
            with pytest.raises(PermissionError):
                scanner.scan()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
