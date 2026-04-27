# -*- coding: utf-8 -*-
"""
JSON 导出器测试
"""

import pytest
import tempfile
import os
import json
from pathlib import Path

from src.pyenv_doctor.models.schemas import PackageInfo, Conflict, SandboxResult
from src.pyenv_doctor.exporters.json_exporter import JSONExporter


class TestJSONExporter:
    """JSONExporter 测试类"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.exporter = JSONExporter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """测试初始化"""
        exporter = JSONExporter()
        assert exporter.format_version == "1.0"
    
    def test_export_basic(self):
        """测试基本导出功能"""
        packages = [
            PackageInfo(name="requests", version="2.28.0", installed_version="2.28.0"),
            PackageInfo(name="flask", version="2.0.0", installed_version="2.0.0"),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        assert result_file.exists()
        assert result_file.suffix == ".json"
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "summary" in data
        assert "packages" in data
        assert len(data["packages"]) == 2
    
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
        
        output_path = os.path.join(self.temp_dir, "report_conflicts.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["summary"]["total_conflicts"] == 1
        assert len(data["conflicts"]) == 1
        assert data["conflicts"][0]["package"] == "numpy"
    
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
        
        output_path = os.path.join(self.temp_dir, "report_sandbox.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data["sandbox_results"]) == 2
        assert data["sandbox_results"][0]["success"] is True
        assert data["sandbox_results"][1]["success"] is False
    
    def test_export_creates_parent_directories(self):
        """测试自动创建父目录"""
        packages = []
        conflicts = []
        results = []
        
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "report.json")
        result_file = self.exporter.export(packages, conflicts, results, nested_path)
        
        assert result_file.exists()
        assert result_file.parent.exists()
    
    def test_export_metadata(self):
        """测试导出元数据"""
        packages = []
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_metadata.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["metadata"]["format_version"] == "1.0"
        assert data["metadata"]["tool_name"] == "PyEnv Doctor"
        assert "generated_at" in data["metadata"]
    
    def test_export_health_score(self):
        """测试健康分数计算"""
        packages = [PackageInfo(name=f"pkg{i}", version="1.0.0", installed_version="1.0.0") for i in range(100)]
        conflicts = [
            Conflict(package=f"conflict{i}", requires=">=2.0", installed="1.0", suggestion="upgrade")
            for i in range(10)
        ]
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_health.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["summary"]["health_score"] == 90.0
    
    def test_export_recommendations_no_conflicts(self):
        """测试无冲突时的建议"""
        packages = [PackageInfo(name="pkg", version="1.0.0", installed_version="1.0.0")]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_no_conflicts.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["type"] == "info"
        assert data["recommendations"][0]["title"] == "环境健康"
    
    def test_export_recommendations_with_success(self):
        """测试有成功方案时的建议"""
        packages = []
        conflicts = [
            Conflict(package="numpy", requires=">=1.20.0", installed="1.19.0", suggestion="upgrade"),
        ]
        results = [
            SandboxResult(scheme="numpy==1.21.0", success=True, error=None),
        ]
        
        output_path = os.path.join(self.temp_dir, "report_success.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        recommendations = data["recommendations"]
        success_rec = next((r for r in recommendations if r["type"] == "success"), None)
        assert success_rec is not None
        assert "packages" in success_rec
    
    def test_export_recommendations_with_failures(self):
        """测试有失败方案时的建议"""
        packages = []
        conflicts = []
        results = [
            SandboxResult(scheme="numpy==1.21.0", success=False, error="Failed"),
        ]
        
        output_path = os.path.join(self.temp_dir, "report_failures.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        recommendations = data["recommendations"]
        warning_rec = next((r for r in recommendations if r["type"] == "warning"), None)
        assert warning_rec is not None
        assert "failed_packages" in warning_rec
    
    def test_export_recommendations_many_conflicts(self):
        """测试大量冲突时的建议"""
        packages = []
        conflicts = [
            Conflict(package=f"conflict{i}", requires=">=2.0", installed="1.0", suggestion="upgrade")
            for i in range(15)
        ]
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_many_conflicts.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        recommendations = data["recommendations"]
        danger_rec = next((r for r in recommendations if r["type"] == "danger"), None)
        assert danger_rec is not None
        assert danger_rec["title"] == "环境严重污染"
    
    def test_export_large_dataset(self):
        """测试导出大数据集"""
        packages = [PackageInfo(name=f"pkg{i}", version="1.0.0", installed_version="1.0.0") for i in range(500)]
        conflicts = [
            Conflict(package=f"conflict{i}", requires=">=2.0", installed="1.0", suggestion="upgrade")
            for i in range(50)
        ]
        results = [
            SandboxResult(scheme=f"pkg{i}==2.0.0", success=(i % 2 == 0), error=None if i % 2 == 0 else "Error")
            for i in range(100)
        ]
        
        output_path = os.path.join(self.temp_dir, "report_large.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        assert result_file.exists()
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert len(data["packages"]) == 500
        assert len(data["conflicts"]) == 50
        assert len(data["sandbox_results"]) == 100
    
    def test_export_unicode_content(self):
        """测试导出 Unicode 内容"""
        packages = [
            PackageInfo(name="中文包", version="1.0.0", installed_version="1.0.0"),
            PackageInfo(name="日本語パッケージ", version="2.0.0", installed_version="2.0.0"),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_unicode.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert any(pkg["name"] == "中文包" for pkg in data["packages"])
        assert any(pkg["name"] == "日本語パッケージ" for pkg in data["packages"])
    
    def test_export_empty_everything(self):
        """测试全空数据的导出"""
        packages = []
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_empty.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["summary"]["total_packages"] == 0
        assert data["summary"]["total_conflicts"] == 0
        assert data["summary"]["health_score"] == 100.0
    
    def test_health_score_calculation(self):
        """测试健康分数计算"""
        assert self.exporter._calculate_health_score(100, 0) == 100.0
        assert self.exporter._calculate_health_score(100, 10) == 90.0
        assert self.exporter._calculate_health_score(100, 50) == 50.0
        assert self.exporter._calculate_health_score(100, 100) == 0.0
        assert self.exporter._calculate_health_score(0, 0) == 100.0


class TestJSONExporterEdgeCases:
    """JSONExporter 边缘场景测试"""
    
    def setup_method(self):
        """每个测试前的设置"""
        self.exporter = JSONExporter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """每个测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_with_special_characters(self):
        """测试包含特殊字符的导出"""
        packages = [
            PackageInfo(name="pkg@special", version="1.0.0+local.build", installed_version="1.0.0"),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_special.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["packages"][0]["name"] == "pkg@special"
    
    def test_export_with_very_long_names(self):
        """测试超长包名的导出"""
        packages = [
            PackageInfo(
                name="very_long_package_name_" * 20,
                version="1.0.0",
                installed_version="1.0.0"
            ),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_long.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        assert result_file.exists()
    
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
        
        output_path = os.path.join(self.temp_dir, "report_mixed.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["summary"]["successful_fixes"] == 2
        assert data["summary"]["failed_fixes"] == 2
    
    def test_export_json_formatting(self):
        """测试 JSON 格式化"""
        packages = [PackageInfo(name="pkg", version="1.0.0", installed_version="1.0.0")]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_format.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        content = result_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        assert len(lines) > 1
        assert "  " in content
    
    def test_export_preserves_encoding(self):
        """测试编码保持"""
        packages = [
            PackageInfo(name="café", version="1.0.0", installed_version="1.0.0"),
            PackageInfo(name="日本語", version="2.0.0", installed_version="2.0.0"),
            PackageInfo(name="العربية", version="3.0.0", installed_version="3.0.0"),
        ]
        conflicts = []
        results = []
        
        output_path = os.path.join(self.temp_dir, "report_encoding.json")
        result_file = self.exporter.export(packages, conflicts, results, output_path)
        
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert any(pkg["name"] == "café" for pkg in data["packages"])
        assert any(pkg["name"] == "日本語" for pkg in data["packages"])
        assert any(pkg["name"] == "العربية" for pkg in data["packages"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
