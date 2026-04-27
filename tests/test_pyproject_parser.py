# -*- coding: utf-8 -*-
"""
pyproject.toml 解析器测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.pyenv_doctor.parsers.pyproject_parser import PyProjectParser


class TestPyProjectParser:
    """PyProjectParser 测试类"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = PyProjectParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """测试初始化"""
        parser = PyProjectParser()
        assert parser.logger is not None
    
    def test_parse_standard_dependencies(self):
        """测试解析标准依赖"""
        content = """
[project]
name = "myproject"
version = "1.0.0"
dependencies = [
    "requests>=2.28.0",
    "flask==2.0.0",
    "numpy~=1.21.0",
]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        assert any(dep["name"] == "requests" for dep in result)
        assert any(dep["name"] == "flask" for dep in result)
        assert any(dep["name"] == "numpy" for dep in result)
    
    def test_parse_optional_dependencies(self):
        """测试解析可选依赖"""
        content = """
[project]
name = "myproject"
dependencies = ["requests>=2.28.0"]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=22.0.0",
]
docs = [
    "sphinx>=4.0.0",
]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path, include_optional=True)
        
        assert len(result) >= 3
        assert any(dep["name"] == "pytest" for dep in result)
        assert any(dep["name"] == "sphinx" for dep in result)
    
    def test_parse_optional_dependencies_disabled(self):
        """测试禁用可选依赖解析"""
        content = """
