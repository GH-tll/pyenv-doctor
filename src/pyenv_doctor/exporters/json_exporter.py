# -*- coding: utf-8 -*-
"""
JSON 报告导出器

将诊断报告导出为 JSON 格式
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from ..models.schemas import PackageInfo, Conflict, SandboxResult


class JSONExporter:
    """
    JSON 报告导出器
    
    将诊断结果导出为结构化的 JSON 格式，便于机器读取和后续处理。
    """
    
    def __init__(self):
        """初始化 JSONExporter"""
        self.format_version = "1.0"
    
    def export(
        self,
        packages: List[PackageInfo],
        conflicts: List[Conflict],
        results: List[SandboxResult],
        output_path: str
    ) -> Path:
        """
        导出诊断报告为 JSON 文件
        
        参数:
            packages: 包信息列表
            conflicts: 冲突列表
            results: 沙箱预演结果列表
            output_path: 输出文件路径
            
        返回:
            Path: 生成的 JSON 文件路径
        """
        report = self._build_report(packages, conflicts, results)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def _build_report(
        self,
        packages: List[PackageInfo],
        conflicts: List[Conflict],
        results: List[SandboxResult]
    ) -> Dict[str, Any]:
        """
        构建报告数据结构
        
        参数:
            packages: 包信息列表
            conflicts: 冲突列表
            results: 沙箱预演结果列表
            
        返回:
            Dict[str, Any]: 报告字典
        """
        # 统计信息
        total_packages = len(packages)
        total_conflicts = len(conflicts)
        successful_fixes = sum(1 for r in results if r.success)
        failed_fixes = sum(1 for r in results if not r.success)
        
        # 构建报告
        report = {
            "metadata": {
                "format_version": self.format_version,
                "generated_at": datetime.now().isoformat(),
                "tool_name": "PyEnv Doctor",
                "tool_version": "0.1.4"
            },
            "summary": {
                "total_packages": total_packages,
                "total_conflicts": total_conflicts,
                "successful_fixes": successful_fixes,
                "failed_fixes": failed_fixes,
                "health_score": self._calculate_health_score(total_packages, total_conflicts)
            },
            "packages": [
                {
                    "name": pkg.name,
                    "version": pkg.version,
                    "requires": pkg.requires
                }
                for pkg in packages
            ],
            "conflicts": [
                {
                    "package": conflict.package,
                    "requires": conflict.requires,
                    "installed": conflict.installed,
                    "suggestion": conflict.suggestion
                }
                for conflict in conflicts
            ],
            "sandbox_results": [
                {
                    "scheme": result.scheme,
                    "success": result.success,
                    "error": result.error
                }
                for result in results
            ],
            "recommendations": self._generate_recommendations(conflicts, results)
        }
        
        return report
    
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
        
        # 健康分数 = 100 * (1 - 冲突率)
        conflict_rate = total_conflicts / total_packages
        score = 100 * (1 - min(conflict_rate, 1.0))
        
        return round(score, 2)
    
    def _generate_recommendations(
        self,
        conflicts: List[Conflict],
        results: List[SandboxResult]
    ) -> List[Dict[str, Any]]:
        """
        生成修复建议
        
        参数:
            conflicts: 冲突列表
            results: 沙箱预演结果列表
            
        返回:
            List[Dict[str, Any]]: 建议列表
        """
        recommendations = []
        
        if not conflicts:
            recommendations.append({
                "type": "info",
                "title": "环境健康",
                "description": "未检测到依赖冲突，环境状态良好"
            })
        else:
            # 成功验证的建议
            successful_schemes = [r for r in results if r.success]
            if successful_schemes:
                packages_to_update = list(set(
                    scheme.split("==")[0] for scheme in [r.scheme for r in successful_schemes]
                ))
                recommendations.append({
                    "type": "success",
                    "title": "推荐修复方案",
                    "description": f"检测到 {len(conflicts)} 个冲突，{len(successful_schemes)} 个修复方案已通过沙箱验证",
                    "packages": packages_to_update,
                    "action": "建议执行以下命令修复环境"
                })
            
            # 失败的方案
            failed_schemes = [r for r in results if not r.success]
            if failed_schemes:
                recommendations.append({
                    "type": "warning",
                    "title": "部分方案验证失败",
                    "description": f"{len(failed_schemes)} 个修复方案在沙箱中验证失败，建议手动处理",
                    "failed_packages": [r.scheme for r in failed_schemes]
                })
            
            # 大量冲突建议
            if len(conflicts) > 10:
                recommendations.append({
                    "type": "danger",
                    "title": "环境严重污染",
                    "description": f"检测到 {len(conflicts)} 个冲突，建议创建新的虚拟环境",
                    "action": "考虑重新创建虚拟环境以获得更干净的环境"
                })
        
        return recommendations
