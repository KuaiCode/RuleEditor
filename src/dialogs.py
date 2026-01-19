# -*- coding: utf-8 -*-
"""
对话框组件
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QListWidget,
    QListWidgetItem, QFileDialog, QProgressDialog, QSpinBox,
    QGroupBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialogButtonBox, QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime


class VersionDialog(QDialog):
    """版本号编辑对话框"""
    
    def __init__(self, current_version: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改版本号")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 版本号输入
        form_layout = QFormLayout()
        self.version_spin = QSpinBox()
        self.version_spin.setRange(1, 99999)
        self.version_spin.setValue(current_version)
        form_layout.addRow("版本号:", self.version_spin)
        layout.addLayout(form_layout)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def get_version(self) -> int:
        return self.version_spin.value()


class ProfileDialog(QDialog):
    """配置文件管理对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("配置文件管理")
        self.setMinimumSize(450, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 配置文件列表
        list_label = QLabel("可用的配置文件:")
        layout.addWidget(list_label)
        
        self.profile_list = QListWidget()
        self.profile_list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self.profile_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("新建配置")
        self.new_btn.clicked.connect(self._new_profile)
        btn_layout.addWidget(self.new_btn)
        
        self.delete_btn = QPushButton("删除配置")
        self.delete_btn.clicked.connect(self._delete_profile)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        self.switch_btn = QPushButton("切换到此配置")
        self.switch_btn.clicked.connect(self._switch_profile)
        self.switch_btn.setEnabled(False)
        btn_layout.addWidget(self.switch_btn)
        
        layout.addLayout(btn_layout)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._refresh_list()
    
    def _refresh_list(self):
        self.profile_list.clear()
        current = self.config_manager.get_current_profile()
        for profile in self.config_manager.get_profiles():
            item = QListWidgetItem(profile)
            if profile == current:
                item.setText(f"{profile} (当前)")
                item.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Bold))
            self.profile_list.addItem(item)
    
    def _on_selection_changed(self, row):
        enabled = row >= 0
        profile = self.profile_list.item(row).text() if enabled else ""
        
        # 不能删除default和当前配置
        is_default = profile.startswith("default")
        is_current = "(当前)" in profile
        
        self.delete_btn.setEnabled(enabled and not is_default and not is_current)
        self.switch_btn.setEnabled(enabled and not is_current)
    
    def _new_profile(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建配置", "配置名称:")
        if ok and name:
            name = name.strip()
            if name and name not in self.config_manager.get_profiles():
                self.config_manager.create_profile(name)
                self._refresh_list()
    
    def _delete_profile(self):
        row = self.profile_list.currentRow()
        if row >= 0:
            profile = self.profile_list.item(row).text().replace(" (当前)", "")
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除配置 \"{profile}\" 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.config_manager.delete_profile(profile)
                self._refresh_list()
    
    def _switch_profile(self):
        row = self.profile_list.currentRow()
        if row >= 0:
            profile = self.profile_list.item(row).text().replace(" (当前)", "")
            self.config_manager.switch_profile(profile)
            self._refresh_list()


class ScanThread(QThread):
    """扫描线程"""
    
    progress = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, scanner, project_path: str):
        super().__init__()
        self.scanner = scanner
        self.project_path = project_path
    
    def run(self):
        try:
            result = self.scanner.scan_project(
                self.project_path,
                lambda c, t, m: self.progress.emit(c, t, m)
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class SpringBootScanDialog(QDialog):
    """SpringBoot项目扫描对话框"""
    
    scan_completed = pyqtSignal(dict)
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._scan_thread: Optional[ScanThread] = None
        
        self.setWindowTitle("SpringBoot项目扫描")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 已扫描的项目
        projects_group = QGroupBox("已扫描的项目")
        projects_layout = QVBoxLayout(projects_group)
        
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(3)
        self.projects_table.setHorizontalHeaderLabels(["项目名称", "路径", "扫描时间"])
        self.projects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.projects_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        projects_layout.addWidget(self.projects_table)
        
        proj_btn_layout = QHBoxLayout()
        self.remove_btn = QPushButton("移除选中项目")
        self.remove_btn.clicked.connect(self._remove_project)
        proj_btn_layout.addWidget(self.remove_btn)
        proj_btn_layout.addStretch()
        projects_layout.addLayout(proj_btn_layout)
        
        layout.addWidget(projects_group)
        
        # 扫描新项目
        scan_group = QGroupBox("扫描新项目")
        scan_layout = QVBoxLayout(scan_group)
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择SpringBoot项目目录...")
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        
        scan_layout.addLayout(path_layout)
        
        # 函数类后缀设置
        suffix_layout = QHBoxLayout()
        suffix_layout.addWidget(QLabel("函数类后缀:"))
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setText(self.config_manager.get_function_classes_suffix())
        self.suffix_edit.setPlaceholderText("例如: Functions")
        suffix_layout.addWidget(self.suffix_edit)
        suffix_layout.addStretch()
        scan_layout.addLayout(suffix_layout)
        
        self.scan_btn = QPushButton("开始扫描")
        self.scan_btn.clicked.connect(self._start_scan)
        scan_layout.addWidget(self.scan_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addWidget(scan_group)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._refresh_projects()
    
    def _refresh_projects(self):
        projects = self.config_manager.get_springboot_projects()
        self.projects_table.setRowCount(len(projects))
        
        for i, proj in enumerate(projects):
            self.projects_table.setItem(i, 0, QTableWidgetItem(proj.get('name', '')))
            self.projects_table.setItem(i, 1, QTableWidgetItem(proj.get('path', '')))
            self.projects_table.setItem(i, 2, QTableWidgetItem(proj.get('scanned_at', '')))
    
    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择SpringBoot项目目录",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.path_edit.setText(path)
    
    def _start_scan(self):
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先选择项目目录")
            return
        
        # 保存函数类后缀设置
        suffix = self.suffix_edit.text().strip()
        if suffix:
            self.config_manager.set_function_classes_suffix(suffix)
        
        # 导入扫描器
        from .springboot_scanner import SpringBootScanner
        
        # 创建进度对话框
        progress = QProgressDialog("正在扫描...", "取消", 0, 100, self)
        progress.setWindowTitle("扫描进度")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        
        # 创建扫描器和线程
        scanner = SpringBootScanner(self.config_manager)
        self._scan_thread = ScanThread(scanner, path)
        
        def on_progress(current, total, msg):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(msg)
        
        def on_finished(result):
            progress.close()
            self._refresh_projects()
            class_count = len(result.get('classes', []))
            QMessageBox.information(
                self, "扫描完成",
                f"扫描完成！\n共发现 {class_count} 个类。"
            )
            self.scan_completed.emit(result)
        
        def on_error(msg):
            progress.close()
            QMessageBox.critical(self, "扫描失败", f"扫描过程中出错:\n{msg}")
        
        self._scan_thread.progress.connect(on_progress)
        self._scan_thread.finished_signal.connect(on_finished)
        self._scan_thread.error.connect(on_error)
        
        self._scan_thread.start()
        self.scan_btn.setEnabled(False)
        
        def on_thread_finished():
            self.scan_btn.setEnabled(True)
        
        self._scan_thread.finished.connect(on_thread_finished)
    
    def _remove_project(self):
        row = self.projects_table.currentRow()
        if row >= 0:
            projects = self.config_manager.get_springboot_projects()
            if row < len(projects):
                path = projects[row].get('path', '')
                self.config_manager.remove_springboot_project(path)
                self._refresh_projects()


class BackupDialog(QDialog):
    """备份管理对话框"""
    
    restore_requested = pyqtSignal(str)
    
    def __init__(self, backup_manager, current_file: str, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.current_file = current_file
        
        self.setWindowTitle("备份管理")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 备份列表
        list_label = QLabel(f"文件 \"{Path(current_file).name}\" 的备份:")
        layout.addWidget(list_label)
        
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["备份时间", "文件大小", "备份文件"])
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.backup_table)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.restore_btn = QPushButton("恢复选中备份")
        self.restore_btn.clicked.connect(self._restore_backup)
        btn_layout.addWidget(self.restore_btn)
        
        self.delete_btn = QPushButton("删除选中备份")
        self.delete_btn.clicked.connect(self._delete_backup)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        self.create_btn = QPushButton("立即创建备份")
        self.create_btn.clicked.connect(self._create_backup)
        btn_layout.addWidget(self.create_btn)
        
        layout.addLayout(btn_layout)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        self._refresh_backups()
    
    def _refresh_backups(self):
        backups = self.backup_manager.get_backups(self.current_file)
        self.backup_table.setRowCount(len(backups))
        
        for i, (path, time, size) in enumerate(backups):
            self.backup_table.setItem(i, 0, QTableWidgetItem(time.strftime("%Y-%m-%d %H:%M:%S")))
            self.backup_table.setItem(i, 1, QTableWidgetItem(f"{size / 1024:.1f} KB"))
            self.backup_table.setItem(i, 2, QTableWidgetItem(Path(path).name))
            self.backup_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, path)
    
    def _get_selected_backup(self) -> Optional[str]:
        row = self.backup_table.currentRow()
        if row >= 0:
            return self.backup_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return None
    
    def _restore_backup(self):
        backup_path = self._get_selected_backup()
        if backup_path:
            reply = QMessageBox.question(
                self, "确认恢复",
                "恢复备份将覆盖当前文件内容。\n当前文件会先自动备份。\n\n确定要恢复吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.backup_manager.restore_backup(backup_path, self.current_file):
                    self.restore_requested.emit(self.current_file)
                    QMessageBox.information(self, "成功", "备份已恢复")
                    self._refresh_backups()
                else:
                    QMessageBox.critical(self, "错误", "恢复备份失败")
    
    def _delete_backup(self):
        backup_path = self._get_selected_backup()
        if backup_path:
            reply = QMessageBox.question(
                self, "确认删除",
                "确定要删除选中的备份吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.backup_manager.delete_backup(backup_path):
                    self._refresh_backups()
    
    def _create_backup(self):
        path = self.backup_manager.create_backup(self.current_file, auto=False)
        if path:
            QMessageBox.information(self, "成功", f"备份已创建:\n{path}")
            self._refresh_backups()
        else:
            QMessageBox.critical(self, "错误", "创建备份失败")


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        self.setWindowTitle("设置")
        self.setMinimumSize(450, 350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 自动备份设置
        backup_group = QGroupBox("自动备份")
        backup_layout = QFormLayout(backup_group)
        
        self.backup_enabled = QCheckBox("启用自动备份")
        self.backup_enabled.setChecked(self.config_manager.get('auto_backup.enabled', True))
        backup_layout.addRow(self.backup_enabled)
        
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 60)
        self.backup_interval.setValue(self.config_manager.get('auto_backup.interval_minutes', 5))
        self.backup_interval.setSuffix(" 分钟")
        backup_layout.addRow("备份间隔:", self.backup_interval)
        
        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 100)
        self.max_backups.setValue(self.config_manager.get('auto_backup.max_backups', 10))
        backup_layout.addRow("最大备份数:", self.max_backups)
        
        layout.addWidget(backup_group)
        
        # 主题设置
        theme_group = QGroupBox("外观")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("跟随系统", "auto")
        self.theme_combo.addItem("浅色", "light")
        self.theme_combo.addItem("深色", "dark")
        
        current_theme = self.config_manager.get('theme', 'auto')
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        
        theme_layout.addRow("主题:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # 函数类设置
        fn_group = QGroupBox("SpringBoot扫描")
        fn_layout = QFormLayout(fn_group)
        
        self.fn_suffix = QLineEdit()
        self.fn_suffix.setText(self.config_manager.get('function_classes_suffix', 'Functions'))
        fn_layout.addRow("函数类后缀:", self.fn_suffix)
        
        layout.addWidget(fn_group)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_settings)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save_settings(self):
        # 保存自动备份设置
        self.config_manager.set('auto_backup.enabled', self.backup_enabled.isChecked())
        self.config_manager.set('auto_backup.interval_minutes', self.backup_interval.value())
        self.config_manager.set('auto_backup.max_backups', self.max_backups.value())
        
        # 保存主题设置
        self.config_manager.set('theme', self.theme_combo.currentData())
        
        # 保存函数类后缀
        self.config_manager.set('function_classes_suffix', self.fn_suffix.text().strip())
        
        self.accept()
    
    def get_theme(self) -> str:
        return self.theme_combo.currentData()
