# -*- coding: utf-8 -*-
"""
SpEL代码自动补全器
"""
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (QCompleter, QTextEdit, QPlainTextEdit, 
                              QListView, QAbstractItemView)
from PyQt6.QtCore import Qt, QStringListModel, QRect
from PyQt6.QtGui import (QTextCursor, QKeyEvent, QFocusEvent, 
                          QStandardItemModel, QStandardItem, QColor, QBrush)


class SpelKeywords:
    """SpEL关键字和内置函数"""
    
    # SpEL操作符
    OPERATORS = ['==', '!=', '>', '<', '>=', '<=', 'and', 'or', 'not', 
                 '&&', '||', '!', '+', '-', '*', '/', '%', '^',
                 '?:', 'instanceof', 'matches', 'between']
    
    # SpEL特殊变量
    SPECIAL_VARS = ['#this', '#root', '#fn', 'null', 'true', 'false', 'NULL', 'T()']
    
    # 常用集合操作
    COLLECTION_OPS = ['.size()', '.isEmpty()', '.?[]', '.![]', '.^[]', '.$[]',
                      '.contains()', '.containsKey()', '.containsValue()',
                      '.get()', '.put()', '.add()', '.remove()', '.clear()']
    
    # 字符串操作
    STRING_OPS = ['.length()', '.trim()', '.toLowerCase()', '.toUpperCase()',
                  '.substring()', '.indexOf()', '.startsWith()', '.endsWith()',
                  '.replace()', '.split()', '.isEmpty()', '.equals()',
                  '.equalsIgnoreCase()', '.contains()', '.matches()']
    
    # 日期操作
    DATE_OPS = ['.isBefore()', '.isAfter()', '.isEqual()', '.plusDays()', 
                '.minusDays()', '.plusMonths()', '.minusMonths()',
                '.getYear()', '.getMonth()', '.getDayOfMonth()']


