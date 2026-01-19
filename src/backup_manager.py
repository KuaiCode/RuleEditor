# -*- coding: utf-8 -*-
"""
备份管理器
支持自动备份和手动备份
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from PyQt6.QtCore import QTimer, QObject, pyqtSignal


class BackupManager(QObject):
    """备份管理器"""
    
    backup_created = pyqtSignal(str)  # 备份创建信号
    
    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._timer: Optional[QTimer] = None
        self._current_file: str = ""
        self._backup_dir: Optional[Path] = None
        
    def start_auto_backup(self, file_path: str):
        """启动自动备份"""
        if not self.config_manager:
            return
        
        self._current_file = file_path
        
        # 获取配置
        auto_backup = self.config_manager.get('auto_backup', {})
        if not auto_backup.get('enabled', True):
            return
        
        interval = auto_backup.get('interval_minutes', 5)
        
        # 设置备份目录
        backup_dir = auto_backup.get('backup_dir', 'backups')
        if not os.path.isabs(backup_dir):
            # 相对于配置文件目录
            backup_dir = self.config_manager.config_dir / backup_dir
        self._backup_dir = Path(backup_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 启动定时器
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._do_auto_backup)
        
        self._timer.start(interval * 60 * 1000)  # 转换为毫秒
    
    def stop_auto_backup(self):
        """停止自动备份"""
        if self._timer:
            self._timer.stop()
    
    def _do_auto_backup(self):
        """执行自动备份"""
        if self._current_file and os.path.exists(self._current_file):
            self.create_backup(self._current_file, auto=True)
    
    def create_backup(self, file_path: str, auto: bool = False) -> Optional[str]:
        """
        创建备份
        
        Args:
            file_path: 要备份的文件路径
            auto: 是否为自动备份
            
        Returns:
            备份文件路径，失败返回None
        """
        if not os.path.exists(file_path):
            return None
        
        # 确定备份目录
        if self._backup_dir:
            backup_dir = self._backup_dir
        else:
            backup_dir = Path(file_path).parent / "backups"
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成备份文件名
        original_name = Path(file_path).stem
        ext = Path(file_path).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "auto_" if auto else ""
        
        backup_name = f"{prefix}{original_name}_{timestamp}{ext}"
        backup_path = backup_dir / backup_name
        
        try:
            shutil.copy2(file_path, backup_path)
            self.backup_created.emit(str(backup_path))
            
            # 清理旧备份
            self._cleanup_old_backups(backup_dir, original_name, ext)
            
            return str(backup_path)
        except Exception as e:
            print(f"创建备份失败: {e}")
            return None
    
    def _cleanup_old_backups(self, backup_dir: Path, file_stem: str, ext: str):
        """清理旧的备份文件"""
        if not self.config_manager:
            return
        
        max_backups = self.config_manager.get('auto_backup.max_backups', 10)
        
        # 获取该文件的所有备份
        pattern = f"*{file_stem}_*{ext}"
        backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
        
        # 删除多余的备份
        while len(backups) > max_backups:
            old_backup = backups.pop(0)
            try:
                old_backup.unlink()
            except Exception as e:
                print(f"删除旧备份失败: {e}")
    
    def get_backups(self, file_path: str) -> List[Tuple[str, datetime, int]]:
        """
        获取文件的备份列表
        
        Returns:
            备份列表，每项为 (路径, 时间, 大小)
        """
        backups = []
        
        # 确定备份目录
        if self._backup_dir:
            backup_dir = self._backup_dir
        else:
            backup_dir = Path(file_path).parent / "backups"
        
        if not backup_dir.exists():
            return backups
        
        original_name = Path(file_path).stem
        ext = Path(file_path).suffix
        
        pattern = f"*{original_name}_*{ext}"
        for backup_file in backup_dir.glob(pattern):
            stat = backup_file.stat()
            backups.append((
                str(backup_file),
                datetime.fromtimestamp(stat.st_mtime),
                stat.st_size
            ))
        
        # 按时间倒序排列
        backups.sort(key=lambda x: x[1], reverse=True)
        
        return backups
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """
        恢复备份
        
        Args:
            backup_path: 备份文件路径
            target_path: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            # 先备份当前文件
            if os.path.exists(target_path):
                self.create_backup(target_path, auto=False)
            
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False
    
    def delete_backup(self, backup_path: str) -> bool:
        """删除备份"""
        try:
            os.unlink(backup_path)
            return True
        except Exception as e:
            print(f"删除备份失败: {e}")
            return False
    
    def set_current_file(self, file_path: str):
        """设置当前文件"""
        self._current_file = file_path
