# -*- coding: utf-8 -*-
"""
配置管理器
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "last_opened_file": "",
        "recent_files": [],
        "auto_backup": {
            "enabled": True,
            "interval_minutes": 5,
            "max_backups": 10,
            "backup_dir": "backups"
        },
        "springboot_projects": [],
        "scanned_classes": {},
        "function_classes_suffix": "Functions",
        "theme": "auto",
        "window": {
            "width": 1400,
            "height": 900,
            "maximized": False
        }
    }
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # 默认配置目录在应用程序同级的config文件夹
            self.config_dir = Path(__file__).parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "app_config.json"
        self._config: Dict[str, Any] = {}
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._current_profile = "default"
        self.load()
    
    def load(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()
        
        # 加载所有配置文件
        self._load_profiles()
    
    def _load_profiles(self):
        """加载所有配置文件"""
        self._profiles = {"default": self._config}
        
        profiles_dir = self.config_dir / "profiles"
        if profiles_dir.exists():
            for profile_file in profiles_dir.glob("*.json"):
                profile_name = profile_file.stem
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        self._profiles[profile_name] = json.load(f)
                except Exception as e:
                    print(f"加载配置文件 {profile_name} 失败: {e}")
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def save_profile(self, profile_name: str):
        """保存指定配置文件"""
        if profile_name == "default":
            self.save()
            return
        
        profiles_dir = self.config_dir / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)
        
        profile_file = profiles_dir / f"{profile_name}.json"
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(self._profiles.get(profile_name, {}), f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件 {profile_name} 失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def get_profiles(self) -> List[str]:
        """获取所有配置文件名"""
        return list(self._profiles.keys())
    
    def get_current_profile(self) -> str:
        """获取当前配置文件名"""
        return self._current_profile
    
    def switch_profile(self, profile_name: str):
        """切换配置文件"""
        if profile_name in self._profiles:
            self._current_profile = profile_name
            self._config = self._profiles[profile_name]
    
    def create_profile(self, profile_name: str, base_profile: str = "default"):
        """创建新配置文件"""
        if profile_name not in self._profiles:
            base_config = self._profiles.get(base_profile, self.DEFAULT_CONFIG)
            self._profiles[profile_name] = base_config.copy()
            self.save_profile(profile_name)
    
    def delete_profile(self, profile_name: str):
        """删除配置文件"""
        if profile_name != "default" and profile_name in self._profiles:
            del self._profiles[profile_name]
            profile_file = self.config_dir / "profiles" / f"{profile_name}.json"
            if profile_file.exists():
                profile_file.unlink()
    
    def add_recent_file(self, file_path: str):
        """添加最近打开的文件"""
        recent = self.get('recent_files', [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        recent = recent[:10]  # 最多保留10个
        self.set('recent_files', recent)
        self.set('last_opened_file', file_path)
    
    def get_recent_files(self) -> List[str]:
        """获取最近打开的文件列表"""
        return self.get('recent_files', [])
    
    def add_springboot_project(self, project_data: Dict[str, Any]):
        """添加SpringBoot项目"""
        projects = self.get('springboot_projects', [])
        # 检查是否已存在
        for i, p in enumerate(projects):
            if p.get('path') == project_data.get('path'):
                projects[i] = project_data
                self.set('springboot_projects', projects)
                return
        projects.append(project_data)
        self.set('springboot_projects', projects)
    
    def get_springboot_projects(self) -> List[Dict[str, Any]]:
        """获取所有SpringBoot项目"""
        return self.get('springboot_projects', [])
    
    def remove_springboot_project(self, project_path: str):
        """移除SpringBoot项目"""
        projects = self.get('springboot_projects', [])
        projects = [p for p in projects if p.get('path') != project_path]
        self.set('springboot_projects', projects)
    
    def get_function_classes_suffix(self) -> str:
        """获取函数类后缀"""
        return self.get('function_classes_suffix', 'Functions')
    
    def set_function_classes_suffix(self, suffix: str):
        """设置函数类后缀"""
        self.set('function_classes_suffix', suffix)
    
    def get_all_scanned_classes(self) -> List[Dict[str, Any]]:
        """获取所有扫描到的类"""
        all_classes = []
        for project in self.get_springboot_projects():
            all_classes.extend(project.get('classes', []))
        return all_classes
    
    def get_function_classes(self) -> List[Dict[str, Any]]:
        """获取所有函数类"""
        suffix = self.get_function_classes_suffix()
        return [c for c in self.get_all_scanned_classes() 
                if c.get('name', '').endswith(suffix) or c.get('is_function_class', False)]
    
    def get_export_config(self) -> Dict[str, Any]:
        """获取可导出的配置（包含扫描结果）"""
        export_data = {
            "springboot_projects": self.get('springboot_projects', []),
            "function_classes_suffix": self.get_function_classes_suffix(),
            "scanned_classes": self.get('scanned_classes', {}),
        }
        return export_data
    
    def merge_config(self, imported_config: Dict[str, Any]):
        """合并导入的配置"""
        # 合并 SpringBoot 项目
        if 'springboot_projects' in imported_config:
            existing_projects = self.get('springboot_projects', [])
            imported_projects = imported_config.get('springboot_projects', [])
            
            # 按路径去重，导入的覆盖已有的
            project_map = {p.get('path'): p for p in existing_projects}
            for proj in imported_projects:
                project_map[proj.get('path')] = proj
            
            self.set('springboot_projects', list(project_map.values()))
        
        # 合并函数类后缀
        if 'function_classes_suffix' in imported_config:
            self.set('function_classes_suffix', imported_config['function_classes_suffix'])
        
        # 合并扫描的类
        if 'scanned_classes' in imported_config:
            existing_classes = self.get('scanned_classes', {})
            imported_classes = imported_config.get('scanned_classes', {})
            existing_classes.update(imported_classes)
            self.set('scanned_classes', existing_classes)
