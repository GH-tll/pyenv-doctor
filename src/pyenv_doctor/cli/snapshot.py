# -*- coding: utf-8 -*-
"""
Snapshot CLI 命令组

实现 snapshot 子命令：list, create, rollback, delete, export
"""

import sys
from datetime import datetime
from typing import Optional

import click

from ..snapshot.manager import SnapshotManager, SnapshotError
from ..repair.rollback import RollbackEngine


@click.group()
def snapshot():
    """
    快照管理命令组
    
    管理环境快照，支持创建、列表、回滚、删除、导出等操作。
    """
    pass


@snapshot.command("list")
@click.option("--json", "json_output", is_flag=True, help="JSON 格式输出")
@click.option("--limit", "-n", default=None, type=int, help="限制显示数量")
def list_snapshots(json_output: bool, limit: Optional[int]):
    """
    列出所有快照
    
    显示快照 ID、创建时间、标签、包数量、是否临时快照。
    """
    try:
        manager = SnapshotManager()
        snapshots = manager.list_snapshots(limit=limit)
        
        if not snapshots:
            click.echo("[INFO] 暂无快照")
            click.echo("")
            click.echo("创建第一个快照：pyenv-doctor snapshot create")
            return
        
        if json_output:
            # JSON 格式输出
            import json
            data = [s.to_dict() for s in snapshots]
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            click.echo("")
            # 表头
            click.echo(f"{'ID':<24} {'Time':<19} {'Label':<20} {'Packages':<10} {'Temp'}")
            click.echo("─" * 85)
            
            # 数据行
            for snap in snapshots:
                time_str = snap.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                label = snap.label or "-"
                temp_mark = "Yes" if snap.is_temporary else "No"
                
                click.echo(
                    f"{snap.id:<24} {time_str:<19} {label:<20} {snap.total_packages:<10} {temp_mark}"
                )
            
            click.echo("")
            click.echo(f"共 {len(snapshots)} 个快照")
    
    except SnapshotError as e:
        click.echo(f"[ERROR] 获取快照失败：{e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 未知错误：{e}")
        sys.exit(1)


