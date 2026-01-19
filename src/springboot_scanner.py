# -*- coding: utf-8 -*-
"""
SpringBoot项目扫描器
扫描Java源代码，提取类、字段、方法信息用于代码补全
"""
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False


class SpringBootScanner:
    """SpringBoot项目扫描器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._scanned_classes: List[Dict[str, Any]] = []
        
    def scan_project(self, project_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        扫描SpringBoot项目
        
        Args:
            project_path: 项目根目录路径
            progress_callback: 进度回调函数 (current, total, message)
            
        Returns:
            扫描结果字典
        """
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise ValueError(f"项目路径不存在: {project_path}")
        
        # 查找Java源文件
        java_files = list(project_path.rglob("*.java"))
        
        # 过滤测试文件和构建目录
        java_files = [f for f in java_files 
                      if 'test' not in str(f).lower() 
                      and 'target' not in str(f)
                      and 'build' not in str(f)
                      and '.gradle' not in str(f)]
        
        total_files = len(java_files)
        if total_files == 0:
            return {
                'name': project_path.name,
                'path': str(project_path),
                'scanned_at': datetime.now().isoformat(),
                'classes': []
            }
        
        self._scanned_classes = []
        
        # 获取函数类后缀
        function_suffix = "Functions"
        if self.config_manager:
            function_suffix = self.config_manager.get_function_classes_suffix()
        
        # 扫描文件
        for i, java_file in enumerate(java_files):
            if progress_callback:
                progress_callback(i + 1, total_files, f"正在扫描: {java_file.name}")
            
            try:
                classes = self._parse_java_file(java_file, function_suffix)
                self._scanned_classes.extend(classes)
            except Exception as e:
                print(f"解析文件失败 {java_file}: {e}")
        
        result = {
            'name': project_path.name,
            'path': str(project_path),
            'scanned_at': datetime.now().isoformat(),
            'classes': self._scanned_classes
        }
        
        # 保存到配置
        if self.config_manager:
            self.config_manager.add_springboot_project(result)
        
        return result
    
    def _parse_java_file(self, file_path: Path, function_suffix: str) -> List[Dict[str, Any]]:
        """解析单个Java文件"""
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except Exception:
                return classes
        
        if HAS_JAVALANG:
            classes = self._parse_with_javalang(content, function_suffix)
        else:
            classes = self._parse_with_regex(content, function_suffix)
        
        return classes
    
    def _parse_with_javalang(self, content: str, function_suffix: str) -> List[Dict[str, Any]]:
        """使用javalang库解析Java代码"""
        classes = []
        
        try:
            tree = javalang.parse.parse(content)
        except Exception:
            return self._parse_with_regex(content, function_suffix)
        
        package_name = tree.package.name if tree.package else ""
        
        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            class_info = self._extract_class_info(node, package_name, function_suffix)
            if class_info:
                classes.append(class_info)
        
        for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
            class_info = self._extract_interface_info(node, package_name, function_suffix)
            if class_info:
                classes.append(class_info)
        
        return classes
    
    def _extract_class_info(self, node, package_name: str, function_suffix: str) -> Optional[Dict[str, Any]]:
        """提取类信息"""
        class_name = node.name
        full_name = f"{package_name}.{class_name}" if package_name else class_name
        
        is_function_class = class_name.endswith(function_suffix)
        
        # 提取字段
        fields = []
        for field in node.fields:
            for declarator in field.declarators:
                field_type = self._get_type_name(field.type)
                fields.append({
                    'name': declarator.name,
                    'type': field_type,
                    'modifiers': list(field.modifiers) if field.modifiers else []
                })
        
        # 提取方法
        methods = []
        for method in node.methods:
            params = []
            if method.parameters:
                for param in method.parameters:
                    param_type = self._get_type_name(param.type)
                    params.append(f"{param_type} {param.name}")
            
            return_type = self._get_type_name(method.return_type) if method.return_type else "void"
            
            methods.append({
                'name': method.name,
                'params': params,
                'return_type': return_type,
                'modifiers': list(method.modifiers) if method.modifiers else []
            })
        
        return {
            'name': class_name,
            'package': package_name,
            'full_name': full_name,
            'fields': fields,
            'methods': methods,
            'is_function_class': is_function_class
        }
    
    def _extract_interface_info(self, node, package_name: str, function_suffix: str) -> Optional[Dict[str, Any]]:
        """提取接口信息"""
        interface_name = node.name
        full_name = f"{package_name}.{interface_name}" if package_name else interface_name
        
        is_function_class = interface_name.endswith(function_suffix)
        
        # 提取方法
        methods = []
        for method in node.methods:
            params = []
            if method.parameters:
                for param in method.parameters:
                    param_type = self._get_type_name(param.type)
                    params.append(f"{param_type} {param.name}")
            
            return_type = self._get_type_name(method.return_type) if method.return_type else "void"
            
            methods.append({
                'name': method.name,
                'params': params,
                'return_type': return_type,
                'modifiers': list(method.modifiers) if method.modifiers else []
            })
        
        return {
            'name': interface_name,
            'package': package_name,
            'full_name': full_name,
            'fields': [],
            'methods': methods,
            'is_function_class': is_function_class
        }
    
    def _get_type_name(self, type_node) -> str:
        """获取类型名称"""
        if type_node is None:
            return "void"
        
        if hasattr(type_node, 'name'):
            type_name = type_node.name
            # 处理泛型
            if hasattr(type_node, 'arguments') and type_node.arguments:
                args = ', '.join(self._get_type_name(arg.type) if hasattr(arg, 'type') else str(arg)
                                for arg in type_node.arguments)
                type_name = f"{type_name}<{args}>"
            return type_name
        
        return str(type_node)
    
    def _parse_with_regex(self, content: str, function_suffix: str) -> List[Dict[str, Any]]:
        """使用正则表达式解析Java代码（备用方案）"""
        classes = []
        
        # 提取包名
        package_match = re.search(r'package\s+([\w.]+)\s*;', content)
        package_name = package_match.group(1) if package_match else ""
        
        # 提取类定义
        class_pattern = r'(?:public\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)'
        interface_pattern = r'(?:public\s+)?interface\s+(\w+)'
        
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            full_name = f"{package_name}.{class_name}" if package_name else class_name
            is_function_class = class_name.endswith(function_suffix)
            
            # 简单提取该类的方法（更详细的解析需要完整的语法分析）
            methods = self._extract_methods_regex(content, class_name)
            fields = self._extract_fields_regex(content, class_name)
            
            classes.append({
                'name': class_name,
                'package': package_name,
                'full_name': full_name,
                'fields': fields,
                'methods': methods,
                'is_function_class': is_function_class
            })
        
        for match in re.finditer(interface_pattern, content):
            interface_name = match.group(1)
            full_name = f"{package_name}.{interface_name}" if package_name else interface_name
            is_function_class = interface_name.endswith(function_suffix)
            
            methods = self._extract_methods_regex(content, interface_name)
            
            classes.append({
                'name': interface_name,
                'package': package_name,
                'full_name': full_name,
                'fields': [],
                'methods': methods,
                'is_function_class': is_function_class
            })
        
        return classes
    
    def _extract_methods_regex(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """使用正则提取方法"""
        methods = []
        
        # 简化的方法匹配模式
        method_pattern = r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(method_pattern, content):
            return_type = match.group(1)
            method_name = match.group(2)
            params_str = match.group(3).strip()
            
            # 跳过构造函数
            if method_name == class_name:
                continue
            
            # 解析参数
            params = []
            if params_str:
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        params.append(param)
            
            methods.append({
                'name': method_name,
                'params': params,
                'return_type': return_type,
                'modifiers': []
            })
        
        return methods
    
    def _extract_fields_regex(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """使用正则提取字段"""
        fields = []
        
        # 简化的字段匹配模式
        field_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*[;=]'
        
        for match in re.finditer(field_pattern, content):
            field_type = match.group(1)
            field_name = match.group(2)
            
            fields.append({
                'name': field_name,
                'type': field_type,
                'modifiers': []
            })
        
        return fields
    
    def get_scanned_classes(self) -> List[Dict[str, Any]]:
        """获取扫描到的类列表"""
        return self._scanned_classes
    
    def get_function_classes(self) -> List[Dict[str, Any]]:
        """获取函数类列表"""
        suffix = "Functions"
        if self.config_manager:
            suffix = self.config_manager.get_function_classes_suffix()
        
        return [c for c in self._scanned_classes 
                if c.get('name', '').endswith(suffix) or c.get('is_function_class', False)]


class ScanProgressDialog:
    """扫描进度对话框的辅助类"""
    
    @staticmethod
    def create_progress_callback(progress_dialog):
        """创建进度回调函数"""
        def callback(current, total, message):
            if progress_dialog:
                progress_dialog.setMaximum(total)
                progress_dialog.setValue(current)
                progress_dialog.setLabelText(message)
        return callback
