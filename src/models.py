# -*- coding: utf-8 -*-
"""
数据模型定义
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Severity(Enum):
    """规则严重程度"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    
    @classmethod
    def from_string(cls, value: str) -> 'Severity':
        try:
            return cls(value.upper())
        except ValueError:
            return cls.MEDIUM


@dataclass
class Rule:
    """规则数据模型"""
    code: str = ""
    name: str = ""
    enabled: bool = True
    severity: Severity = Severity.MEDIUM
    expression: str = ""
    message: str = ""
    
    # 兼容旧字段名
    condition_expression: str = ""
    message_template: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典用于YAML序列化"""
        result = {
            'code': self.code,
            'name': self.name,
            'enabled': self.enabled,
            'severity': self.severity.value
        }
        
        # 根据实际使用的字段名输出
        if self.condition_expression:
            result['conditionExpression'] = self.condition_expression
            result['messageTemplate'] = self.message_template or self.message
        else:
            result['expression'] = self.expression or self.condition_expression
            result['message'] = self.message or self.message_template
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """从字典创建Rule对象"""
        rule = cls()
        rule.code = data.get('code', '')
        rule.name = data.get('name', '')
        rule.enabled = data.get('enabled', True)
        rule.severity = Severity.from_string(data.get('severity', 'MEDIUM'))
        
        # 处理不同的字段名
        rule.expression = data.get('expression', '')
        rule.condition_expression = data.get('conditionExpression', '')
        rule.message = data.get('message', '')
        rule.message_template = data.get('messageTemplate', '')
        
        return rule
    
    def get_expression(self) -> str:
        """获取表达式（兼容两种字段名）"""
        return self.expression or self.condition_expression
    
    def set_expression(self, value: str):
        """设置表达式"""
        if self.condition_expression:
            self.condition_expression = value
        else:
            self.expression = value
    
    def get_message(self) -> str:
        """获取消息模板（兼容两种字段名）"""
        return self.message or self.message_template
    
    def set_message(self, value: str):
        """设置消息模板"""
        if self.message_template:
            self.message_template = value
        else:
            self.message = value


@dataclass
class RuleFile:
    """规则文件数据模型"""
    version: int = 1
    rules: List[Rule] = field(default_factory=list)
    file_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典用于YAML序列化"""
        return {
            'version': self.version,
            'rules': [rule.to_dict() for rule in self.rules]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_path: str = "") -> 'RuleFile':
        """从字典创建RuleFile对象"""
        rule_file = cls()
        rule_file.version = data.get('version', 1)
        rule_file.rules = [Rule.from_dict(r) for r in data.get('rules', [])]
        rule_file.file_path = file_path
        return rule_file


@dataclass
class JavaClass:
    """Java类信息"""
    name: str = ""
    package: str = ""
    full_name: str = ""
    fields: List[Dict[str, str]] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    is_function_class: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'package': self.package,
            'full_name': self.full_name,
            'fields': self.fields,
            'methods': self.methods,
            'is_function_class': self.is_function_class
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JavaClass':
        obj = cls()
        obj.name = data.get('name', '')
        obj.package = data.get('package', '')
        obj.full_name = data.get('full_name', '')
        obj.fields = data.get('fields', [])
        obj.methods = data.get('methods', [])
        obj.is_function_class = data.get('is_function_class', False)
        return obj


@dataclass 
class SpringBootProject:
    """SpringBoot项目配置"""
    name: str = ""
    path: str = ""
    scanned_at: str = ""
    classes: List[JavaClass] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'path': self.path,
            'scanned_at': self.scanned_at,
            'classes': [c.to_dict() for c in self.classes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpringBootProject':
        obj = cls()
        obj.name = data.get('name', '')
        obj.path = data.get('path', '')
        obj.scanned_at = data.get('scanned_at', '')
        obj.classes = [JavaClass.from_dict(c) for c in data.get('classes', [])]
        return obj
