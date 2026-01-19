# -*- coding: utf-8 -*-
"""
规则编辑器 - 应用程序入口
"""
import sys
import os

# 确保可以导入src模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.main_window import create_main_window


def main():
    """应用程序入口"""
    # 启用高DPI支持（PyQt6默认启用）
    # 设置高DPI缩放策略
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("规则编辑器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RuleEditor")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = create_main_window()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
