# -*- coding: utf-8 -*-
"""
requirements.txt 解析器

解析 requirements.txt 文件中的依赖声明
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

from packaging.requirements import Requirement, InvalidRequirement


class RequirementsParser:
    """
    requirements.txt 解析器
    
    支持解析标准 requirements.txt 文件格式：
    - 包名==版本号
    - 包名>=版本号
    - 包名<=版本号
    - 包名~=版本号
    - -r 其他文件
    - 注释行（# 开头）
    - 空行
    """
    
    def __init__(self):
        """初始化 RequirementsParser"""
        self.logger = logging.getLogger(__name__)
    
    def parse(self, file_path: str) -> List[Dict[str, str]]:
        """
        解析 requirements.txt 文件
        
        参数:
            file_path: 文件路径
            
        返回:
            List[Dict[str, str]]: 依赖列表，每项包含 name 和 version
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        dependencies = []
        
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # 跳过空行和注释
                if not line or line.startswith("#"):
                    continue
                
                # 跳过 -r 包含的其他文件（不递归解析）
                if line.startswith("-r "):
                    self.logger.warning(f"第 {line_num} 行：跳过包含文件 {line[3:]}")
                    continue
                
                # 跳过其他选项标志
                if line.startswith("-"):
                    continue
                
                # 解析依赖
                try:
                    dep = self._parse_line(line)
                    if dep:
                        dependencies.append(dep)
                except Exception as e:
                    self.logger.warning(f"第 {line_num} 行解析失败：{line} - {e}")
        
        return dependencies
    
    def _parse_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        解析单行依赖声明
        
        参数:
            line: 依赖声明行
            
        返回:
            Optional[Dict[str, str]]: 依赖信息字典
        """
        # 移除行尾注释
        if "#" in line:
            line = line.split("#")[0].strip()
        
        # 移除环境变量标记
        line = re.sub(r"\s*;.*$", "", line)
        
        # 尝试使用 packaging 解析
        try:
            req = Requirement(line)
            return {
                "name": req.name,
                "version": str(req.specifier) if req.specifier else "*",
                "full": line
            }
        except InvalidRequirement:
            pass
        
        # 尝试简单格式解析（包名==版本号）
        match = re.match(r"^([a-zA-Z0-9_.-]+)\s*(==|>=|<=|~=|!=|>|<)\s*([a-zA-Z0-9_.!+*-]+)", line)
        if match:
            return {
                "name": match.group(1),
                "version": f"{match.group(2)}{match.group(3)}",
                "full": line
            }
        
        # 仅包名（无版本约束）
        match = re.match(r"^([a-zA-Z0-9_.-]+)$", line)
        if match:
            return {
                "name": match.group(1),
                "version": "*",
                "full": line
            }
        
        self.logger.warning(f"无法解析依赖行：{line}")
        return None
    
    def parse_string(self, content: str) -> List[Dict[str, str]]:
        """
        从字符串解析依赖
        
        参数:
            content: requirements.txt 内容字符串
            
        返回:
            List[Dict[str, str]]: 依赖列表
        """
        dependencies = []
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            try:
                dep = self._parse_line(line)
                if dep:
                    dependencies.append(dep)
            except Exception as e:
                self.logger.warning(f"解析失败：{line} - {e}")
        
        return dependencies
