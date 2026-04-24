# -*- coding: utf-8 -*-
"""
Schemas 模块单元测试

测试用例覆盖:
- PackageInfo 测试: PI-001 至 PI-006
- Conflict 测试: CF-001 至 CF-003
- SandboxResult 测试: SR-001 至 SR-003
"""

import sys
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyenv_doctor.models.schemas import PackageInfo, Conflict, SandboxResult


class TestPackageInfo:
    """PackageInfo 测试类"""

    def test_valid_package_info(self):
        """
        PI-001: 有效包信息

        前置条件: 无
        预期结果: 成功创建 PackageInfo
        """
        pkg = PackageInfo(
            name="numpy",
            version="1.24.0",
            requires=["pytest>=7.0"]
        )
        assert pkg.name == "numpy"
        assert pkg.version == "1.24.0"
        assert len(pkg.requires) == 1

    def test_package_name_with_dots(self):
        """
        PI-002: 包名包含点号

        前置条件: 包名包含点号（如 pdfminer.six）
        预期结果: 成功创建 PackageInfo
        """
        pkg = PackageInfo(
            name="pdfminer.six",
            version="20221105",
            requires=[]
        )
        assert pkg.name == "pdfminer.six"

    def test_package_name_with_namespace(self):
        """
        PI-003: 命名空间包名

        前置条件: 包名包含多个点号（如 ruamel.yaml）
        预期结果: 成功创建 PackageInfo
        """
        pkg = PackageInfo(
            name="ruamel.yaml",
            version="0.17.21",
            requires=[]
        )
        assert pkg.name == "ruamel.yaml"

    def test_invalid_package_name_empty(self):
        """
        PI-004: 空包名

        前置条件: 包名为空
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid package name"):
            PackageInfo(name="", version="1.0.0", requires=[])

    def test_invalid_package_name_too_long(self):
        """
        PI-005: 包名过长

        前置条件: 包名超过 200 字符
        预期结果: 抛出 ValueError
        """
        long_name = "a" * 201
        with pytest.raises(ValueError, match="length must be 1-200"):
            PackageInfo(name=long_name, version="1.0.0", requires=[])

    def test_invalid_package_name_special_chars(self):
        """
        PI-006: 包名包含非法字符

        前置条件: 包名包含 @ 或其他非法字符
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid package name format"):
            PackageInfo(name="package@name", version="1.0.0", requires=[])

    def test_invalid_version_format(self):
        """
        PI-007: 无效版本号

        前置条件: 版本号格式错误
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid version format"):
            PackageInfo(name="numpy", version="invalid-version", requires=[])

    def test_invalid_requirement_format(self):
        """
        PI-008: 无效依赖声明

        前置条件: 依赖声明格式错误
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid requirement format"):
            PackageInfo(name="numpy", version="1.0.0", requires=["invalid req"])


class TestConflict:
    """Conflict 测试类"""

    def test_valid_conflict(self):
        """
        CF-001: 有效冲突信息

        前置条件: 无
        预期结果: 成功创建 Conflict
        """
        conflict = Conflict(
            package="pandas",
            requires="numpy<1.24",
            installed="1.24.0",
            suggestion="numpy==1.23.0"
        )
        assert conflict.package == "pandas"
        assert conflict.requires == "numpy<1.24"

    def test_empty_package_name(self):
        """
        CF-002: 空包名

        前置条件: 包名为空
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Package name cannot be empty"):
            Conflict(
                package="",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="numpy==1.23.0"
            )

    def test_invalid_suggestion_format(self):
        """
        CF-003: 无效修复建议格式

        前置条件: 修复建议格式错误
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid suggestion format"):
            Conflict(
                package="pandas",
                requires="numpy<1.24",
                installed="1.24.0",
                suggestion="invalid-suggestion"
            )


class TestSandboxResult:
    """SandboxResult 测试类"""

    def test_successful_result(self):
        """
        SR-001: 成功结果

        前置条件: 无
        预期结果: 成功创建 SandboxResult
        """
        result = SandboxResult(
            scheme="numpy==1.23.0",
            success=True,
            error=None
        )
        assert result.success is True
        assert result.error is None

    def test_failed_result(self):
        """
        SR-002: 失败结果

        前置条件: 无
        预期结果: 成功创建包含错误信息的 SandboxResult
        """
        result = SandboxResult(
            scheme="numpy==1.23.0",
            success=False,
            error="Package not found"
        )
        assert result.success is False
        assert result.error == "Package not found"

    def test_success_with_error(self):
        """
        SR-003: 成功时包含错误信息

        前置条件: success=True 但 error 不为 None
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Error must be None when success is True"):
            SandboxResult(
                scheme="numpy==1.23.0",
                success=True,
                error="Should be None"
            )

    def test_invalid_scheme_format(self):
        """
        SR-004: 无效修复方案格式

        前置条件: 修复方案格式错误
        预期结果: 抛出 ValueError
        """
        with pytest.raises(ValueError, match="Invalid scheme format"):
            SandboxResult(
                scheme="invalid-scheme",
                success=True,
                error=None
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