class SpelCompleter:
    """SpEL代码补全器"""
    
    # 成对符号
    PAIR_CHARS = {
        '(': ')',
        '[': ']',
        '{': '}',
        '"': '"',
        "'": "'",
    }
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._completions: List[str] = []
        self._build_completions()
        
    def _build_completions(self):
        """构建补全列表"""
        self._completions = []
        
        # 添加SpEL关键字
        self._completions.extend(SpelKeywords.OPERATORS)
        self._completions.extend(SpelKeywords.SPECIAL_VARS)
        
        # 添加常用操作
        for op in SpelKeywords.COLLECTION_OPS:
            self._completions.append(op)
        for op in SpelKeywords.STRING_OPS:
            self._completions.append(op)
        for op in SpelKeywords.DATE_OPS:
            self._completions.append(op)
        
        # 从配置中加载扫描到的类和方法
        if self.config_manager:
            self._load_from_config()
    
    def _load_from_config(self):
        """从配置中加载扫描结果"""
        if not self.config_manager:
            return
            
        # 加载所有类
        classes = self.config_manager.get_all_scanned_classes()
        for cls in classes:
            class_name = cls.get('name', '')
            if class_name:
                self._completions.append(class_name)
            
            # 加载字段
            for field in cls.get('fields', []):
                field_name = field.get('name', '')
                if field_name:
                    self._completions.append(field_name)
                    # 添加带点的形式
                    self._completions.append(f".{field_name}")
            
            # 加载方法
            for method in cls.get('methods', []):
                method_name = method.get('name', '')
                if method_name:
                    params = method.get('params', [])
                    params_str = ', '.join(params) if params else ''
                    self._completions.append(f"{method_name}({params_str})")
                    self._completions.append(f".{method_name}({params_str})")
        
        # 加载函数类的方法（以#fn.xxx的形式）
        function_classes = self.config_manager.get_function_classes()
        for cls in function_classes:
            for method in cls.get('methods', []):
                method_name = method.get('name', '')
                if method_name:
                    params = method.get('params', [])
                    params_str = ', '.join(params) if params else ''
                    self._completions.append(f"#fn.{method_name}({params_str})")
    
    def refresh_completions(self):
        """刷新补全列表"""
        self._completions = []
        self._build_completions()
    
    def get_completions(self, prefix: str = "") -> List[str]:
        """获取补全建议，按匹配度排序（大小写匹配优先，但不区分大小写搜索）"""
        if not prefix:
            return self._completions[:50]  # 限制返回数量
        
        prefix_lower = prefix.lower()
        
        # 分类匹配结果，每个类别再分为大小写匹配和不匹配
        exact_case_match = []       # 完全匹配 + 大小写相同
        exact_case_diff = []        # 完全匹配 + 大小写不同
        prefix_case_match = []      # 前缀匹配 + 大小写相同
        prefix_case_diff = []       # 前缀匹配 + 大小写不同
        contains_case_match = []    # 包含匹配 + 大小写相同
        contains_case_diff = []     # 包含匹配 + 大小写不同
        
        for item in self._completions:
            item_lower = item.lower()
            # 提取用于匹配的名称（去掉.和#前缀，去掉括号及参数）
            match_name_lower = item_lower.lstrip('.#')
            match_name_original = item.lstrip('.#')
            if '(' in match_name_lower:
                paren_pos = match_name_lower.index('(')
                match_name_lower = match_name_lower[:paren_pos]
                match_name_original = match_name_original[:paren_pos]
            
            # 检查大小写是否匹配
            def case_matches(original: str, input_prefix: str) -> bool:
                """检查输入的前缀与原字符串的大小写是否一致"""
                if len(input_prefix) > len(original):
                    return False
                return original[:len(input_prefix)] == input_prefix
            
            if match_name_lower == prefix_lower:
                # 完全匹配
                if case_matches(match_name_original, prefix):
                    exact_case_match.append(item)
                else:
                    exact_case_diff.append(item)
            elif match_name_lower.startswith(prefix_lower):
                # 前缀匹配
                if case_matches(match_name_original, prefix):
                    prefix_case_match.append((len(match_name_lower), item))
                else:
                    prefix_case_diff.append((len(match_name_lower), item))
            elif prefix_lower in match_name_lower:
                # 包含匹配
                pos = match_name_lower.index(prefix_lower)
                # 检查包含位置的大小写是否匹配
                if match_name_original[pos:pos+len(prefix)] == prefix:
                    contains_case_match.append((pos, len(match_name_lower), item))
                else:
                    contains_case_diff.append((pos, len(match_name_lower), item))
        
        # 排序
        prefix_case_match.sort(key=lambda x: x[0])
        prefix_case_diff.sort(key=lambda x: x[0])
        contains_case_match.sort(key=lambda x: (x[0], x[1]))
        contains_case_diff.sort(key=lambda x: (x[0], x[1]))
        
        # 合并结果：每个类别中大小写匹配的优先
        result = (exact_case_match + exact_case_diff + 
                  [m[1] for m in prefix_case_match] + [m[1] for m in prefix_case_diff] +
                  [m[2] for m in contains_case_match] + [m[2] for m in contains_case_diff])
        return result[:30]  # 限制返回数量
    
    def get_context_completions(self, text: str, cursor_pos: int) -> List[str]:
        """基于上下文获取补全建议"""
        # 获取光标前的文本
        text_before = text[:cursor_pos]
        
        # 找到当前正在输入的词
        word_start = cursor_pos
        for i in range(cursor_pos - 1, -1, -1):
            char = text[i] if i < len(text) else ''
            if char in ' \t\n()[]{}=<>!&|+-*/%^,;:':
                break
            word_start = i
        
        current_word = text[word_start:cursor_pos]
        
        # 检查是否在输入#fn.之后的方法名
        if current_word.startswith('#fn.'):
            # 提取方法名前缀
            method_prefix = current_word[4:]  # 去掉 '#fn.'
            # 返回函数类的方法，并过滤
            if self.config_manager:
                fn_methods = []
                for cls in self.config_manager.get_function_classes():
                    for method in cls.get('methods', []):
                        method_name = method.get('name', '')
                        params = method.get('params', [])
                        params_str = ', '.join(params) if params else ''
                        full_method = f"{method_name}({params_str})"
                        # 过滤：方法名以输入的前缀开头
                        if not method_prefix or method_name.lower().startswith(method_prefix.lower()):
                            fn_methods.append(full_method)
                return fn_methods
            return []
        
        # 检查是否在输入点之后（对象属性/方法访问）
        if '.' in current_word:
            parts = current_word.rsplit('.', 1)
            if len(parts) == 2:
                obj_name, prop_prefix = parts
                # 查找对象类型并返回其属性和方法
                return self._get_object_members(obj_name, prop_prefix)
        
        return self.get_completions(current_word)
    
    def _get_object_members(self, obj_name: str, prefix: str) -> List[str]:
        """获取对象的成员（属性和方法）"""
        members = []
        
        if not self.config_manager:
            # 返回通用的操作
            all_ops = (SpelKeywords.COLLECTION_OPS + 
                      SpelKeywords.STRING_OPS + 
                      SpelKeywords.DATE_OPS)
            for op in all_ops:
                if op.startswith('.'):
                    member = op[1:]  # 去掉开头的点
                    if not prefix or member.lower().startswith(prefix.lower()):
                        members.append(member)
            return members
        
        # 查找匹配的类
        classes = self.config_manager.get_all_scanned_classes()
        for cls in classes:
            # 检查字段名是否匹配
            for field in cls.get('fields', []):
                if field.get('name') == obj_name:
                    # 找到匹配的类，返回其成员
                    field_type = field.get('type', '')
                    return self._get_class_members_by_type(field_type, prefix)
        
        # 通用成员
        all_ops = (SpelKeywords.COLLECTION_OPS + 
                  SpelKeywords.STRING_OPS + 
                  SpelKeywords.DATE_OPS)
        for op in all_ops:
            if op.startswith('.'):
                member = op[1:]
                if not prefix or member.lower().startswith(prefix.lower()):
                    members.append(member)
        
        return members
    
    def _get_class_members_by_type(self, type_name: str, prefix: str) -> List[str]:
        """根据类型名获取类成员"""
        members = []
        
        if not self.config_manager:
            return members
        
        classes = self.config_manager.get_all_scanned_classes()
        for cls in classes:
            if cls.get('name') == type_name or cls.get('full_name', '').endswith(type_name):
                # 添加字段
                for field in cls.get('fields', []):
                    name = field.get('name', '')
                    if not prefix or name.lower().startswith(prefix.lower()):
                        members.append(name)
                
                # 添加方法
                for method in cls.get('methods', []):
                    name = method.get('name', '')
                    params = method.get('params', [])
                    params_str = ', '.join(params) if params else ''
                    method_str = f"{name}({params_str})"
                    if not prefix or name.lower().startswith(prefix.lower()):
                        members.append(method_str)
        
        return members
    
    @staticmethod
    def get_matching_bracket(char: str) -> Optional[str]:
        """获取匹配的括号"""
        return SpelCompleter.PAIR_CHARS.get(char)
    
    @staticmethod
    def should_auto_complete_pair(char: str) -> bool:
        """判断是否应该自动补全成对符号"""
        return char in SpelCompleter.PAIR_CHARS


