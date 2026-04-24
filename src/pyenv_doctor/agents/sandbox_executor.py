# -*- coding: utf-8 -*-
"""
SandboxExecutor Agent - 沙箱预演代理

职责: 创建沙箱并预演修复方案

@skill 沙箱预演
"""

import logging
import re
import shutil
import subprocess
import tempfile
import time
import venv
from pathlib import Path
from typing import List, Tuple

from ..models.schemas import Conflict, SandboxResult


class SandboxExecutor:
    """
    沙箱预演 Agent

    创建临时虚拟环境，预演修复方案。

    属性:
        name: Agent 名称，固定值 "SandboxExecutor"
        timeout: 单次安装超时时间（秒）
    """

    name: str = "SandboxExecutor"

    def __init__(self, timeout: int = 60):
        """
        初始化 SandboxExecutor

        参数:
            timeout: 单次安装超时时间（秒）
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def create_sandbox(self) -> Path:
        """
        创建临时沙箱环境

        返回:
            Path: 沙箱环境根目录路径

        异常:
            OSError: venv 创建失败时抛出
        """
        try:
            # 创建临时目录
            sandbox_dir = Path(tempfile.mkdtemp(prefix="pyenv_doctor_"))

            # 创建虚拟环境
            venv.create(sandbox_dir, with_pip=True)

            self.logger.info(f"创建沙箱环境: {sandbox_dir}")
            return sandbox_dir

        except OSError as e:
            self.logger.error(f"创建沙箱失败: {e}")
            raise

    def get_pip_path(self, sandbox_dir: Path) -> Path:
        """
        获取沙箱内 pip 路径

        参数:
            sandbox_dir: 沙箱环境根目录

        返回:
            Path: pip 可执行文件路径

        异常:
            FileNotFoundError: pip 不存在时抛出
        """
        # Windows 平台
        pip_path = sandbox_dir / "Scripts" / "pip.exe"
        if pip_path.exists():
            return pip_path

        # Linux/macOS 平台
        pip_path = sandbox_dir / "bin" / "pip"
        if pip_path.exists():
            return pip_path

        raise FileNotFoundError(f"pip not found in sandbox: {sandbox_dir}")

    def simulate_fix(self, sandbox_dir: Path, suggestion: str) -> Tuple[bool, str]:
        """
        在沙箱中模拟安装

        参数:
            sandbox_dir: 沙箱环境根目录
            suggestion: 修复建议，格式为 包名==版本号

        返回:
            Tuple[bool, str]: (是否成功, 错误信息)
        """
        # 参数白名单验证，防止命令注入
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*==.+$", suggestion):
            return False, f"Invalid suggestion format: {suggestion}"
        
        # 检查是否包含危险字符
        dangerous_chars = [';', '|', '`', '$', '&', ' ']
        if any(char in suggestion for char in dangerous_chars):
            return False, f"Dangerous characters detected in suggestion: {suggestion}"
        
        try:
            pip_path = self.get_pip_path(sandbox_dir)

            # 执行 pip install
            result = subprocess.run(
                [str(pip_path), "install", suggestion, "--quiet"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            success = result.returncode == 0
            error = result.stderr if not success else ""

            return success, error

        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except FileNotFoundError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def preview(self, conflicts: List[Conflict]) -> List[SandboxResult]:
        """
        批量预演修复方案

        参数:
            conflicts: 冲突列表

        返回:
            List[SandboxResult]: 预演结果列表
        """
        # 空列表直接返回
        if not conflicts:
            return []

        results: List[SandboxResult] = []
        sandbox = None

        try:
            # 创建沙箱环境
            sandbox = self.create_sandbox()

            # 遍历冲突，预演修复方案
            for conflict in conflicts:
                suggestion = conflict.suggestion
                success, error = self.simulate_fix(sandbox, suggestion)

                result = SandboxResult(
                    scheme=suggestion,
                    success=success,
                    error=error if not success else None
                )
                results.append(result)

        except Exception as e:
            self.logger.error(f"预演失败: {e}")
            # 为所有冲突返回失败结果
            for conflict in conflicts:
                results.append(SandboxResult(
                    scheme=conflict.suggestion,
                    success=False,
                    error=str(e)
                ))

        finally:
            # 清理沙箱环境
            if sandbox:
                self._cleanup(sandbox)

        return results

    def _cleanup(self, sandbox_dir: Path):
        """
        清理沙箱环境

        参数:
            sandbox_dir: 沙箱环境根目录
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.rmtree(sandbox_dir, ignore_errors=False)
                self.logger.info(f"清理沙箱环境: {sandbox_dir}")
                return
            except Exception as e:
                self.logger.warning(f"清理沙箱失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待 1 秒后重试
        
        self.logger.error(f"清理沙箱最终失败: {sandbox_dir}")
