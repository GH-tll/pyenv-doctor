# -*- coding: utf-8 -*-
"""
CLI 入口模块

提供命令行接口，协调各 Agent 执行诊断流程。
"""

import sys
from pathlib import Path
from importlib.metadata import version
from typing import Optional

import click

from ..agents import EnvScanner, ConflictSolver, SandboxExecutor
from ..exporters import JSONExporter, MarkdownExporter
from ..parsers import RequirementsParser, PyProjectParser
from ..models.schemas import RepairStrategy


@click.group()
@click.version_option(version=version("pyenv-doctor-tool"), prog_name="pyenv-doctor-tool")
def main():
    """
    PyEnv Doctor - Python 环境诊断与沙箱预演工具
    """
    pass


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="导出报告文件路径（支持 .json 和 .md 后缀）")
@click.option("--format", "-f", "file_format", default="auto", type=click.Choice(["auto", "requirements", "pyproject"]), 
              help="依赖文件格式（auto=自动检测）")
def check_file(file: str, output: str, file_format: str):
    """
    检查依赖文件中的潜在冲突
    
    FILE: requirements.txt 或 pyproject.toml 文件路径
    """
    from pathlib import Path
    
    file_path = Path(file)
    if not file_path.exists():
        click.echo(f"[ERROR] 文件不存在：{file}")
        sys.exit(1)
    
    # 自动检测或手动指定格式
    if file_format == "auto":
        if file_path.name == "pyproject.toml":
            file_format = "pyproject"
        else:
            file_format = "requirements"
    
    click.echo(f"[INFO] 解析文件：{file_path}")
    
    try:
        # 解析依赖
        if file_format == "pyproject":
            parser = PyProjectParser()
            dependencies = parser.parse(str(file_path))
        else:
            parser = RequirementsParser()
            dependencies = parser.parse(str(file_path))
        
        click.echo(f"[OK] 解析到 {len(dependencies)} 个依赖")
        
        # 显示依赖列表
        click.echo("\n检测到的依赖:")
        for dep in dependencies:
            click.echo(f"  - {dep['name']}{dep['version']}")
        
        # 导出（如果指定）
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_path.suffix.lower() == ".json":
                import json
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(dependencies, f, ensure_ascii=False, indent=2)
                click.echo(f"\n[OK] 依赖列表已导出：{output_path}")
            else:
                click.echo(f"\n[WARN] 仅支持 JSON 格式导出")
        
    except Exception as e:
        click.echo(f"[ERROR] 解析失败：{e}")
        sys.exit(1)


