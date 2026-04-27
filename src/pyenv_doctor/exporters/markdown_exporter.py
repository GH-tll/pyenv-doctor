# -*- coding: utf-8 -*-
"""
Markdown 报告导出器

将诊断报告导出为 Markdown 格式
"""

from datetime import datetime
from pathlib import Path
from typing import List

from ..models.schemas import PackageInfo, Conflict, SandboxResult


class MarkdownExporter:
    """
    Markdown 报告导出器
    
    将诊断结果导出为可读性强的 Markdown 格式报告，适合人工阅读和分享。
    """
    
    def __init__(self):
        """初始化 MarkdownExporter"""
        self.format_version = "1.0"
    
    def export(
        self,
        packages: List[PackageInfo],
        conflicts: List[Conflict],
        results: List[SandboxResult],
        output_path: str
    ) -> Path:
        """
        导出诊断报告为 Markdown 文件
        
        参数:
            packages: 包信息列表
            conflicts: 冲突列表
            results: 沙箱预演结果列表
            output_path: 输出文件路径
            
        返回:
            Path: 生成的 Markdown 文件路径
        """
        content = self._generate_content(packages, conflicts, results)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return output_file
    
    def _generate_content(
        self,
        packages: List[PackageInfo],
        conflicts: List[Conflict],
        results: List[SandboxResult]
    ) -> str:
        """
        生成 Markdown 内容
        
        参数:
            packages: 包信息列表
            conflicts: 冲突列表
            results: 沙箱预演结果列表
            
        返回:
            str: Markdown 内容
        """
        lines = []
        
        # 标题
        lines.append("# 🔍 PyEnv Doctor 诊断报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**工具版本**: v0.1.4")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 概要统计
        lines.append("## 📊 概要统计")
        lines.append("")
        total_packages = len(packages)
        total_conflicts = len(conflicts)
        successful_fixes = sum(1 for r in results if r.success)
        failed_fixes = sum(1 for r in results if not r.success)
        health_score = self._calculate_health_score(total_packages, total_conflicts)
        
        lines.append(f"- **总包数**: {total_packages}")
        lines.append(f"- **冲突数**: {total_conflicts}")
        lines.append(f"- **成功验证**: {successful_fixes} 个方案")
        lines.append(f"- **验证失败**: {failed_fixes} 个方案")
        lines.append(f"- **健康分数**: {health_score}/100")
        lines.append("")
        
        # 健康状态图标
        if health_score >= 90:
            lines.append("✅ **环境状态**: 优秀")
        elif health_score >= 70:
            lines.append("⚠️ **环境状态**: 良好（存在少量冲突）")
        elif health_score >= 50:
            lines.append("⚠️ **环境状态**: 一般（建议修复）")
        else:
            lines.append("❌ **环境状态**: 较差（强烈建议修复）")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 冲突详情
        if conflicts:
            lines.append("## ⚠️ 检测到的冲突")
            lines.append("")
            for i, conflict in enumerate(conflicts, 1):
                lines.append(f"### 冲突 {i}")
                lines.append("")
                lines.append(f"- **包名**: `{conflict.package}`")
                lines.append(f"- **依赖要求**: `{conflict.requires}`")
                lines.append(f"- **已安装版本**: `{conflict.installed}`")
                lines.append(f"- **修复建议**: `{conflict.suggestion}`")
                lines.append("")
            lines.append("---")
            lines.append("")
        else:
            lines.append("## ✅ 无冲突")
            lines.append("")
            lines.append("未检测到依赖冲突，环境状态良好！")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # 沙箱预演结果
        if results:
            lines.append("## 🧪 沙箱预演结果")
            lines.append("")
            for i, result in enumerate(results, 1):
                status = "✅" if result.success else "❌"
                lines.append(f"{status} **方案 {i}**: `{result.scheme}`")
                if not result.success:
                    lines.append(f"   - 错误：{result.error}")
                lines.append("")
            lines.append("---")
            lines.append("")
        
        # 修复建议
        lines.append("## 💡 修复建议")
        lines.append("")
        
        successful_schemes = [r for r in results if r.success]
        failed_schemes = [r for r in results if not r.success]
        
        if successful_schemes:
            lines.append("### ✅ 推荐方案（已验证）")
            lines.append("")
            lines.append("以下方案已在沙箱环境中验证可行：")
            lines.append("")
            for i, result in enumerate(successful_schemes, 1):
                lines.append(f"{i}. `pip install {result.scheme}`")
            lines.append("")
            
            # 一键执行命令
            schemes_str = " ".join([r.scheme for r in successful_schemes])
            lines.append("**一键执行命令**:")
            lines.append("")
            lines.append(f"```bash")
            lines.append(f"pip install {schemes_str}")
            lines.append(f"```")
            lines.append("")
        
        if failed_schemes:
            lines.append("### ⚠️ 验证失败的方案")
            lines.append("")
            lines.append("以下方案在沙箱中验证失败，建议手动处理：")
            lines.append("")
            for result in failed_schemes:
                lines.append(f"- `{result.scheme}`: {result.error}")
            lines.append("")
        
        if not conflicts:
            lines.append("环境无冲突，无需修复。")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # 健康建议
        lines.append("## 📋 健康建议")
        lines.append("")
        
        if total_conflicts == 0:
            lines.append("✅ 环境非常健康，请继续保持！")
        elif total_conflicts <= 5:
            lines.append("⚠️ 存在少量冲突，建议及时修复以避免潜在问题。")
        elif total_conflicts <= 20:
            lines.append("⚠️ 冲突较多，建议尽快修复或考虑重建虚拟环境。")
        else:
            lines.append("❌ 环境严重污染，强烈建议创建新的虚拟环境！")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*报告由 PyEnv Doctor 生成*")
        lines.append("")
        
        return "\n".join(lines)
    
    def _calculate_health_score(self, total_packages: int, total_conflicts: int) -> float:
        """
        计算环境健康分数
        
        参数:
            total_packages: 总包数
            total_conflicts: 冲突数
            
        返回:
            float: 健康分数（0-100）
        """
        if total_packages == 0:
            return 100.0
        
        conflict_rate = total_conflicts / total_packages
        score = 100 * (1 - min(conflict_rate, 1.0))
        
        return round(score, 2)
