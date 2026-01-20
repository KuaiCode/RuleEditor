# -*- coding: utf-8 -*-
"""
规则编辑器组件
"""
import yaml
from typing import Optional, List, Dict, Any
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QFrame, QMessageBox, QFileDialog, QScrollArea,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from .models import Rule, RuleFile, Severity
from .spel_completer import SpelCompleter, SpelTextEdit


class SeverityBadge(QLabel):
    """严重程度徽章"""
    
    COLORS = {
        Severity.LOW: ("#4caf50", "#e8f5e9"),      # 绿色
        Severity.MEDIUM: ("#ff9800", "#fff3e0"),   # 橙色
        Severity.HIGH: ("#f44336", "#ffebee"),     # 红色
        Severity.CRITICAL: ("#9c27b0", "#f3e5f5")  # 紫色
    }
    
    def __init__(self, severity: Severity = Severity.MEDIUM, parent=None):
        super().__init__(parent)
        self.set_severity(severity)
    
    def set_severity(self, severity: Severity):
        """设置严重程度"""
        text_color, bg_color = self.COLORS.get(severity, self.COLORS[Severity.MEDIUM])
        self.setText(severity.value)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }}
        """)


class RuleListItem(QWidget):
    """规则列表项"""
    
    def __init__(self, rule: Rule, parent=None):
        super().__init__(parent)
        self.rule = rule
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # 设置最小高度确保内容完整显示
        self.setMinimumHeight(60)
        
        # 启用状态指示器
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.update_status()
        layout.addWidget(self.status_indicator)
        
        # 规则信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 规则名称
        self.name_label = QLabel(self.rule.name or self.rule.code)
        self.name_label.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.Medium))
        info_layout.addWidget(self.name_label)
        
        # 规则编号
        self.code_label = QLabel(self.rule.code)
        self.code_label.setStyleSheet("color: #888888; font-size: 9pt;")
        info_layout.addWidget(self.code_label)
        
        layout.addLayout(info_layout, 1)
        
        # 严重程度徽章
        self.severity_badge = SeverityBadge(self.rule.severity)
        layout.addWidget(self.severity_badge)
    
    def update_status(self):
        """更新状态指示器"""
        if self.rule.enabled:
            self.status_indicator.setStyleSheet("""
                QLabel {
                    background-color: #4caf50;
                    border-radius: 6px;
                }
            """)
        else:
            self.status_indicator.setStyleSheet("""
                QLabel {
                    background-color: #9e9e9e;
                    border-radius: 6px;
                }
            """)
    
    def update_display(self):
        """更新显示"""
        self.name_label.setText(self.rule.name or self.rule.code)
        self.code_label.setText(self.rule.code)
        self.severity_badge.set_severity(self.rule.severity)
        self.update_status()


class RuleEditPanel(QWidget):
    """规则编辑面板"""
    
    rule_changed = pyqtSignal()
    
    def __init__(self, spel_completer: SpelCompleter = None, parent=None):
        super().__init__(parent)
        self.spel_completer = spel_completer
        self._current_rule: Optional[Rule] = None
        self._setup_ui()
        
        # 设置背景透明，让主题样式生效
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel("规则详情")
        title_label.setProperty("heading", True)
        title_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_widget = QWidget()
        scroll_widget.setObjectName("scrollWidget")
        scroll_widget.setStyleSheet("#scrollWidget { background: transparent; }")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)
        basic_layout.setContentsMargins(16, 16, 16, 16)
        
        # 规则编号
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("例如: RULE_001")
        self.code_edit.textChanged.connect(self._on_field_changed)
        basic_layout.addRow("规则编号:", self.code_edit)
        
        # 规则名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("规则的简短描述")
        self.name_edit.textChanged.connect(self._on_field_changed)
        basic_layout.addRow("规则名称:", self.name_edit)
        
        # 启用状态
        status_layout = QHBoxLayout()
        self.enabled_check = QCheckBox("启用此规则")
        self.enabled_check.stateChanged.connect(self._on_field_changed)
        status_layout.addWidget(self.enabled_check)
        status_layout.addStretch()
        basic_layout.addRow("状态:", status_layout)
        
        # 严重程度
        severity_layout = QHBoxLayout()
        self.severity_combo = QComboBox()
        self.severity_combo.addItem("低 (LOW)", Severity.LOW)
        self.severity_combo.addItem("中 (MEDIUM)", Severity.MEDIUM)
        self.severity_combo.addItem("高 (HIGH)", Severity.HIGH)
        self.severity_combo.addItem("严重 (CRITICAL)", Severity.CRITICAL)
        self.severity_combo.currentIndexChanged.connect(self._on_field_changed)
        self.severity_combo.setMinimumWidth(180)
        severity_layout.addWidget(self.severity_combo)
        severity_layout.addStretch()
        basic_layout.addRow("严重程度:", severity_layout)
        
        scroll_layout.addWidget(basic_group)
        
        # 规则表达式组
        expr_group = QGroupBox("规则表达式 (SpEL)")
        expr_layout = QVBoxLayout(expr_group)
        expr_layout.setSpacing(8)
        expr_layout.setContentsMargins(16, 16, 16, 16)
        
        self.expression_edit = SpelTextEdit(self, self.spel_completer)
        self.expression_edit.setPlaceholderText('使用 SpEL 编写规则条件，例如: baseInfo.idNumber == NULL，支持代码补全 (Alt+/)')
        self.expression_edit.setMinimumHeight(80)
        self.expression_edit.setMaximumHeight(120)
        self.expression_edit.textChanged.connect(self._on_field_changed)
        expr_layout.addWidget(self.expression_edit)
        
        scroll_layout.addWidget(expr_group)
        
        # 消息模板组
        msg_group = QGroupBox("提示消息模板")
        msg_layout = QVBoxLayout(msg_group)
        msg_layout.setSpacing(8)
        msg_layout.setContentsMargins(16, 16, 16, 16)
        
        self.message_edit = SpelTextEdit(self, self.spel_completer)
        self.message_edit.setPlaceholderText('支持使用 #{expression} 插入动态内容，例如: #{hospitalizationInfo.stayDays}')
        self.message_edit.setMinimumHeight(60)
        self.message_edit.setMaximumHeight(100)
        self.message_edit.textChanged.connect(self._on_field_changed)
        msg_layout.addWidget(self.message_edit)
        
        scroll_layout.addWidget(msg_group)
        
        # 添加弹性空间
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)
        
        # 初始状态
        self.setEnabled(False)
    
    def set_spel_completer(self, completer: SpelCompleter):
        """设置SpEL补全器"""
        self.spel_completer = completer
        self.expression_edit.set_spel_completer(completer)
        self.message_edit.set_spel_completer(completer)
    
    def load_rule(self, rule: Rule):
        """加载规则到编辑面板"""
        self._current_rule = rule
        self.setEnabled(True)
        
        # 暂时断开信号
        self.code_edit.blockSignals(True)
        self.name_edit.blockSignals(True)
        self.enabled_check.blockSignals(True)
        self.severity_combo.blockSignals(True)
        self.expression_edit.blockSignals(True)
        self.message_edit.blockSignals(True)
        
        # 加载数据
        self.code_edit.setText(rule.code)
        self.name_edit.setText(rule.name)
        self.enabled_check.setChecked(rule.enabled)
        
        # 设置严重程度
        for i in range(self.severity_combo.count()):
            if self.severity_combo.itemData(i) == rule.severity:
                self.severity_combo.setCurrentIndex(i)
                break
        
        self.expression_edit.setPlainText(rule.get_expression())
        self.message_edit.setPlainText(rule.get_message())
        
        # 恢复信号
        self.code_edit.blockSignals(False)
        self.name_edit.blockSignals(False)
        self.enabled_check.blockSignals(False)
        self.severity_combo.blockSignals(False)
        self.expression_edit.blockSignals(False)
        self.message_edit.blockSignals(False)
    
    def save_to_rule(self) -> Optional[Rule]:
        """保存编辑面板数据到规则"""
        if not self._current_rule:
            return None
        
        self._current_rule.code = self.code_edit.text().strip()
        self._current_rule.name = self.name_edit.text().strip()
        self._current_rule.enabled = self.enabled_check.isChecked()
        self._current_rule.severity = self.severity_combo.currentData()
        self._current_rule.set_expression(self.expression_edit.toPlainText())
        self._current_rule.set_message(self.message_edit.toPlainText())
        
        return self._current_rule
    
    def clear(self):
        """清空编辑面板"""
        self._current_rule = None
        self.setEnabled(False)
        
        self.code_edit.clear()
        self.name_edit.clear()
        self.enabled_check.setChecked(True)
        self.severity_combo.setCurrentIndex(1)  # MEDIUM
        self.expression_edit.clear()
        self.message_edit.clear()
    
    def _on_field_changed(self):
        """字段变化处理"""
        if self._current_rule:
            self.save_to_rule()
            self.rule_changed.emit()


class RuleEditor(QWidget):
    """规则编辑器主组件"""
    
    file_modified = pyqtSignal()
    
    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.spel_completer = SpelCompleter(config_manager)
        self._rule_file: Optional[RuleFile] = None
        self._is_modified = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：规则列表
        list_panel = QWidget()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(16, 16, 8, 16)
        list_layout.setSpacing(12)
        
        # 列表标题、版本号和操作按钮
        list_header = QHBoxLayout()
        list_title = QLabel("规则列表")
        list_title.setProperty("heading", True)
        list_title.setFont(QFont("Microsoft YaHei UI", 14, QFont.Weight.Bold))
        list_header.addWidget(list_title)
        
        # 版本号编辑区域
        version_label = QLabel("版本:")
        version_label.setStyleSheet("color: #666666; font-size: 9pt;")
        list_header.addWidget(version_label)
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("1")
        self.version_edit.setFixedWidth(50)
        self.version_edit.setText("1")
        self.version_edit.textChanged.connect(self._on_version_changed)
        list_header.addWidget(self.version_edit)
        
        list_header.addStretch()
        
        # 添加规则按钮
        self.add_btn = QPushButton("+ 添加规则")
        self.add_btn.clicked.connect(self._add_rule)
        list_header.addWidget(self.add_btn)
        
        list_layout.addLayout(list_header)
        
        # 规则列表
        self.rule_list = QListWidget()
        self.rule_list.setSpacing(4)
        self.rule_list.currentRowChanged.connect(self._on_rule_selected)
        list_layout.addWidget(self.rule_list)
        
        # 删除规则按钮
        delete_layout = QHBoxLayout()
        delete_layout.addStretch()
        self.delete_btn = QPushButton("删除选中规则")
        self.delete_btn.setProperty("flat", True)
        self.delete_btn.clicked.connect(self._delete_rule)
        self.delete_btn.setEnabled(False)
        delete_layout.addWidget(self.delete_btn)
        list_layout.addLayout(delete_layout)
        
        # 右侧：编辑面板
        self.edit_panel = RuleEditPanel(self.spel_completer)
        self.edit_panel.rule_changed.connect(self._on_rule_changed)
        
        # 添加到分割器
        splitter.addWidget(list_panel)
        splitter.addWidget(self.edit_panel)
        splitter.setSizes([350, 650])
        
        layout.addWidget(splitter)
    
    def set_spel_completer(self, completer: SpelCompleter):
        """设置SpEL补全器"""
        self.spel_completer = completer
        self.edit_panel.set_spel_completer(completer)
    
    def refresh_completions(self):
        """刷新代码补全"""
        self.spel_completer.refresh_completions()
    
    def new_file(self) -> RuleFile:
        """创建新规则文件"""
        self._rule_file = RuleFile()
        self._is_modified = False
        self._refresh_list()
        self._update_version_display()
        self.edit_panel.clear()
        return self._rule_file
    
    def load_file(self, file_path: str) -> bool:
        """加载规则文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            self._rule_file = RuleFile.from_dict(data, file_path)
            self._is_modified = False
            self._refresh_list()
            self._update_version_display()
            
            # 选中第一条规则
            if self._rule_file.rules:
                self.rule_list.setCurrentRow(0)
            else:
                self.edit_panel.clear()
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件失败:\n{e}")
            return False
    
    def save_file(self, file_path: str = None) -> bool:
        """保存规则文件"""
        if not self._rule_file:
            return False
        
        if file_path:
            self._rule_file.file_path = file_path
        
        if not self._rule_file.file_path:
            return False
        
        try:
            data = self._rule_file.to_dict()
            with open(self._rule_file.file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            self._is_modified = False
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败:\n{e}")
            return False
    
    def export_file(self, file_path: str) -> bool:
        """导出规则文件"""
        return self.save_file(file_path)
    
    def is_modified(self) -> bool:
        """是否已修改"""
        return self._is_modified
    
    def get_rule_file(self) -> Optional[RuleFile]:
        """获取当前规则文件"""
        return self._rule_file
    
    def get_version(self) -> int:
        """获取版本号"""
        return self._rule_file.version if self._rule_file else 1
    
    def set_version(self, version: int):
        """设置版本号"""
        if self._rule_file:
            self._rule_file.version = version
            self._set_modified()
    
    def _on_version_changed(self, text: str):
        """版本号变化处理"""
        if not self._rule_file:
            return
        try:
            version = int(text) if text else 1
            if version != self._rule_file.version:
                self._rule_file.version = version
                self._set_modified()
        except ValueError:
            pass
    
    def _update_version_display(self):
        """更新版本号显示"""
        if self._rule_file:
            self.version_edit.blockSignals(True)
            self.version_edit.setText(str(self._rule_file.version))
            self.version_edit.blockSignals(False)
        else:
            self.version_edit.blockSignals(True)
            self.version_edit.setText("1")
            self.version_edit.blockSignals(False)
    
    def _refresh_list(self):
        """刷新规则列表"""
        self.rule_list.clear()
        
        if not self._rule_file:
            return
        
        for rule in self._rule_file.rules:
            item = QListWidgetItem()
            item_widget = RuleListItem(rule)
            # 设置固定高度确保内容完整显示
            item.setSizeHint(QSize(item_widget.sizeHint().width(), 70))
            self.rule_list.addItem(item)
            self.rule_list.setItemWidget(item, item_widget)
    
    def _on_rule_selected(self, row: int):
        """规则选中处理"""
        if row < 0 or not self._rule_file or row >= len(self._rule_file.rules):
            self.edit_panel.clear()
            self.delete_btn.setEnabled(False)
            return
        
        rule = self._rule_file.rules[row]
        self.edit_panel.load_rule(rule)
        self.delete_btn.setEnabled(True)
    
    def _on_rule_changed(self):
        """规则变化处理"""
        self._set_modified()
        
        # 更新列表项显示
        row = self.rule_list.currentRow()
        if row >= 0:
            item = self.rule_list.item(row)
            widget = self.rule_list.itemWidget(item)
            if widget and isinstance(widget, RuleListItem):
                widget.update_display()
    
    def _add_rule(self):
        """添加新规则"""
        if not self._rule_file:
            self._rule_file = RuleFile()
        
        # 生成新规则编号
        import random
        code = f"NEW_RULE_{random.randint(100000, 999999)}"
        
        new_rule = Rule(
            code=code,
            name="新规则",
            enabled=True,
            severity=Severity.MEDIUM,
            expression="",
            message=""
        )
        
        self._rule_file.rules.append(new_rule)
        self._refresh_list()
        
        # 选中新规则
        self.rule_list.setCurrentRow(len(self._rule_file.rules) - 1)
        self._set_modified()
    
    def _delete_rule(self):
        """删除当前规则"""
        row = self.rule_list.currentRow()
        if row < 0 or not self._rule_file:
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(f"确定要删除规则 \"{self._rule_file.rules[row].name}\" 吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        yes_btn = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        no_btn = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(no_btn)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == yes_btn:
            del self._rule_file.rules[row]
            self._refresh_list()
            self._set_modified()
            
            # 选中相邻的规则
            if self._rule_file.rules:
                new_row = min(row, len(self._rule_file.rules) - 1)
                self.rule_list.setCurrentRow(new_row)
            else:
                self.edit_panel.clear()
    
    def _set_modified(self):
        """设置已修改状态"""
        self._is_modified = True
        self.file_modified.emit()