@snapshot.command("create")
@click.option("--label", "-l", default=None, help="快照标签")
@click.option("--temporary", is_flag=True, help="创建临时快照")
def create_snapshot(label: Optional[str], temporary: bool):
    """
    创建新快照
    
    记录当前环境所有包的版本信息，用于后续回滚。
    """
    try:
        click.echo("[SNAPSHOT] 正在创建快照...")
        
        manager = SnapshotManager()
        snapshot = manager.create(label=label, temporary=temporary, timeout=30)
        
        click.echo(f"[OK] 快照创建成功！")
        click.echo(f"  - ID: {snapshot.id}")
        click.echo(f"  - 时间：{snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        if label:
            click.echo(f"  - 标签：{label}")
        click.echo(f"  - Python 版本：{snapshot.python_version}")
        if snapshot.venv_path:
            click.echo(f"  - 虚拟环境：{snapshot.venv_path}")
        click.echo(f"  - 包数量：{snapshot.total_packages}")
        if temporary:
            click.echo(f"  - 类型：临时快照（自动修复成功后可转为永久）")
        
        click.echo("")
        click.echo("回滚命令：")
        click.echo(f"  pyenv-doctor snapshot rollback {snapshot.id}")
    
    except SnapshotError as e:
        click.echo(f"[ERROR] 创建快照失败：{e}")
        sys.exit(1)
    except PermissionError:
        click.echo("[ERROR] 权限不足，无法读取已安装包列表")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 未知错误：{e}")
        sys.exit(1)


@snapshot.command("rollback")
@click.argument("snapshot_id", required=False)
@click.option("--latest", is_flag=True, help="回滚到最新快照")
@click.option("--dry-run", is_flag=True, help="预览不回滚")
@click.option("--yes", "-y", is_flag=True, help="跳过确认")
@click.option("--verify/--no-verify", default=True, help="回滚后验证（默认开启）")
def rollback_snapshot(
    snapshot_id: Optional[str],
    latest: bool,
    dry_run: bool,
    yes: bool,
    verify: bool
):
    """
    回滚到指定快照
    
    SNAPSHOT_ID: 快照 ID，或使用 --latest 回滚到最新快照
    """
    # 参数验证
    if not snapshot_id and not latest:
        click.echo("[ERROR] 请指定快照 ID 或使用 --latest 参数")
        click.echo("")
        click.echo("示例：")
        click.echo("  pyenv-doctor snapshot rollback 20260424_143022_abc123")
        click.echo("  pyenv-doctor snapshot rollback --latest")
        sys.exit(1)
    
    try:
        manager = SnapshotManager()
        engine = RollbackEngine()
        
        # 确定快照 ID
        if latest:
            snapshot_id = engine.get_latest_snapshot_id()
            if not snapshot_id:
                click.echo("[ERROR] 无可用快照")
                sys.exit(1)
            click.echo(f"[INFO] 使用最新快照：{snapshot_id}")
        
        # 加载快照
        snapshot = manager.get(snapshot_id)
        if not snapshot:
            click.echo(f"[ERROR] 快照不存在：{snapshot_id}")
            sys.exit(1)
        
        # 预览回滚影响
        preview = manager.preview_rollback(snapshot_id)
        
        if dry_run:
            # 仅预览
            click.echo("[DRY-RUN] 回滚预览:")
            click.echo("=" * 60)
            click.echo(f"快照 ID: {snapshot_id}")
            click.echo(f"创建时间：{snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"标签：{snapshot.label or '-'}")
            click.echo(f"包数量：{snapshot.total_packages}")
            click.echo("")
            
            if preview.total_changes == 0:
                click.echo("[INFO] 当前环境已与快照一致，无需回滚")
            else:
                click.echo(f"将恢复以下包 ({preview.total_changes} 个):")
                for change in preview.changes[:20]:  # 最多显示 20 个
                    click.echo(
                        f"  - {change.package_name}: {change.current_version} → {change.target_version}"
                    )
                if preview.total_changes > 20:
                    click.echo(f"  ... 还有 {preview.total_changes - 20} 个包")
            
            click.echo("")
            click.echo("[DRY-RUN] 预览完成，未执行实际回滚")
            return
        
        # 显示预览并确认
        click.echo("[ROLLBACK] 回滚预览:")
        click.echo("=" * 60)
        if preview.total_changes > 0:
            click.echo(f"将恢复 {preview.total_changes} 个包")
            for change in preview.changes[:5]:  # 显示前 5 个
                click.echo(
                    f"  - {change.package_name}: {change.current_version} → {change.target_version}"
                )
            if preview.total_changes > 5:
                click.echo(f"  ... 共 {preview.total_changes} 个包")
        else:
            click.echo("[INFO] 当前环境已与快照一致")
        
        click.echo("")
        
        # 用户确认
        if not yes:
            confirm = click.prompt(
                "[CONFIRM] 是否继续回滚？[y/N]",
                type=str,
                default="N"
            )
            if confirm.lower() != 'y':
                click.echo("[INFO] 已取消回滚")
                return
        
        # 执行回滚
        click.echo("")
        click.echo(f"[ROLLBACK] 正在回滚到 {snapshot_id}...")
        
        # 进度回调
        def progress_callback(current: int, total: int, package_name: str):
            percentage = (current / total) * 100
            bar_length = 30
            filled_length = int(bar_length * current // total)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            click.echo(
                f"\r[ROLLBACK] 进度 [{bar}] {percentage:.1f}% ({current}/{total}) {package_name}",
                nl=False
            )
        
        result = engine.rollback(snapshot_id, verify=verify)
        
        click.echo("")  # 换行
        
        if result.success:
            click.echo(f"[OK] 回滚成功！")
            click.echo(f"  - 恢复包数量：{result.packages_restored}")
            click.echo(f"  - 耗时：{result.duration:.1f}秒")
            click.echo(f"  - 验证：{'通过' if result.verified else '未验证'}")
            click.echo("")
            click.echo("环境已恢复到：")
            click.echo(f"  {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            click.echo("[ERROR] 回滚失败")
            sys.exit(1)
    
    except SnapshotError as e:
        click.echo(f"[ERROR] 回滚失败：{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("")
        click.echo("[INFO] 用户取消回滚")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 未知错误：{e}")
        sys.exit(1)


@snapshot.command("delete")
@click.argument("snapshot_ids", nargs=-1, required=True)
@click.option("--yes", "-y", is_flag=True, help="跳过确认")
def delete_snapshot(snapshot_ids: tuple, yes: bool):
    """
    删除快照
    
    SNAPSHOT_IDS: 一个或多个快照 ID
    """
    try:
        manager = SnapshotManager()
        
        # 验证快照是否存在
        existing_ids = []
        for sid in snapshot_ids:
            snapshot = manager.get(sid)
            if snapshot:
                existing_ids.append(sid)
            else:
                click.echo(f"[WARN] 快照不存在：{sid}")
        
        if not existing_ids:
            click.echo("[INFO] 无有效快照可删除")
            return
        
        # 显示待删除快照
        click.echo("[DELETE] 将删除以下快照:")
        for sid in existing_ids:
            snapshot = manager.get(sid)
            if snapshot:
                time_str = snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                label = snapshot.label or "-"
                click.echo(f"  - {sid} ({time_str}, 标签：{label})")
        
        click.echo("")
        
        # 用户确认
        if not yes:
            confirm = click.prompt(
                f"[CONFIRM] 确认删除 {len(existing_ids)} 个快照？[y/N]",
                type=str,
                default="N"
            )
            if confirm.lower() != 'y':
                click.echo("[INFO] 已取消删除")
                return
        
        # 执行删除
        deleted_count = 0
        for sid in existing_ids:
            try:
                manager.delete(sid)
                deleted_count += 1
            except Exception as e:
                click.echo(f"[WARN] 删除失败 {sid}: {e}")
        
        click.echo(f"[OK] 成功删除 {deleted_count} 个快照")
    
    except SnapshotError as e:
        click.echo(f"[ERROR] 删除失败：{e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 未知错误：{e}")
        sys.exit(1)


@snapshot.command("export")
@click.argument("snapshot_id")
@click.option("--output", "-o", default="requirements.txt", help="输出文件路径（默认：requirements.txt）")
@click.option("--format", "-f", "file_format", default="requirements", 
              type=click.Choice(["requirements", "json"]), 
              help="导出格式（默认：requirements）")
def export_snapshot(snapshot_id: str, output: str, file_format: str):
    """
    导出快照
    
    SNAPSHOT_ID: 快照 ID
    
    导出为 requirements.txt 或 JSON 格式。
    """
    try:
        manager = SnapshotManager()
        
        # 验证快照存在
        snapshot = manager.get(snapshot_id)
        if not snapshot:
            click.echo(f"[ERROR] 快照不存在：{snapshot_id}")
            sys.exit(1)
        
        click.echo(f"[EXPORT] 正在导出快照 {snapshot_id}...")
        
        # 导出
        output_path = manager.export(snapshot_id, output, format=file_format)
        
        click.echo(f"[OK] 导出成功！")
        click.echo(f"  - 输出文件：{output_path}")
        click.echo(f"  - 格式：{file_format}")
        click.echo(f"  - 包数量：{snapshot.total_packages}")
        
        if file_format == "requirements":
            click.echo("")
            click.echo("使用导出的 requirements.txt:")
            click.echo(f"  pip install -r {output_path}")
    
    except SnapshotError as e:
        click.echo(f"[ERROR] 导出失败：{e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 未知错误：{e}")
        sys.exit(1)


@snapshot.command("cleanup")
@click.option("--temporary", is_flag=True, help="仅清理临时快照")
@click.option("--yes", "-y", is_flag=True, help="跳过确认")
def cleanup_snapshots(temporary: bool, yes: bool):
    """
    清理快照
    
    删除临时快照或过期快照。
    """
    try:
        manager = SnapshotManager()
        
        # 获取快照列表
        all_snapshots = manager.list_snapshots()
        
        if temporary:
            # 仅清理临时快照
            to_delete = [s for s in all_snapshots if s.is_temporary]
            click.echo(f"[CLEANUP] 找到 {len(to_delete)} 个临时快照")
        else:
            # 清理所有快照
            to_delete = all_snapshots
            click.echo(f"[CLEANUP] 找到 {len(to_delete)} 个快照")
        
        if not to_delete:
            click.echo("[INFO] 无需清理")
            return
        
        # 显示待删除快照
        click.echo("")
        click.echo("将删除以下快照:")
        for snap in to_delete[:10]:  # 最多显示 10 个
            time_str = snap.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            label = snap.label or "-"
            temp_mark = " (临时)" if snap.is_temporary else ""
            click.echo(f"  - {snap.id} ({time_str}, 标签：{label}){temp_mark}")
        
        if len(to_delete) > 10:
            click.echo(f"  ... 还有 {len(to_delete) - 10} 个")
        
        click.echo("")
        
        # 用户确认
        if not yes:
            confirm = click.prompt(
                f"[CONFIRM] 确认删除 {len(to_delete)} 个快照？[y/N]",
                type=str,
                default="N"
            )
            if confirm.lower() != 'y':
                click.echo("[INFO] 已取消清理")
                return
        
        # 执行删除
        deleted_count = 0
        for snap in to_delete:
            try:
                manager.delete(snap.id)
                deleted_count += 1
            except Exception as e:
                click.echo(f"[WARN] 删除失败 {snap.id}: {e}")
        
        click.echo(f"[OK] 成功删除 {deleted_count} 个快照")
    
    except SnapshotError as e:
        click.echo(f"[ERROR] 清理失败：{e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[ERROR] 未知错误：{e}")
        sys.exit(1)
