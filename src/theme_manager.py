# -*- coding: utf-8 -*-
"""
主题管理器 - 支持Windows深浅色主题和高DPI
"""
import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication, QStyleFactory
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt

try:
    import darkdetect
    HAS_DARKDETECT = True
except ImportError:
    HAS_DARKDETECT = False


class ThemeManager:
    """主题管理器"""
    
    # 现代简约风格的浅色主题
    LIGHT_STYLE = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    
    QWidget {
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 10pt;
    }
    
    QMenuBar {
        background-color: #ffffff;
        border-bottom: 1px solid #e0e0e0;
        padding: 4px;
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }
    
    QMenuBar::item:selected {
        background-color: #e8e8e8;
    }
    
    QMenu {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 8px;
        padding: 4px;
    }
    
    QMenu::item {
        padding: 8px 32px 8px 16px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #0078d4;
        color: white;
    }
    
    QToolBar {
        background-color: #ffffff;
        border: none;
        border-bottom: 1px solid #e0e0e0;
        padding: 4px;
        spacing: 4px;
    }
    
    QToolButton {
        background-color: transparent;
        border: none;
        border-radius: 4px;
        padding: 6px;
    }
    
    QToolButton:hover {
        background-color: #e8e8e8;
    }
    
    QToolButton:pressed {
        background-color: #d0d0d0;
    }
    
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    QPushButton:hover {
        background-color: #106ebe;
    }
    
    QPushButton:pressed {
        background-color: #005a9e;
    }
    
    QPushButton:disabled {
        background-color: #cccccc;
        color: #888888;
    }
    
    QPushButton[flat="true"] {
        background-color: transparent;
        color: #0078d4;
    }
    
    QPushButton[flat="true"]:hover {
        background-color: #e8f4fd;
    }
    
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        padding: 8px;
        selection-background-color: #0078d4;
        selection-color: white;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #0078d4;
        padding: 7px;
    }
    
    QComboBox {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 100px;
    }
    
    QComboBox:focus {
        border: 2px solid #0078d4;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #666666;
        margin-right: 8px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        selection-background-color: #0078d4;
        selection-color: white;
    }
    
    QCheckBox {
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid #999999;
    }
    
    QCheckBox::indicator:checked {
        background-color: #0078d4;
        border-color: #0078d4;
    }
    
    QCheckBox::indicator:hover {
        border-color: #0078d4;
    }
    
    QListWidget, QTreeWidget, QTableWidget {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        outline: none;
    }
    
    QListWidget::item, QTreeWidget::item {
        padding: 8px;
        border-radius: 4px;
    }
    
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: #0078d4;
        color: white;
    }
    
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: #f0f0f0;
    }
    
    QScrollBar:vertical {
        background-color: #f5f5f5;
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }
    
    QScrollBar::handle:vertical {
        background-color: #c0c0c0;
        border-radius: 6px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #a0a0a0;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    
    QScrollBar:horizontal {
        background-color: #f5f5f5;
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #c0c0c0;
        border-radius: 6px;
        min-width: 30px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #a0a0a0;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }
    
    QTabWidget::pane {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #ffffff;
    }
    
    QTabBar::tab {
        background-color: #f0f0f0;
        border: none;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }
    
    QTabBar::tab:selected {
        background-color: #ffffff;
        border-bottom: 2px solid #0078d4;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #e8e8e8;
    }
    
    QGroupBox {
        font-weight: bold;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        background-color: #ffffff;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: #333333;
    }
    
    QSplitter::handle {
        background-color: #e0e0e0;
    }
    
    QSplitter::handle:hover {
        background-color: #0078d4;
    }
    
    QStatusBar {
        background-color: #f5f5f5;
        border-top: 1px solid #e0e0e0;
        color: #666666;
    }
    
    QLabel {
        color: #333333;
    }
    
    QLabel[heading="true"] {
        font-size: 14pt;
        font-weight: bold;
        color: #1a1a1a;
    }
    
    QFrame[frameShape="4"] {
        background-color: #e0e0e0;
        max-height: 1px;
    }
    
    QProgressBar {
        border: none;
        border-radius: 4px;
        background-color: #e0e0e0;
        text-align: center;
    }
    
    QProgressBar::chunk {
        background-color: #0078d4;
        border-radius: 4px;
    }
    
    QSpinBox {
        background-color: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        padding: 6px;
    }
    
    QSpinBox:focus {
        border: 2px solid #0078d4;
    }
    
    QDialog {
        background-color: #f5f5f5;
    }
    """
    
    # 现代简约风格的深色主题
    DARK_STYLE = """
    QMainWindow {
        background-color: #1e1e1e;
    }
    
    QWidget {
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 10pt;
        color: #e0e0e0;
        background-color: #1e1e1e;
    }
    
    QMainWindow, QDialog {
        background-color: #1e1e1e;
    }
    
    QMenuBar {
        background-color: #252526;
        border-bottom: 1px solid #3c3c3c;
        padding: 4px;
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }
    
    QMenuBar::item:selected {
        background-color: #3c3c3c;
    }
    
    QMenu {
        background-color: #2d2d30;
        border: 1px solid #3c3c3c;
        border-radius: 8px;
        padding: 4px;
    }
    
    QMenu::item {
        padding: 8px 32px 8px 16px;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #0078d4;
        color: white;
    }
    
    QToolBar {
        background-color: #252526;
        border: none;
        border-bottom: 1px solid #3c3c3c;
        padding: 4px;
        spacing: 4px;
    }
    
    QToolButton {
        background-color: transparent;
        border: none;
        border-radius: 4px;
        padding: 6px;
        color: #e0e0e0;
    }
    
    QToolButton:hover {
        background-color: #3c3c3c;
    }
    
    QToolButton:pressed {
        background-color: #4c4c4c;
    }
    
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    QPushButton:hover {
        background-color: #1a8fe3;
    }
    
    QPushButton:pressed {
        background-color: #005a9e;
    }
    
    QPushButton:disabled {
        background-color: #4c4c4c;
        color: #888888;
    }
    
    QPushButton[flat="true"] {
        background-color: transparent;
        color: #4fc3f7;
    }
    
    QPushButton[flat="true"]:hover {
        background-color: #2d3b45;
    }
    
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #2d2d30;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
        padding: 8px;
        color: #e0e0e0;
        selection-background-color: #0078d4;
        selection-color: white;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 2px solid #0078d4;
        padding: 7px;
    }
    
    QComboBox {
        background-color: #2d2d30;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 100px;
        color: #e0e0e0;
    }
    
    QComboBox:focus {
        border: 2px solid #0078d4;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #a0a0a0;
        margin-right: 8px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #2d2d30;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
        selection-background-color: #0078d4;
        selection-color: white;
    }
    
    QCheckBox {
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 2px solid #666666;
        background-color: #2d2d30;
    }
    
    QCheckBox::indicator:checked {
        background-color: #0078d4;
        border-color: #0078d4;
    }
    
    QCheckBox::indicator:hover {
        border-color: #0078d4;
    }
    
    QListWidget, QTreeWidget, QTableWidget {
        background-color: #252526;
        border: 1px solid #3c3c3c;
        border-radius: 8px;
        outline: none;
        color: #e0e0e0;
    }
    
    QListWidget::item, QTreeWidget::item {
        padding: 8px;
        border-radius: 4px;
    }
    
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: #0078d4;
        color: white;
    }
    
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: #3c3c3c;
    }
    
    QScrollBar:vertical {
        background-color: #2d2d30;
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }
    
    QScrollBar::handle:vertical {
        background-color: #5a5a5a;
        border-radius: 6px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #7a7a7a;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    
    QScrollBar:horizontal {
        background-color: #2d2d30;
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #5a5a5a;
        border-radius: 6px;
        min-width: 30px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #7a7a7a;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }
    
    QTabWidget::pane {
        border: 1px solid #3c3c3c;
        border-radius: 8px;
        background-color: #252526;
    }
    
    QTabBar::tab {
        background-color: #2d2d30;
        border: none;
        padding: 10px 20px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #a0a0a0;
    }
    
    QTabBar::tab:selected {
        background-color: #252526;
        border-bottom: 2px solid #0078d4;
        color: #e0e0e0;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #3c3c3c;
    }
    
    QGroupBox {
        font-weight: bold;
        border: 1px solid #3c3c3c;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 12px;
        background-color: #252526;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: #e0e0e0;
    }
    
    QSplitter::handle {
        background-color: #3c3c3c;
    }
    
    QSplitter::handle:hover {
        background-color: #0078d4;
    }
    
    QStatusBar {
        background-color: #252526;
        border-top: 1px solid #3c3c3c;
        color: #a0a0a0;
    }
    
    QLabel {
        color: #e0e0e0;
        background-color: transparent;
    }
    
    QLabel[heading="true"] {
        font-size: 14pt;
        font-weight: bold;
        color: #ffffff;
        background-color: transparent;
    }
    
    QScrollArea {
        background-color: transparent;
        border: none;
    }
    
    QScrollArea > QWidget > QWidget {
        background-color: transparent;
    }
    
    QFrame {
        background-color: transparent;
    }
    
    QFrame[frameShape="4"] {
        background-color: #3c3c3c;
        max-height: 1px;
    }
    
    QProgressBar {
        border: none;
        border-radius: 4px;
        background-color: #3c3c3c;
        text-align: center;
        color: #e0e0e0;
    }
    
    QProgressBar::chunk {
        background-color: #0078d4;
        border-radius: 4px;
    }
    
    QSpinBox {
        background-color: #2d2d30;
        border: 1px solid #3c3c3c;
        border-radius: 6px;
        padding: 6px;
        color: #e0e0e0;
    }
    
    QSpinBox:focus {
        border: 2px solid #0078d4;
    }
    
    QDialog {
        background-color: #1e1e1e;
    }
    
    QHeaderView::section {
        background-color: #2d2d30;
        color: #e0e0e0;
        padding: 8px;
        border: none;
        border-bottom: 1px solid #3c3c3c;
    }
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._current_theme = "auto"
        self._is_dark = False
    
    def setup_high_dpi(self):
        """设置高DPI支持"""
        # PyQt6默认启用高DPI支持
        pass
    
    def detect_system_theme(self) -> str:
        """检测系统主题"""
        if HAS_DARKDETECT:
            return "dark" if darkdetect.isDark() else "light"
        return "light"
    
    def apply_theme(self, app: QApplication, theme: str = "auto"):
        """应用主题"""
        self._current_theme = theme
        
        if theme == "auto":
            actual_theme = self.detect_system_theme()
        else:
            actual_theme = theme
        
        self._is_dark = (actual_theme == "dark")
        
        if actual_theme == "dark":
            app.setStyleSheet(self.DARK_STYLE)
        else:
            app.setStyleSheet(self.LIGHT_STYLE)
        
        # 保存主题设置
        if self.config_manager:
            self.config_manager.set('theme', theme)
    
    def get_current_theme(self) -> str:
        """获取当前主题设置"""
        return self._current_theme
    
    def is_dark_theme(self) -> bool:
        """是否为深色主题"""
        return self._is_dark
    
    def toggle_theme(self, app: QApplication):
        """切换主题"""
        if self._current_theme == "auto":
            new_theme = "dark" if not self._is_dark else "light"
        elif self._current_theme == "dark":
            new_theme = "light"
        else:
            new_theme = "dark"
        
        self.apply_theme(app, new_theme)
        return new_theme


def setup_app_style(app: QApplication, config_manager=None) -> ThemeManager:
    """设置应用程序样式"""
    theme_manager = ThemeManager(config_manager)
    theme_manager.setup_high_dpi()
    
    # 从配置中读取主题设置
    theme = "auto"
    if config_manager:
        theme = config_manager.get('theme', 'auto')
    
    theme_manager.apply_theme(app, theme)
    
    return theme_manager
