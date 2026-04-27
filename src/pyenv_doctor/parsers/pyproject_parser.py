# -*- coding: utf-8 -*-
"""
pyproject.toml 解析器

解析 pyproject.toml 文件中的依赖声明
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    import tomllib
except ImportError:
    # Python < 3.11 使用 tomli
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


class PyProjectParser:
    """
    pyproject.toml 解析器
    
    支持解析标准 pyproject.toml 文件中的依赖：
    - [project] dependencies
    - [project.optional-dependencies]
    - [tool.poetry.dependencies]
    """
    
    def __init__(self):
        """初始化 PyProjectParser"""
        self.logger = logging.getLogger(__name__)
        
        if tomllib is None:
            self.logger.warning(
                "tomllib/tomli 未安装，pyproject.toml 解析功能不可用。"
                "请安装：pip install tomli (Python < 3.11)"
            )
    
    def parse(self, file_path: str, include_optional: bool = True) -> List[Dict[str, str]]:
        """
        解析 pyproject.toml 文件
        
        参数:
            file_path: 文件路径
            include_optional: 是否包含可选依赖
            
        返回:
            List[Dict[str, str]]: 依赖列表
        """
        if tomllib is None:
            raise ImportError("tomllib/tomli 未安装")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{file_path}")
        
        with open(path, "rb") as f:
            try:
                data = tomllib.load(f)
            except Exception as e:
                raise ValueError(f"解析 pyproject.toml 失败：{e}")
        
        dependencies = []
        
        # 解析 [project] dependencies
        if "project" in data:
            project = data["project"]
            
            # 标准依赖
            if "dependencies" in project:
                for dep_str in project["dependencies"]:
                    dep = self._parse_dependency(dep_str)
                    if dep:
                        dependencies.append(dep)
            
            # 可选依赖
            if include_optional and "optional-dependencies" in project:
                for group_name, deps in project["optional-dependencies"].items():
                    self.logger.info(f"解析可选依赖组：{group_name}")
                    for dep_str in deps:
                        dep = self._parse_dependency(dep_str)
                        if dep:
                            dep["optional"] = group_name
                            dependencies.append(dep)
        
        # 解析 [tool.poetry.dependencies]
        if "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]
            
            if "dependencies" in poetry:
                for name, version in poetry["dependencies"].items():
                    # 跳过 Python 版本声明
                    if name.lower() == "python":
                        continue
                    
                    dep = {
                        "name": name,
                        "version": self._convert_poetry_version(version),
                        "full": f"{name}{self._convert_poetry_version(version)}"
                    }
                    dependencies.append(dep)
        
        return dependencies
    
    def _parse_dependency(self, dep_str: str) -> Optional[Dict[str, str]]:
        """
        解析单个依赖声明
        
        参数:
            dep_str: 依赖声明字符串
            
        返回:
            Optional[Dict[str, str]]: 依赖信息
        """
        try:
            req = Requirement(dep_str)
            return {
                "name": req.name,
                "version": str(req.specifier) if req.specifier else "*",
                "full": dep_str
            }
        except Exception as e:
            self.logger.warning(f"解析依赖失败：{dep_str} - {e}")
            return None
    
    def _convert_poetry_version(self, version) -> str:
        """
        转换 Poetry 版本格式为标准格式
        
        参数:
            version: Poetry 版本声明（可以是字符串或字典）
            
        返回:
            str: 标准版本约束
        """
        if isinstance(version, str):
            # 简单版本字符串
            if version.startswith("^"):
                # Poetry 的 ^ 操作符
                base_version = version[1:]
                return f">={base_version}"
            elif version.startswith("~"):
                # Poetry 的 ~ 操作符
                base_version = version[1:]
                return f"~={base_version}"
            elif version == "*":
                return "*"
            else:
                return f"=={version}"
        elif isinstance(version, dict):
            # 复杂版本声明
            parts = []
            if "version" in version:
                ver = version["version"]
                if ver.startswith("^"):
                    parts.append(f">={ver[1:]}")
                elif ver.startswith("~"):
                    parts.append(f"~={ver[1:]}")
                else:
                    parts.append(f"=={ver}")
            
            if "markers" in version:
                parts.append(f"; {version['markers']}")
            
            return " ".join(parts) if parts else "*"
        else:
            return "*"


# 需要导入的类
from packaging.requirements import Requirement
