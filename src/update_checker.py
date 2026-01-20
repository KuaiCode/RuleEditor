# -*- coding: utf-8 -*-
"""
更新检测器
"""
import json
import webbrowser
from typing import Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError
from PyQt6.QtCore import QThread, pyqtSignal


# 应用版本
APP_VERSION = "1.1"

# GitHub 仓库信息 (请根据实际情况修改)
GITHUB_OWNER = "your-username"
GITHUB_REPO = "RuleEditor"


class UpdateChecker(QThread):
    """更新检测线程"""
    
    update_available = pyqtSignal(str, str)  # (latest_version, release_url)
    check_finished = pyqtSignal(bool, str)   # (has_update, message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    
    def run(self):
        """检测更新"""
        try:
            result = self._check_update()
            if result:
                latest_version, release_url = result
                if self._compare_versions(latest_version, APP_VERSION) > 0:
                    self.update_available.emit(latest_version, release_url)
                    self.check_finished.emit(True, f"发现新版本: {latest_version}")
                else:
                    self.check_finished.emit(False, "当前已是最新版本")
            else:
                self.check_finished.emit(False, "检查更新失败")
        except Exception as e:
            self.check_finished.emit(False, f"检查更新失败: {str(e)}")
    
    def _check_update(self) -> Optional[Tuple[str, str]]:
        """检查 GitHub Release"""
        try:
            request = Request(
                self.api_url,
                headers={
                    'User-Agent': f'RuleEditor/{APP_VERSION}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                tag_name = data.get('tag_name', '')
                html_url = data.get('html_url', '')
                
                # 去掉 v 前缀
                version = tag_name.lstrip('v')
                return (version, html_url)
        except URLError:
            return None
        except Exception:
            return None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        比较版本号
        返回: 1 如果 v1 > v2, -1 如果 v1 < v2, 0 如果相等
        """
        def parse_version(v):
            parts = []
            for part in v.split('.'):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(0)
            return parts
        
        v1_parts = parse_version(v1)
        v2_parts = parse_version(v2)
        
        # 补齐长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for p1, p2 in zip(v1_parts, v2_parts):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0


def open_release_page(url: str):
    """打开 Release 页面"""
    webbrowser.open(url)


def get_app_version() -> str:
    """获取应用版本"""
    return APP_VERSION