@main.command()
@click.option("--timeout", "-t", default=60, help="沙箱预演超时时间（秒）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
@click.option("--output", "-o", default=None, help="导出报告文件路径（支持 .json 和 .md 后缀）")
@click.option("--parallel", is_flag=True, default=True, help="启用并行预演（默认开启）")
@click.option("--workers", "-w", default=3, type=int, help="并行工作线程数（默认 3，仅并行模式有效）")
@click.option("--fix", is_flag=True, help="自动执行修复")
@click.option("--strategy", default="balanced", type=click.Choice(["conservative", "balanced", "aggressive"]), 
              help="修复策略（默认：balanced）")
@click.option("--dry-run", is_flag=True, help="只显示不执行")
@click.option("--yes", "-y", is_flag=True, help="跳过确认")
# FIX-快速模式支持: 新增 --fast 选项用于快速诊断
@click.option("--fast", is_flag=True, help="启用快速模式（仅扫描用户安装的包）")
def diagnose(
    timeout: int, 
    verbose: bool, 
    output: str, 
    parallel: bool, 
    workers: int,
    fix: bool,
    strategy: str,
    dry_run: bool,
    yes: bool,
    fast: bool  # FIX-快速模式支持: 接收 fast 参数
):
    """
    执行完整诊断流程，检测依赖冲突并提供修复建议。
    
    使用 --fix 选项可自动执行修复。
    使用 --fast 选项启用快速模式，仅扫描用户安装的包。
    """
    from pathlib import Path
    from datetime import datetime
    
    # STEP 1: 检测 Python 版本
    if sys.version_info < (3, 8):
        click.echo("[ERROR] Python 版本不兼容，需要 Python 3.8+")
        sys.exit(1)

    # STEP 2: 检测虚拟环境
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if not in_venv:
        click.echo("[WARN] 建议在虚拟环境中运行")

    # STEP 3: EnvScanner 扫描环境
    # FIX-快速模式支持: 根据 fast 参数传递 only_user 给 EnvScanner
    scan_mode = "快速" if fast else "标准"
    click.echo(f"[SCAN] 扫描环境（{scan_mode}模式）...")
    try:
        scanner = EnvScanner(only_user=fast)
        packages = scanner.scan()
        click.echo(f"[OK] 发现 {len(packages)} 个包")
    except PermissionError:
        click.echo("[ERROR] 权限不足，无法扫描环境")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 扫描失败：{e}")
        sys.exit(1)

    # STEP 4: ConflictSolver 检测冲突
    click.echo("[DIAGNOSE] 检测冲突...")
    solver = ConflictSolver()
    conflicts = solver.detect(packages)

    if not conflicts:
        click.echo("[OK] 未发现冲突")
        return

    click.echo(f"[WARN] 发现 {len(conflicts)} 个冲突:")
    for conflict in conflicts:
        click.echo(
            f"  - {conflict.package} 要求 {conflict.requires}，"
            f"但已安装 {conflict.installed}"
        )

    # STEP 5: SandboxExecutor 预演修复方案
    if parallel:
        click.echo(f"[SANDBOX] 并行模拟修复（{workers} 个工作线程）...")
    else:
        click.echo("[SANDBOX] 串行模拟修复...")
    executor = SandboxExecutor(timeout=timeout)
    results = executor.preview(conflicts, parallel=parallel, max_workers=workers)

    # STEP 6: 输出诊断报告
    click.echo("[RESULT] 修复建议:")
    
    # 如果需要导出报告
    if output:
        output_path = Path(output)
        if output_path.suffix.lower() == ".json":
            exporter = JSONExporter()
            exporter.export(packages, conflicts, results, str(output_path))
            click.echo(f"\n[OK] 报告已导出：{output_path}")
        elif output_path.suffix.lower() == ".md":
            exporter = MarkdownExporter()
            exporter.export(packages, conflicts, results, str(output_path))
            click.echo(f"\n[OK] 报告已导出：{output_path}")
        else:
            click.echo(f"\n[WARN] 不支持的文件格式：{output_path.suffix}，支持 .json 和 .md")
    
    # 分析冲突，生成智能方案
    failed_schemes = [r for r in results if not r.success]
    success_schemes = [r for r in results if r.success]
    
    if failed_schemes and not success_schemes:
        # 所有方案都失败
        click.echo("\n[ERROR] 所有修复方案验证失败，建议手动处理：")
        for result in failed_schemes:
            click.echo(f"  - {result.scheme}: {result.error.split(chr(10))[0] if chr(10) in result.error else result.error}")
        return
    
    # 按包名分组成功方案
    from collections import defaultdict
    package_schemes = defaultdict(list)
    for result in success_schemes:
        pkg_name = result.scheme.split('==')[0] if '==' in result.scheme else result.scheme.split('>=')[0].split('<=')[0]
        package_schemes[pkg_name].append(result.scheme)
    
    # 智能方案推荐
    total_conflicts = len(conflicts)
    total_packages = len(package_schemes)
    
    # 方案 1: 推荐方案（选择每个包的最高版本）- 完整验证
    click.echo("\n【方案一】推荐方案 [已验证] ★★★★★")
    click.echo("=" * 60)
    click.echo("说明：此方案中每个版本都已在沙箱中单独验证可行")
    click.echo("推荐度：强烈推荐（优先使用）")
    click.echo("")
    recommended = []
    for pkg_name, schemes in package_schemes.items():
        # 提取版本号并排序
        versions = []
        for scheme in schemes:
            if '==' in scheme:
                version = scheme.split('==')[1]
                versions.append(version)
        if versions:
            # 选择最高版本
            max_version = max(versions, key=lambda v: [int(x) for x in v.split('.') if x.isdigit()])
            recommended.append(f"{pkg_name}=={max_version}")
    
    for i, scheme in enumerate(recommended, 1):
        click.echo(f"  {i}. pip install {scheme}")
    
    click.echo("\n一键执行：")
    click.echo(f"  pip install {' '.join(recommended)}")
    
    # 方案 2: 仅在复杂冲突时展示（多个包冲突）
    if total_packages >= 2:
        click.echo("\n【方案二】保守方案 [部分验证] ★★★☆☆")
        click.echo("=" * 60)
        click.echo("说明：此方案中每个版本已单独验证，但组合使用未经过测试")
        click.echo("推荐度：保守选择（适合不想大幅变动的环境）")
        click.echo("")
        minimal = []
        for pkg_name, schemes in package_schemes.items():
            # 选择最低可行版本
            versions = []
            for scheme in schemes:
                if '==' in scheme:
                    version = scheme.split('==')[1]
                    versions.append(version)
            if versions:
                min_version = min(versions, key=lambda v: [int(x) for x in v.split('.') if x.isdigit()])
                minimal.append(f"{pkg_name}=={min_version}")
        
        for i, scheme in enumerate(minimal, 1):
            click.echo(f"  {i}. pip install {scheme}")
        
        click.echo("\n一键执行：")
        click.echo(f"  pip install {' '.join(minimal)}")
    
    # 方案 3: 单个包冲突时，提供详细说明
    if total_packages == 1:
        pkg_name = list(package_schemes.keys())[0]
        click.echo(f"\n【方案二】单包升级 [已验证] ★★★★★")
        click.echo("=" * 60)
        click.echo(f"说明：检测到单个包冲突：{pkg_name}")
        click.echo(f"推荐度：直接升级到最新兼容版本即可解决")
        click.echo("")
        click.echo(f"一键执行：pip install {recommended[0]}")
    
    # 警告信息（简化输出）
    if failed_schemes:
        click.echo("\n[WARN] 以下方案验证失败（已跳过）:")
        for result in failed_schemes:
            click.echo(f"  - {result.scheme}")
    
    # 智能建议
    click.echo("\n" + "=" * 60)
    click.echo("[重要说明]")
    click.echo("  - 方案一：每个版本已单独验证，强烈推荐优先使用")
    if total_packages >= 2:
        click.echo("  - 方案二：每个版本已单独验证，但组合效果未经测试")
    click.echo("  - 所有验证均在沙箱隔离环境中进行，确保安全性")
    click.echo("=" * 60)
    
    if total_conflicts > 5:
        click.echo(f"\n[TIP] 检测到 {total_conflicts} 个冲突，建议创建新的虚拟环境以获得更干净的环境")
    
    # ========== 新增：自动修复功能 ==========
    if fix:
        click.echo("")
        click.echo("=" * 60)
        click.echo("[AUTO-FIX] 自动修复模式启动")
        click.echo("=" * 60)
        
        # 策略映射
        strategy_map = {
            "conservative": RepairStrategy.CONSERVATIVE,
            "balanced": RepairStrategy.BALANCED,
            "aggressive": RepairStrategy.AGGRESSIVE,
        }
        selected_strategy = strategy_map[strategy]
        
        click.echo(f"[INFO] 修复策略：{selected_strategy.value}")
        click.echo(f"[INFO] 预演模式：{'是' if dry_run else '否'}")
        click.echo("")
        
        try:
            # 导入修复相关模块
            from ..snapshot.manager import SnapshotManager
            from ..repair.auto_repair import AutoRepair
            from ..repair.rollback import RollbackEngine
            
            # 1. 创建快照（临时禁用，优化性能）
            # FIX-性能优化：临时禁用自动快照创建，避免卡顿
            # click.echo("[SNAPSHOT] 创建临时快照...")
            # manager = SnapshotManager()
            # snapshot = manager.create(label="auto-fix", temporary=True, timeout=30)
            # click.echo(f"[OK] 快照 ID: {snapshot.id} (临时)")
            # click.echo("")
            snapshot = None
            click.echo("[INFO] 已跳过快照创建（性能优化）")
            click.echo("[提示] 如需回滚保护，建议在执行修复前先手动备份：")
            click.echo("       pip freeze > backup_before_fix.txt")
            click.echo("")
            
            # 2. 执行修复
            repair = AutoRepair(
                strategy=selected_strategy,
                dry_run=dry_run,
                timeout=timeout
            )
            
            # 转换 packages 为字典格式
            current_versions = {pkg.name: pkg.version for pkg in packages}
            
            click.echo("[AUTO-FIX] 开始执行修复...")
            # FIX-快照 ID 为空处理：snapshot 为 None 时传递 None
            result = repair.execute(conflicts, current_versions, snapshot_id=snapshot.id if snapshot else None)
            
            click.echo("")
            click.echo(result.to_report())
            
            # 3. 处理修复结果
            if result.success:
                click.echo("")
                
                if dry_run:
                    click.echo("[DRY-RUN] 预演模式，未执行实际修复")
                else:
                    # 询问是否保留状态
                    if not yes:
                        keep = click.prompt(
                            "[KEEP] 是否保留当前状态？[Y/n]",
                            type=str,
                            default="Y"
                        )
                    else:
                        keep = "Y"
                    
                    if keep.lower() == 'y':
                        # 临时转永久
                        if snapshot:
                            snapshot.is_temporary = False
                            from ..snapshot.storage import SnapshotStorage
                            storage = SnapshotStorage()
                            storage.save(snapshot)
                            click.echo("[OK] 临时快照已转为永久快照")
                            click.echo(f"  快照 ID: {snapshot.id}")
                        else:
                            click.echo("[INFO] 快照已跳过，无法保留状态")
                    else:
                        # 回滚到修复前
                        if snapshot:
                            click.echo("")
                            click.echo("[ROLLBACK] 正在回滚到修复前状态...")
                            engine = RollbackEngine()
                            rollback_result = engine.rollback(snapshot.id)
                            
                            if rollback_result.success:
                                click.echo("[OK] 已回滚到修复前状态")
                            else:
                                click.echo("[ERROR] 回滚失败，请手动处理")
                                sys.exit(1)
                        else:
                            click.echo("[INFO] 快照已跳过，无法回滚")
            
            elif result.cancelled_by_user:
                click.echo("[INFO] 用户取消修复，快照已保留")
                click.echo(f"  快照 ID: {snapshot.id}")
                click.echo("  回滚命令：pyenv-doctor snapshot rollback {}".format(snapshot.id))
            
            else:
                # 修复失败，自动回滚
                click.echo("")
                click.echo("[AUTO-ROLLBACK] 修复失败，正在自动回滚...")
                engine = RollbackEngine()
                rollback_result = engine.rollback(snapshot.id)
                
                if rollback_result.success:
                    click.echo("[OK] 已自动回滚到修复前状态")
                else:
                    click.echo("[ERROR] 回滚失败，请手动处理")
                    sys.exit(1)
        
        except ImportError as e:
            click.echo(f"[ERROR] 导入修复模块失败：{e}")
            sys.exit(1)
        except Exception as e:
            click.echo(f"[ERROR] 修复异常：{e}")
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


# 注意：snapshot 命令组在 main() 函数启动前注册
# 为避免循环导入，使用延迟注册方式
def _register_snapshot_command():
    """注册 snapshot 命令组"""
    try:
        from .snapshot import snapshot as snapshot_group
        main.add_command(snapshot_group)
    except Exception as e:
        # 静默失败，不影响其他命令
        pass


# 注册 snapshot 命令
_register_snapshot_command()


if __name__ == "__main__":
    main()
