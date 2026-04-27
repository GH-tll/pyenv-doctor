# -*- coding: utf-8 -*-
"""
Markdown 导出器测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.pyenv_doctor.models.schemas import PackageInfo, Conflict, SandboxResult
from src.pyenv_doctor.exporters.markdown_exporter import MarkdownExporter


class TestMarkdownExporter:
    """MarkdownExporter 测试类"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.exporter = MarkdownExporter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """测试初始化"""
        exporter = MarkdownExporter()
        assert exporter.format_version == "1.0"
    
    def test_export_basic(self):
        """测试基本导出功能"""
        packages = [
            PackageInfo(name="requests", version="2.28.0", installed_version="2.28.0"),
            PackageInfo(name="flask", version="2.0.0", installed_version="2.0.0"),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        assert result_file.exists()
        assert result_file.suffix == ".md"
        
        content = result_file.read_text(encoding="utf-8")
        assert "PyEnv Doctor 诊断报告" in content
        assert "生成时间" in content
        assert "总包数" in content
    
    def test_export_with_conflicts(self):
        """测试包含冲突的导出"""
        packages = [
            PackageInfo(name="requests", version="2.28.0", installed_version="2.28.0"),
        ]
        conflicts = [
            Conflict(
                package="numpy",
                requires=">=1.20.0",
                installed="1.19.0",
                suggestion="upgrade to 1.21.0"
            ),
        ]
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_conflicts.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "检测到的冲突" in content
        assert "numpy" in content
        assert "1.19.0" in content
    
    def test_export_with_sandbox_results(self):
        """测试包含沙箱结果的导出"""
        packages = []
        conflicts = [
            Conflict(
                package="numpy",
                requires=">=1.20.0",
                installed="1.19.0",
                suggestion="upgrade to 1.21.0"
            ),
        ]
        results = [
            SandboxResult(
                scheme="numpy==1.21.0",
                success=True,
                error=None
            ),
            SandboxResult(
                scheme="numpy==1.22.0",
                success=False,
                error="Installation failed"
            ),
        ]
        
        output_path = os.path.join(self.temp_dir, "report_sandbox.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "沙箱预演结果" in content
        assert "推荐方案（已验证）" in content
        assert "numpy==1.21.0" in content
        assert "验证失败的方案" in content
    
    def test_export_creates_parent_directories(self):
        """测试自动创建父目录"""
        packages = []
        conflicts = []
        results = []
        
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "report.md")
        result_file = self.exporter.export(packages, conflicts, results, nested_path)
        
        assert result_file.exists()
        assert result_file.parent.exists()
    
    def test_health_score_calculation(self):
        """测试健康分数计算"""
        assert self.exporter._calculate_health_score(100, 0) == 100.0
        assert self.exporter._calculate_health_score(100, 5) == 95.0
        assert self.exporter._calculate_health_score(100, 50) == 50.0
        assert self.exporter._calculate_health_score(100, 100) == 0.0
        assert self.exporter._calculate_health_score(0, 0) == 100.0
    
    def test_export_large_conflict_list(self):
        """测试大量冲突的导出"""
        packages = [PackageInfo(name=f"pkg{i}", version="1.0.0", installed_version="1.0.0") for i in range(50)]
        conflicts = [
            Conflict(
                package=f"conflict_pkg_{i}",
                requires=">=2.0.0",
                installed="1.0.0",
                suggestion=f"upgrade to 2.{i}.0"
            )
            for i in range(25)
        ]
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_large.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "检测到的冲突" in content
        assert "conflict_pkg_0" in content
        assert "conflict_pkg_24" in content
    
    def test_export_multiple_successful_schemes(self):
        """测试多个成功方案的导出"""
        packages = []
        conflicts = []
        results = [
            SandboxResult(scheme="pkg1==1.0.0", success=True, error=None),
            SandboxResult(scheme="pkg2==2.0.0", success=True, error=None),
            SandboxResult(scheme="pkg3==3.0.0", success=True, error=None),
        ]
        
        output_path = os.path.join(self.temp_dir, "report_multi_success.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "一键执行命令" in content
        assert "pip install pkg1==1.0.0 pkg2==2.0.0 pkg3==3.0.0" in content
    
    def test_export_all_failed_schemes(self):
        """测试全部失败的方案导出"""
        packages = []
        conflicts = []
        results = [
            SandboxResult(scheme="pkg1==1.0.0", success=False, error="Error 1"),
            SandboxResult(scheme="pkg2==2.0.0", success=False, error="Error 2"),
        ]
        
        output_path = os.path.join(self.temp_dir, "report_all_failed.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "验证失败的方案" in content
        assert "Error 1" in content
        assert "Error 2" in content
    
    def test_export_health_status_excellent(self):
        """测试优秀健康状态的输出"""
        packages = [PackageInfo(name="pkg", version="1.0.0", installed_version="1.0.0")]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_excellent.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "环境状态" in content
        assert "优秀" in content
    
    def test_export_health_status_poor(self):
        """测试较差健康状态的输出"""
        packages = [PackageInfo(name=f"pkg{i}", version="1.0.0", installed_version="1.0.0") for i in range(100)]
        conflicts = [
            Conflict(package=f"conflict{i}", requires=">=2.0", installed="1.0", suggestion="upgrade")
            for i in range(80)
        ]
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_poor.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "环境严重污染" in content or "环境状态" in content
    
    def test_export_no_conflicts_message(self):
        """测试无冲突时的消息"""
        packages = [PackageInfo(name="pkg", version="1.0.0", installed_version="1.0.0")]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_no_conflicts.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "无冲突" in content
        assert "环境无冲突，无需修复" in content
    
    def test_export_with_unicode_content(self):
        """测试包含 Unicode 内容的导出"""
        packages = [
            PackageInfo(name="中文包", version="1.0.0", installed_version="1.0.0"),
            PackageInfo(name="日本語パッケージ", version="2.0.0", installed_version="2.0.0"),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_unicode.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "中文包" in content
        assert "日本語パッケージ" in content
    
    def test_export_generates_timestamp(self):
        """测试生成时间戳"""
        packages = []
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_timestamp.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "生成时间" in content
        import re
        timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, content)


class TestMarkdownExporterEdgeCases:
    """MarkdownExporter 边缘场景测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.exporter = MarkdownExporter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_empty_everything(self):
        """测试全空数据的导出"""
        packages = []
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_empty.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        assert result_file.exists()
        content = result_file.read_text(encoding="utf-8")
        assert "PyEnv Doctor 诊断报告" in content
        assert "总包数" in content
    
    def test_export_very_long_package_name(self):
        """测试超长包名的导出"""
        packages = [
            PackageInfo(
                name="very_long_package_name_that_is_unusually_long_" * 10,
                version="1.0.0",
                installed_version="1.0.0"
            ),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_long_name.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        assert result_file.exists()
    
    def test_export_special_characters_in_conflicts(self):
        """测试冲突中包含特殊字符的导出"""
        packages = []
        conflicts = [
            Conflict(
                package="pkg@special#chars!",
                requires=">=1.0.0; python_version>='3.8'",
                installed="1.0.0+local.build",
                suggestion="upgrade to 2.0.0-beta.1"
            ),
        ]
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_special_chars.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "pkg@special#chars!" in content
    
    def test_export_mixed_success_failure(self):
        """测试混合成功和失败结果的导出"""
        packages = []
        conflicts = []
        results = [
            SandboxResult(scheme="success1", success=True, error=None),
            SandboxResult(scheme="fail1", success=False, error="Error"),
            SandboxResult(scheme="success2", success=True, error=None),
            SandboxResult(scheme="fail2", success=False, error="Error"),
        ]
        
        output_path = os.path.join(self.temp_dir, "report_mixed.md")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        assert "推荐方案（已验证）" in content
        assert "验证失败的方案" in content
        assert "success1" in content
        assert "fail1" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