[project]
name = "myproject"
dependencies = ["requests>=2.28.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path, include_optional=False)
        
        assert len(result) == 1
        assert result[0]["name"] == "requests"
    
    def test_parse_poetry_dependencies(self):
        """测试解析 Poetry 依赖"""
        content = """
[tool.poetry]
name = "myproject"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.28.0"
flask = "2.0.0"
numpy = "~1.21.0"
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        assert any(dep["name"] == "requests" for dep in result)
        assert any(dep["name"] == "flask" for dep in result)
        assert any(dep["name"] == "numpy" for dep in result)
    
    def test_parse_poetry_complex_version(self):
        """测试解析 Poetry 复杂版本声明"""
        content = """
[tool.poetry.dependencies]
python = "^3.8"
requests = { version = "^2.28.0", markers = "python_version >= '3.8'" }
flask = { version = "2.0.0" }
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
        requests_dep = next((d for d in result if d["name"] == "requests"), None)
        assert requests_dep is not None
    
    def test_parse_mixed_project_and_poetry(self):
        """测试同时包含 project 和 poetry 依赖"""
        content = """
[project]
dependencies = ["requests>=2.28.0"]

[tool.poetry.dependencies]
python = "^3.8"
flask = "2.0.0"
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
        assert any(dep["name"] == "requests" for dep in result)
        assert any(dep["name"] == "flask" for dep in result)
    
    def test_parse_file_not_found(self):
        """测试文件不存在的情况"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("/nonexistent/path/pyproject.toml")
    
    def test_parse_invalid_toml(self):
        """测试无效的 TOML 格式"""
        content = """
[project
name = "invalid"
"""
        file_path = self._create_temp_file(content)
        
        with pytest.raises(ValueError):
            self.parser.parse(file_path)
    
    def test_parse_empty_file(self):
        """测试空文件"""
        content = ""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 0
    
    def test_parse_only_python_version(self):
        """测试只有 Python 版本声明"""
        content = """
[tool.poetry.dependencies]
python = "^3.8"
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 0
    
    def test_parse_dependency_with_extras(self):
        """测试带额外功能的依赖"""
        content = """
[project]
dependencies = [
    "requests[security]>=2.28.0",
    "flask[async]==2.0.0",
]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_version_with_star(self):
        """测试使用 * 的版本"""
        content = """
[tool.poetry.dependencies]
python = "^3.8"
package = "*"
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert any(dep["name"] == "package" for dep in result)
    
    def test_parse_poetry_dict_version_with_markers(self):
        """测试带标记的 Poetry 字典版本"""
        content = """
[tool.poetry.dependencies]
python = "^3.8"
pywin32 = { version = ">=300", markers = "sys_platform == 'win32'" }
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert any(dep["name"] == "pywin32" for dep in result)
    
    def _create_temp_file(self, content: str) -> str:
        """创建临时 TOML 文件"""
        file_path = os.path.join(self.temp_dir, "pyproject.toml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path


class TestPyProjectParserPrivateMethods:
    """PyProjectParser 私有方法测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = PyProjectParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_dependency_simple(self):
        """测试解析简单依赖"""
        result = self.parser._parse_dependency("requests>=2.28.0")
        assert result is not None
        assert result["name"] == "requests"
        assert "2.28.0" in result["version"]
    
    def test_parse_dependency_exact_version(self):
        """测试解析精确版本"""
        result = self.parser._parse_dependency("flask==2.0.0")
        assert result is not None
        assert result["name"] == "flask"
        assert result["version"] == "==2.0.0"
    
    def test_parse_dependency_no_version(self):
        """测试解析无版本依赖"""
        result = self.parser._parse_dependency("requests")
        assert result is not None
        assert result["name"] == "requests"
        assert result["version"] == "*"
    
    def test_parse_dependency_invalid(self):
        """测试解析无效依赖"""
        result = self.parser._parse_dependency("invalid@@package")
        assert result is None
    
    def test_convert_poetry_version_caret(self):
        """测试转换 Poetry ^ 版本"""
        result = self.parser._convert_poetry_version("^2.28.0")
        assert result == ">=2.28.0"
    
    def test_convert_poetry_version_tilde(self):
        """测试转换 Poetry ~ 版本"""
        result = self.parser._convert_poetry_version("~2.28.0")
        assert result == "~=2.28.0"
    
    def test_convert_poetry_version_exact(self):
        """测试转换精确版本"""
        result = self.parser._convert_poetry_version("2.28.0")
        assert result == "==2.28.0"
    
    def test_convert_poetry_version_star(self):
        """测试转换 * 版本"""
        result = self.parser._convert_poetry_version("*")
        assert result == "*"
    
    def test_convert_poetry_version_dict_simple(self):
        """测试转换字典版本（简单）"""
        result = self.parser._convert_poetry_version({"version": "^2.28.0"})
        assert result == ">=2.28.0"
    
    def test_convert_poetry_version_dict_with_markers(self):
        """测试转换带标记的字典版本"""
        result = self.parser._convert_poetry_version({
            "version": "^2.28.0",
            "markers": "python_version >= '3.8'"
        })
        assert ">=2.28.0" in result
        assert "python_version" in result
    
    def test_convert_poetry_version_unknown_type(self):
        """测试转换未知类型版本"""
        result = self.parser._convert_poetry_version(None)
        assert result == "*"
    
    def _create_temp_file(self, content: str) -> str:
        """创建临时 TOML 文件"""
        file_path = os.path.join(self.temp_dir, "pyproject.toml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path


class TestPyProjectParserEdgeCases:
    """PyProjectParser 边缘场景测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = PyProjectParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_unicode_package_names(self):
        """测试解析 Unicode 包名"""
        content = """
[project]
dependencies = [
    "中文包>=1.0.0",
    "日本語パッケージ>=2.0.0",
]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_many_dependencies(self):
        """测试解析大量依赖"""
        deps = [f'"package{i}>=1.0.0"' for i in range(100)]
        content = f"""
[project]
dependencies = [
    {', '.join(deps)}
]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 100
    
    def test_parse_nested_optional_groups(self):
        """测试解析多个可选依赖组"""
        content = """
[project]
dependencies = ["requests>=2.28.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=22.0.0"]
test = ["pytest-cov>=3.0.0", "mock>=4.0.0"]
docs = ["sphinx>=4.0.0", "sphinx-rtd-theme>=1.0.0"]
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path, include_optional=True)
        
        assert len(result) >= 7
    
    def test_parse_poetry_with_python_constraint(self):
        """测试 Poetry 中 Python 版本约束被跳过"""
        content = """
[tool.poetry.dependencies]
python = ">=3.8,<4.0"
requests = "^2.28.0"
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        assert result[0]["name"] == "requests"
    
    def _create_temp_file(self, content: str) -> str:
        """创建临时 TOML 文件"""
        file_path = os.path.join(self.temp_dir, "pyproject.toml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
