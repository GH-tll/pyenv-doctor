# -*- coding: utf-8 -*-
"""
requirements.txt 解析器测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.pyenv_doctor.parsers.requirements_parser import RequirementsParser


class TestRequirementsParser:
    """RequirementsParser 测试类"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = RequirementsParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """测试初始化"""
        parser = RequirementsParser()
        assert parser.logger is not None
    
    def test_parse_simple_requirements(self):
        """测试解析简单的 requirements.txt"""
        content = """requests==2.28.0
flask==2.0.0
numpy>=1.21.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        assert any(dep["name"] == "requests" for dep in result)
        assert any(dep["name"] == "flask" for dep in result)
        assert any(dep["name"] == "numpy" for dep in result)
    
    def test_parse_with_comments(self):
        """测试解析包含注释的文件"""
        content = """# 这是注释
requests==2.28.0
# 另一个注释
flask==2.0.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_with_empty_lines(self):
        """测试解析包含空行的文件"""
        content = """requests==2.28.0

flask==2.0.0

numpy>=1.21.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
    
    def test_parse_with_inline_comments(self):
        """测试解析包含行内注释的依赖"""
        content = """requests==2.28.0  # HTTP 库
flask==2.0.0  # Web 框架
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
        assert result[0]["name"] == "requests"
        assert result[1]["name"] == "flask"
    
    def test_parse_with_r_flag(self):
        """测试解析包含 -r 标志的文件"""
        content = """-r base.txt
requests==2.28.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        assert result[0]["name"] == "requests"
    
    def test_parse_with_other_flags(self):
        """测试解析包含其他标志的文件"""
        content = """--index-url https://pypi.org/simple/
requests==2.28.0
-e git+https://github.com/example/repo.git
flask==2.0.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_version_operators(self):
        """测试解析不同版本操作符"""
        content = """requests==2.28.0
flask>=2.0.0
numpy<=1.21.0
pandas~=1.3.0
scipy!=1.7.0
matplotlib>3.4.0
seaborn<0.12.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 7
    
    def test_parse_no_version(self):
        """测试解析无版本声明的包"""
        content = """requests
flask
numpy
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        assert all(dep["version"] == "*" for dep in result)
    
    def test_parse_file_not_found(self):
        """测试文件不存在的情况"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("/nonexistent/path/requirements.txt")
    
    def test_parse_empty_file(self):
        """测试空文件"""
        content = ""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 0
    
    def test_parse_only_comments(self):
        """测试只有注释的文件"""
        content = """# 注释 1
# 注释 2
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 0
    
    def test_parse_with_whitespace(self):
        """测试包含空白字符的解析"""
        content = """  requests==2.28.0  
\tflask==2.0.0\t
  numpy>=1.21.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
    
    def test_parse_complex_version_specifiers(self):
        """测试解析复杂版本说明符"""
        content = """requests>=2.28.0,<3.0.0
flask==2.0.0
numpy>=1.20.0,<=1.23.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
    
    def test_parse_package_with_extras(self):
        """测试解析带额外功能的包"""
        content = """requests[security]>=2.28.0
flask[async]==2.0.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2


class TestRequirementsParserParseString:
    """RequirementsParser parse_string 方法测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = RequirementsParser()
    
    def test_parse_string_basic(self):
        """测试从字符串解析基本依赖"""
        content = """requests==2.28.0
flask==2.0.0
"""
        result = self.parser.parse_string(content)
        
        assert len(result) == 2
    
    def test_parse_string_with_comments(self):
        """测试从字符串解析带注释的依赖"""
        content = """# 注释
requests==2.28.0
# 另一个注释
flask==2.0.0
"""
        result = self.parser.parse_string(content)
        
        assert len(result) == 2
    
    def test_parse_string_empty(self):
        """测试从空字符串解析"""
        content = ""
        result = self.parser.parse_string(content)
        
        assert len(result) == 0
    
    def test_parse_string_with_empty_lines(self):
        """测试从字符串解析带空行的依赖"""
        content = """requests==2.28.0

flask==2.0.0

"""
        result = self.parser.parse_string(content)
        
        assert len(result) == 2
    
    def test_parse_string_single_line(self):
        """测试解析单行依赖"""
        content = "requests==2.28.0"
        result = self.parser.parse_string(content)
        
        assert len(result) == 1
        assert result[0]["name"] == "requests"
    
    def test_parse_string_multiple_lines(self):
        """测试解析多行依赖"""
        content = "\n".join([f"package{i}=={i}.0.0" for i in range(1, 51)])
        result = self.parser.parse_string(content)
        
        assert len(result) == 50
    
    def test_parse_string_with_trailing_newlines(self):
        """测试解析带尾部换行符的字符串"""
        content = """requests==2.28.0
