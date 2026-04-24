# -*- coding: utf-8 -*-
"""
Tools 模块单元测试

测试用例覆盖:
- PipTool 测试: PT-001 至 PT-003
- VenvTool 测试: VT-001 至 VT-003
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyenv_doctor.tools.pip_tool import PipTool
from pyenv_doctor.tools.venv_tool import VenvTool


class TestPipTool:
    """PipTool 测试类"""

    def test_pip_tool_name(self):
        """
        PT-001: 工具名称

        前置条件: 无
        预期结果: name 属性为 "pip"
        """
        tool = PipTool()
        assert tool.name == "pip"

    def test_pip_tool_execute_success(self):
        """
        PT-002: 成功执行命令

        前置条件: pip 命令可用
        预期结果: 返回命令输出
        """
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "Package    Version\n---------- -------\nnumpy      1.24.0\n"
            mock_run.return_value = mock_result
            
            tool = PipTool()
            result = tool.execute("list")
            
            assert "numpy" in result

    def test_pip_tool_execute_failure(self):
        """
        PT-003: 执行失败

        前置条件: pip 命令失败
        预期结果: 返回错误信息
        """
        import subprocess
        
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd="pip",
                stderr="Package not found"
            )
            
            tool = PipTool()
            result = tool.execute("install nonexistent-package")
            
            assert "Error:" in result


class TestVenvTool:
    """VenvTool 测试类"""

    def test_venv_tool_name(self):
        """
        VT-001: 工具名称

        前置条件: 无
        预期结果: name 属性为 "venv"
        """
        tool = VenvTool()
        assert tool.name == "venv"

    def test_venv_tool_execute_success(self):
        """
        VT-002: 成功创建虚拟环境

        前置条件: 无
        预期结果: 返回成功信息
        """
        with patch("venv.create") as mock_create:
            mock_create.return_value = None
            
            tool = VenvTool()
            result = tool.execute("/tmp/test_env")
            
            assert "Created venv" in result

    def test_venv_tool_execute_failure(self):
        """
        VT-003: 创建失败

        前置条件: 路径无效
        预期结果: 返回错误信息
        """
        with patch("venv.create") as mock_create:
            mock_create.side_effect = Exception("Invalid path")
            
            tool = VenvTool()
            result = tool.execute("/invalid/path")
            
            assert "Error:" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
