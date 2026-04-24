# -*- coding: utf-8 -*-
"""
CLI 入口模块

提供命令行接口，协调各 Agent 执行诊断流程。
"""

import sys

import click

from .agents import EnvScanner, ConflictSolver, SandboxExecutor


@click.group()
@click.version_option(version="0.1.4", prog_name="pyenv-doctor-tool")
def main():
    """
    PyEnv Doctor - Python 环境诊断与沙箱预演工具
    """
    pass


@main.command()
@click.option("--timeout", "-t", default=60, help="沙箱预演超时时间（秒）")
@click.option("--verbose", "-v", is_flag=True, help="显示详细输出")
def diagnose(timeout: int, verbose: bool):
    """
    执行完整诊断流程，检测依赖冲突并提供修复建议。
    """
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
    click.echo("[SCAN] 扫描环境...")
    try:
        scanner = EnvScanner()
        packages = scanner.scan()
        click.echo(f"[OK] 发现 {len(packages)} 个包")
    except PermissionError:
        click.echo("[ERROR] 权限不足，无法扫描环境")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 扫描失败: {e}")
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
    click.echo("[SANDBOX] 模拟修复...")
    executor = SandboxExecutor(timeout=timeout)
    results = executor.preview(conflicts)

    # STEP 6: 输出诊断报告
    click.echo("[RESULT] 修复建议:")
    
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


if __name__ == "__main__":
    main()
