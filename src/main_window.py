# -*- coding: utf-8 -*-
"""
规则编辑器主窗口
"""
import os
import sys
from typing import Optional
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QApplication
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QFont, QCloseEvent

from .config_manager import ConfigManager
from .theme_manager import ThemeManager, setup_app_style
from .rule_editor import RuleEditor
from .backup_manager import BackupManager
from .spel_completer import SpelCompleter
from .update_checker import UpdateChecker, get_app_version, open_release_page
from .dialogs import (
    VersionDialog, ProfileDialog, SpringBootScanDialog,
    BackupDialog, SettingsDialog
)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, config_manager: ConfigManager, theme_manager: ThemeManager):
        super().__init__()
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        
        # 创建组件
        self.backup_manager = BackupManager(config_manager, self)
        self.spel_completer = SpelCompleter(config_manager)
        
        self._current_file: Optional[str] = None
        self._update_checker = None
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._load_window_state()
        
        # 连接信号
        self.rule_editor.file_modified.connect(self._on_file_modified)
        self.backup_manager.backup_created.connect(self._on_backup_created)
        
        # 自动打开上次的文件
        last_file = self.config_manager.get('last_opened_file', '')
        if last_file and os.path.exists(last_file):
            QTimer.singleShot(100, lambda: self._open_file(last_file))
        
        # 启动时自动检查更新（延迟2秒，等界面加载完成）
        QTimer.singleShot(2000, self._auto_check_update)
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("规则编辑器")
        self.setMinimumSize(1000, 700)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 规则编辑器
        self.rule_editor = RuleEditor(self.config_manager)
        self.rule_editor.set_spel_completer(self.spel_completer)
        layout.addWidget(self.rule_editor)
    
    def _setup_menus(self):
        """设置菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_action = QAction("新建(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_file_dialog)
        file_menu.addAction(open_action)
        
        # 最近文件子菜单
        self.recent_menu = file_menu.addMenu("最近打开(&R)")
        self._update_recent_menu()
        
        file_menu.addSeparator()
        
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为(&A)...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)
        
        export_action = QAction("导出(&E)...", self)
        export_action.triggered.connect(self._export_file)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        backup_action = QAction("备份管理(&B)...", self)
        backup_action.triggered.connect(self._show_backup_dialog)
        edit_menu.addAction(backup_action)
        
        create_backup_action = QAction("立即备份(&K)", self)
        create_backup_action.setShortcut(QKeySequence("Ctrl+B"))
        create_backup_action.triggered.connect(self._create_backup)
        edit_menu.addAction(create_backup_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        scan_action = QAction("SpringBoot项目扫描(&S)...", self)
        scan_action.triggered.connect(self._show_scan_dialog)
        tools_menu.addAction(scan_action)
        
        tools_menu.addSeparator()
        
        profile_action = QAction("配置文件管理(&P)...", self)
        profile_action.triggered.connect(self._show_profile_dialog)
        tools_menu.addAction(profile_action)
        
        import_config_action = QAction("导入配置(&I)...", self)
        import_config_action.triggered.connect(self._import_config)
        tools_menu.addAction(import_config_action)
        
        export_config_action = QAction("导出配置(&E)...", self)
        export_config_action.triggered.connect(self._export_config)
        tools_menu.addAction(export_config_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("设置(&O)...", self)
        settings_action.triggered.connect(self._show_settings_dialog)
        tools_menu.addAction(settings_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        theme_menu = view_menu.addMenu("主题(&T)")
        
        auto_theme_action = QAction("跟随系统(&A)", self)
        auto_theme_action.triggered.connect(lambda: self._set_theme("auto"))
        theme_menu.addAction(auto_theme_action)
        
        light_theme_action = QAction("浅色(&L)", self)
        light_theme_action.triggered.connect(lambda: self._set_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("深色(&D)", self)
        dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        check_update_action = QAction("检查更新(&U)...", self)
        check_update_action.triggered.connect(self._check_update)
        help_menu.addAction(check_update_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # 新建
        new_action = QAction("新建", self)
        new_action.setToolTip("新建规则文件 (Ctrl+N)")
        new_action.triggered.connect(self._new_file)
        toolbar.addAction(new_action)
        
        # 打开
        open_action = QAction("打开", self)
        open_action.setToolTip("打开规则文件 (Ctrl+O)")
        open_action.triggered.connect(self._open_file_dialog)
        toolbar.addAction(open_action)
        
        # 保存
        save_action = QAction("保存", self)
        save_action.setToolTip("保存规则文件 (Ctrl+S)")
        save_action.triggered.connect(self._save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 备份
        backup_action = QAction("备份", self)
        backup_action.setToolTip("立即创建备份 (Ctrl+B)")
        backup_action.triggered.connect(self._create_backup)
        toolbar.addAction(backup_action)
        
        toolbar.addSeparator()
        
        # SpringBoot扫描
        scan_action = QAction("扫描项目", self)
        scan_action.setToolTip("扫描SpringBoot项目")
        scan_action.triggered.connect(self._show_scan_dialog)
        toolbar.addAction(scan_action)
    
    def _setup_statusbar(self):
        """设置状态栏"""
        statusbar = self.statusBar()
        
        # 文件状态标签
        self.file_status_label = QLabel("未打开文件")
        statusbar.addWidget(self.file_status_label, 1)
        
        # 版本标签
        self.version_label = QLabel()
        statusbar.addPermanentWidget(self.version_label)
        
        # 配置文件标签
        self.profile_label = QLabel()
        self._update_profile_label()
        statusbar.addPermanentWidget(self.profile_label)
    
    def _load_window_state(self):
        """加载窗口状态"""
        width = self.config_manager.get('window.width', 1400)
        height = self.config_manager.get('window.height', 900)
        maximized = self.config_manager.get('window.maximized', False)
        
        self.resize(width, height)
        if maximized:
            self.showMaximized()
    
    def _save_window_state(self):
        """保存窗口状态"""
        if not self.isMaximized():
            self.config_manager.set('window.width', self.width())
            self.config_manager.set('window.height', self.height())
        self.config_manager.set('window.maximized', self.isMaximized())
    
    def _update_title(self):
        """更新窗口标题"""
        title = "规则编辑器"
        if self._current_file:
            filename = Path(self._current_file).name
            if self.rule_editor.is_modified():
                title = f"*{filename} - {title}"
            else:
                title = f"{filename} - {title}"
        self.setWindowTitle(title)
    
    def _update_status(self):
        """更新状态栏"""
        if self._current_file:
            self.file_status_label.setText(self._current_file)
        else:
            self.file_status_label.setText("未打开文件")
        
        version = self.rule_editor.get_version()
        self.version_label.setText(f"版本: {version}")
    
    def _update_profile_label(self):
        """更新配置文件标签"""
        profile = self.config_manager.get_current_profile()
        self.profile_label.setText(f"配置: {profile}")
    
    def _update_recent_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        recent_files = self.config_manager.get_recent_files()
        
        if not recent_files:
            action = QAction("(无)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
        else:
            for i, file_path in enumerate(recent_files[:10]):
                action = QAction(f"{i + 1}. {Path(file_path).name}", self)
                action.setData(file_path)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, p=file_path: self._open_file(p))
                self.recent_menu.addAction(action)
    
    def _check_save(self) -> bool:
        """检查是否需要保存"""
        if self.rule_editor.is_modified():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("保存更改")
            msg_box.setText("当前文件已修改，是否保存？")
            msg_box.setIcon(QMessageBox.Icon.Question)
            
            save_btn = msg_box.addButton("保存", QMessageBox.ButtonRole.AcceptRole)
            discard_btn = msg_box.addButton("不保存", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(save_btn)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()
            
            if clicked == save_btn:
                return self._save_file()
            elif clicked == cancel_btn:
                return False
        
        return True
    
    def _new_file(self):
        """新建文件"""
        if not self._check_save():
            return
        
        self.rule_editor.new_file()
        self._current_file = None
        self.backup_manager.stop_auto_backup()
        self._update_title()
        self._update_status()
    
    def _open_file_dialog(self):
        """打开文件对话框"""
        if not self._check_save():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开规则文件",
            "",
            "YAML文件 (*.yml *.yaml);;所有文件 (*.*)"
        )
        
        if file_path:
            self._open_file(file_path)
    
    def _open_file(self, file_path: str):
        """打开文件"""
        if not self._check_save():
            return
        
        if self.rule_editor.load_file(file_path):
            self._current_file = file_path
            self.config_manager.add_recent_file(file_path)
            self._update_recent_menu()
            self._update_title()
            self._update_status()
            
            # 启动自动备份
            self.backup_manager.start_auto_backup(file_path)
    
    def _save_file(self) -> bool:
        """保存文件"""
        if not self._current_file:
            return self._save_file_as()
        
        if self.rule_editor.save_file(self._current_file):
            self._update_title()
            return True
        return False
    
    def _save_file_as(self) -> bool:
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存规则文件",
            "",
            "YAML文件 (*.yml);;所有文件 (*.*)"
        )
        
        if file_path:
            if not file_path.endswith(('.yml', '.yaml')):
                file_path += '.yml'
            
            if self.rule_editor.save_file(file_path):
                self._current_file = file_path
                self.config_manager.add_recent_file(file_path)
                self._update_recent_menu()
                self._update_title()
                self._update_status()
                
                # 重新启动自动备份
                self.backup_manager.start_auto_backup(file_path)
                return True
        
        return False
    
    def _export_file(self):
        """导出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出规则文件",
            "",
            "YAML文件 (*.yml);;所有文件 (*.*)"
        )
        
        if file_path:
            if not file_path.endswith(('.yml', '.yaml')):
                file_path += '.yml'
            
            if self.rule_editor.export_file(file_path):
                QMessageBox.information(self, "导出成功", f"文件已导出到:\n{file_path}")
    
    def _create_backup(self):
        """创建备份"""
        if self._current_file:
            path = self.backup_manager.create_backup(self._current_file, auto=False)
            if path:
                self.statusBar().showMessage(f"备份已创建: {path}", 3000)
        else:
            QMessageBox.warning(self, "提示", "请先保存文件")
    
    def _show_backup_dialog(self):
        """显示备份管理对话框"""
        if not self._current_file:
            QMessageBox.warning(self, "提示", "请先打开或保存文件")
            return
        
        dialog = BackupDialog(self.backup_manager, self._current_file, self)
        dialog.restore_requested.connect(self._on_backup_restored)
        dialog.exec()
    
    def _show_scan_dialog(self):
        """显示SpringBoot扫描对话框"""
        dialog = SpringBootScanDialog(self.config_manager, self)
        dialog.scan_completed.connect(self._on_scan_completed)
        dialog.exec()
    
    def _show_profile_dialog(self):
        """显示配置文件管理对话框"""
        dialog = ProfileDialog(self.config_manager, self)
        dialog.exec()
        self._update_profile_label()
        
        # 刷新代码补全
        self.spel_completer.refresh_completions()
        self.rule_editor.refresh_completions()
    
    def _show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            # 应用主题
            new_theme = dialog.get_theme()
            self.theme_manager.apply_theme(QApplication.instance(), new_theme)
            
            # 重新配置自动备份
            if self._current_file:
                self.backup_manager.stop_auto_backup()
                if self.config_manager.get('auto_backup.enabled', True):
                    self.backup_manager.start_auto_backup(self._current_file)
            
            # 刷新代码补全
            self.spel_completer.refresh_completions()
            self.rule_editor.refresh_completions()
    
    def _set_theme(self, theme: str):
        """设置主题"""
        self.theme_manager.apply_theme(QApplication.instance(), theme)
    
    def _show_about(self):
        """显示关于对话框"""
        version = get_app_version()
        QMessageBox.about(
            self, "关于规则编辑器",
            f"<h3>规则编辑器</h3>"
            f"<p>版本 {version}</p>"
            "<p>一个用于编辑结算规则的桌面应用程序。</p>"
            "<p>支持功能:</p>"
            "<ul>"
            "<li>规则文件的创建、编辑和保存</li>"
            "<li>SpEL表达式编辑和代码补全</li>"
            "<li>SpringBoot项目扫描</li>"
            "<li>自动备份和恢复</li>"
            "<li>深浅色主题切换</li>"
            "</ul>"
        )
    
    def _check_update(self):
        """检查更新（手动触发）"""
        self.statusBar().showMessage("正在检查更新...")
        
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.check_finished.connect(self._on_check_finished)
        self._update_checker.start()
    
    def _auto_check_update(self):
        """自动检查更新（静默模式，只在有更新时提示）"""
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.check_finished.connect(self._on_auto_check_finished)
        self._update_checker.start()
    
    def _on_auto_check_finished(self, has_update: bool, message: str):
        """自动检查更新完成（静默模式，不显示无更新提示）"""
        if has_update:
            self.statusBar().showMessage(message, 5000)
        # 无更新时不显示任何提示
    
    def _on_update_available(self, latest_version: str, release_url: str):
        """发现新版本"""
        current_version = get_app_version()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("发现新版本")
        msg_box.setText(f"发现新版本 v{latest_version}\n当前版本: v{current_version}\n\n是否前往下载页面？")
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        yes_btn = msg_box.addButton("前往下载", QMessageBox.ButtonRole.AcceptRole)
        no_btn = msg_box.addButton("稍后再说", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(yes_btn)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == yes_btn:
            open_release_page(release_url)
    
    def _on_check_finished(self, has_update: bool, message: str):
        """检查更新完成"""
        self.statusBar().showMessage(message, 3000)
        if not has_update and "失败" not in message:
            QMessageBox.information(self, "检查更新", message)
    
    def _import_config(self):
        """导入配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置文件",
            "",
            "JSON 文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # 验证配置文件格式
                if not isinstance(imported_config, dict):
                    raise ValueError("无效的配置文件格式")
                
                # 合并配置
                self.config_manager.merge_config(imported_config)
                self.config_manager.save()
                
                # 刷新代码补全
                self.spel_completer.refresh_completions()
                self.rule_editor.refresh_completions()
                
                QMessageBox.information(self, "导入成功", "配置文件已成功导入")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入配置文件失败:\n{e}")
    
    def _export_config(self):
        """导出配置文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置文件",
            "config_export.json",
            "JSON 文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                import json
                config_data = self.config_manager.get_export_config()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "导出成功", f"配置文件已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出配置文件失败:\n{e}")
    
    def _on_file_modified(self):
        """文件修改处理"""
        self._update_title()
    
    def _on_backup_created(self, path: str):
        """备份创建处理"""
        self.statusBar().showMessage(f"自动备份已创建", 2000)
    
    def _on_backup_restored(self, file_path: str):
        """备份恢复处理"""
        self.rule_editor.load_file(file_path)
        self._update_title()
    
    def _on_scan_completed(self, result: dict):
        """扫描完成处理"""
        # 刷新代码补全
        self.spel_completer.refresh_completions()
        self.rule_editor.refresh_completions()
    
    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        if not self._check_save():
            event.ignore()
            return
        
        self._save_window_state()
        self.backup_manager.stop_auto_backup()
        event.accept()


def create_main_window() -> MainWindow:
    """创建主窗口"""
    # 创建配置管理器（不传参数，让它自动检测正确的目录）
    config_manager = ConfigManager()
    
    # 设置主题
    theme_manager = setup_app_style(QApplication.instance(), config_manager)
    
    # 创建主窗口
    window = MainWindow(config_manager, theme_manager)
    
    return window