flask==2.0.0


"""
        result = self.parser.parse_string(content)
        
        assert len(result) == 2


class TestRequirementsParserPrivateMethods:
    """RequirementsParser 私有方法测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = RequirementsParser()
    
    def test_parse_line_exact_version(self):
        """测试解析精确版本行"""
        result = self.parser._parse_line("requests==2.28.0")
        assert result is not None
        assert result["name"] == "requests"
        assert result["version"] == "==2.28.0"
    
    def test_parse_line_greater_version(self):
        """测试解析大于版本行"""
        result = self.parser._parse_line("requests>=2.28.0")
        assert result is not None
        assert result["name"] == "requests"
        assert result["version"] == ">=2.28.0"
    
    def test_parse_line_no_version(self):
        """测试解析无版本行"""
        result = self.parser._parse_line("requests")
        assert result is not None
        assert result["name"] == "requests"
        assert result["version"] == "*"
    
    def test_parse_line_with_comment(self):
        """测试解析带注释行"""
        result = self.parser._parse_line("requests==2.28.0  # comment")
        assert result is not None
        assert result["name"] == "requests"
    
    def test_parse_line_with_environment_marker(self):
        """测试解析带环境标记行"""
        result = self.parser._parse_line("pywin32>=300; sys_platform == 'win32'")
        assert result is not None
        assert result["name"] == "pywin32"
    
    def test_parse_line_invalid(self):
        """测试解析无效行"""
        result = self.parser._parse_line("invalid@@package")
        assert result is None
    
    def test_parse_line_with_spaces(self):
        """测试解析带空格的行"""
        result = self.parser._parse_line("  requests  ==  2.28.0  ")
        assert result is not None
        assert result["name"] == "requests"
    
    def test_parse_line_package_with_dots(self):
        """测试解析带点的包名"""
        result = self.parser._parse_line("zope.interface>=5.0.0")
        assert result is not None
        assert result["name"] == "zope.interface"
    
    def test_parse_line_package_with_underscores(self):
        """测试解析带下划线的包名"""
        result = self.parser._parse_line("beautifulsoup4>=4.9.0")
        assert result is not None
        assert result["name"] == "beautifulsoup4"
    
    def test_parse_line_package_with_hyphens(self):
        """测试解析带连字符的包名"""
        result = self.parser._parse_line("some-package>=1.0.0")
        assert result is not None
        assert result["name"] == "some-package"
    
    def test_parse_line_version_with_local(self):
        """测试解析带本地版本的行"""
        result = self.parser._parse_line("package==1.0.0+local.build")
        assert result is not None
        assert result["name"] == "package"
    
    def test_parse_line_version_with_prerelease(self):
        """测试解析带预发布版本的行"""
        result = self.parser._parse_line("package==2.0.0b1")
        assert result is not None
        assert result["name"] == "package"
    
    def test_parse_line_complex_specifier(self):
        """测试解析复杂版本说明符"""
        result = self.parser._parse_line("package>=1.0.0,<2.0.0")
        assert result is not None
        assert result["name"] == "package"


class TestRequirementsParserEdgeCases:
    """RequirementsParser 边缘场景测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.parser = RequirementsParser()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_unicode_package_names(self):
        """测试解析 Unicode 包名"""
        content = """中文包>=1.0.0
日本語パッケージ>=2.0.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_very_long_line(self):
        """测试解析超长行"""
        long_name = "very_long_package_name_" * 20
        content = f"{long_name}>=1.0.0"
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
    
    def test_parse_many_requirements(self):
        """测试解析大量依赖"""
        content = "\n".join([f"package{i}=={i}.0.0" for i in range(1, 501)])
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 500
    
    def test_parse_mixed_valid_invalid(self):
        """测试解析混合有效和无效依赖"""
        content = """requests==2.28.0
invalid@@package
flask==2.0.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_version_with_dev_release(self):
        """测试解析带开发版本的依赖"""
        content = """package==1.0.0.dev1
another==2.0.0.post1
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
    
    def test_parse_git_url_skipped(self):
        """测试 Git URL 被跳过"""
        content = """git+https://github.com/user/repo.git
requests==2.28.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
    
    def test_parse_http_url_skipped(self):
        """测试 HTTP URL 被跳过"""
        content = """https://github.com/user/repo/archive/main.zip
requests==2.28.0
"""
        file_path = self._create_temp_file(content)
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
    
    def _create_temp_file(self, content: str) -> str:
        """创建临时文件"""
        file_path = os.path.join(self.temp_dir, "requirements.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