class SpelTextEdit(QPlainTextEdit):
    """支持SpEL代码补全的文本编辑器"""
    
    def __init__(self, parent=None, spel_completer: SpelCompleter = None):
        super().__init__(parent)
        self.spel_completer = spel_completer
        self._completing = False  # 防止递归
        self._popup_visible = False
        
        # 创建补全弹出框 - 使用ToolTip类型避免抢夺焦点
        self.completer_popup = QListView()
        self.completer_popup.setWindowFlags(
            Qt.WindowType.ToolTip | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.completer_popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.completer_popup.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.completer_popup.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.completer_popup.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.completer_popup.clicked.connect(self._on_popup_clicked)
        self.completer_popup.hide()
        
        # 设置补全弹出框样式
        self.completer_popup.setStyleSheet("""
            QListView {
                background-color: #2d2d30;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 10pt;
                outline: none;
            }
            QListView::item {
                padding: 6px 10px;
                border-radius: 2px;
            }
            QListView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QListView::item:hover {
                background-color: #3c3c3c;
            }
        """)
        
        self.completer_model = QStringListModel()
        self.completer_popup.setModel(self.completer_model)
        
        # 设置字体
        self.setFont(self.font())
    
    def set_spel_completer(self, completer: SpelCompleter):
        """设置SpEL补全器"""
        self.spel_completer = completer
    
    def _on_popup_clicked(self, index):
        """点击补全列表项"""
        self._insert_completion(index)
        self.setFocus()  # 恢复焦点到编辑框
    
    def keyPressEvent(self, event: QKeyEvent):
        """处理按键事件"""
        # 处理补全弹出框的导航
        if self._popup_visible:
            if event.key() == Qt.Key.Key_Down:
                self._move_selection(1)
                return
            elif event.key() == Qt.Key.Key_Up:
                self._move_selection(-1)
                return
            elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                self._insert_completion()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self._hide_popup()
                return
        
        # Alt+/ 手动触发代码补全 (避免与输入法冲突)
        if event.key() == Qt.Key.Key_Slash and event.modifiers() == Qt.KeyboardModifier.AltModifier:
            self._update_completions(force=True)
            return
        
        # 处理成对符号自动补全
        text = event.text()
        if text and SpelCompleter.should_auto_complete_pair(text):
            closing = SpelCompleter.get_matching_bracket(text)
            if closing:
                super().keyPressEvent(event)
                cursor = self.textCursor()
                cursor.insertText(closing)
                cursor.movePosition(QTextCursor.MoveOperation.Left)
                self.setTextCursor(cursor)
                # 触发补全更新
                self._update_completions()
                return
        
        # 处理退格键删除成对符号
        if event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                pos = cursor.position()
                text = self.toPlainText()
                if pos > 0 and pos < len(text):
                    char_before = text[pos - 1]
                    char_after = text[pos]
                    if SpelCompleter.PAIR_CHARS.get(char_before) == char_after:
                        # 同时删除成对符号
                        cursor.deleteChar()
        
        super().keyPressEvent(event)
        
        # 在按键后更新补全建议（仅对可打印字符）
        if event.text() and event.text().isprintable():
            self._update_completions()
    
    def _hide_popup(self):
        """隐藏补全弹出框"""
        self._popup_visible = False
        self.completer_popup.hide()
    
    def _update_completions(self, force: bool = False):
        """更新补全建议"""
        if self._completing or not self.spel_completer:
            return
        
        self._completing = True
        try:
            cursor = self.textCursor()
            text = self.toPlainText()
            pos = cursor.position()
            
            # 获取当前输入的词
            word_start = pos
            for i in range(pos - 1, -1, -1):
                if i >= len(text):
                    break
                char = text[i]
                if char in ' \t\n()[]{}=<>!&|+-*/%^,;:':
                    break
                word_start = i
            
            current_word = text[word_start:pos] if word_start < pos else ""
            
            # 如果输入长度足够或强制显示，显示补全建议
            if len(current_word) >= 1 or force:
                completions = self.spel_completer.get_context_completions(text, pos)
                if completions:
                    self._show_completions(completions)
                else:
                    self._hide_popup()
            else:
                self._hide_popup()
        finally:
            self._completing = False
    
    def _show_completions(self, completions: List[str]):
        """显示补全建议"""
        self.completer_model.setStringList(completions)
        
        # 计算弹出框位置
        cursor_rect = self.cursorRect()
        popup_pos = self.mapToGlobal(cursor_rect.bottomLeft())
        
        # 调整位置，确保在屏幕内
        popup_pos.setY(popup_pos.y() + 2)
        
        # 设置弹出框大小和位置
        self.completer_popup.setMinimumWidth(250)
        self.completer_popup.setMaximumWidth(400)
        self.completer_popup.setMaximumHeight(200)
        self.completer_popup.move(popup_pos)
        self.completer_popup.show()
        self.completer_popup.raise_()
        self._popup_visible = True
        
        # 选中第一项
        if completions:
            self.completer_popup.setCurrentIndex(self.completer_model.index(0))
    
    def _move_selection(self, delta: int):
        """移动选择"""
        current = self.completer_popup.currentIndex()
        row = current.row() + delta
        row = max(0, min(row, self.completer_model.rowCount() - 1))
        self.completer_popup.setCurrentIndex(self.completer_model.index(row))
    
    def _insert_completion(self, index=None):
        """插入选中的补全项"""
        if index is None:
            index = self.completer_popup.currentIndex()
        
        if not index.isValid():
            self._hide_popup()
            return
        
        completion = self.completer_model.data(index, Qt.ItemDataRole.DisplayRole)
        
        # 处理函数补全：只保留函数名和空括号，去掉参数描述
        if '(' in completion and ')' in completion:
            # 检查是否是函数形式 name(params)
            paren_start = completion.index('(')
            func_name = completion[:paren_start]
            # 只保留函数名和空括号
            completion = f"{func_name}()"
        
        # 获取当前词的起始位置（以.作为分隔符，只替换.后面的内容）
        cursor = self.textCursor()
        text = self.toPlainText()
        pos = cursor.position()
        
        word_start = pos
        for i in range(pos - 1, -1, -1):
            if i >= len(text):
                break
            char = text[i]
            # 把.也作为分隔符，这样"baseInfo.na"只会替换"na"部分
            if char in ' \t\n()[]{}=<>!&|+-*/%^,;:.#':
                break
            word_start = i
        
        # 替换当前词
        cursor.setPosition(word_start)
        cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
        
        # 处理补全文本
        if completion.startswith('.'):
            # 如果补全是以点开头的，去掉开头的点（因为.已作为分隔符）
            completion = completion[1:]
        if completion.startswith('#'):
            # 如果补全是以#开头的，检查前面是否已有#
            if word_start > 0 and text[word_start - 1] == '#':
                completion = completion[1:]  # 去掉开头的#
        
        cursor.insertText(completion)
        
        # 如果插入的是函数，把光标移到括号中间
        if completion.endswith('()'):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1)
            self.setTextCursor(cursor)
        
        self._hide_popup()
    
    def focusOutEvent(self, event: QFocusEvent):
        """失去焦点时隐藏补全弹出框"""
        # 使用延时隐藏，避免立即隐藏导致点击补全项失败
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._delayed_hide_popup)
        super().focusOutEvent(event)
    
    def _delayed_hide_popup(self):
        """延时隐藏弹出框"""
        # 如果鼠标在弹出框上，不隐藏
        if self.completer_popup.underMouse():
            return
        # 如果编辑器有焦点，不隐藏
        if self.hasFocus():
            return
        self._hide_popup()

