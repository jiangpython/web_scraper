#!/usr/bin/env python3
"""
配置加载器 - 从.env文件加载配置
"""

import os
from typing import Dict, Any

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_file="config.env"):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            self.config[key.strip()] = value.strip()
        
        # 设置环境变量
        for key, value in self.config.items():
            if key not in os.environ:
                os.environ[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置值"""
        try:
            return int(self.config.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置值"""
        value = self.config.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = str(value)
        os.environ[key] = str(value)
    
    def save_config(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("# 数英网数据统计与智能对话系统配置文件\n")
            f.write("# 请根据实际情况修改以下配置\n\n")
            
            # 按分类组织配置
            sections = {
                "Gemini API配置": ["GEMINI_API_KEY"],
                "服务器配置": ["SERVER_HOST", "SERVER_PORT", "DEBUG_MODE"],
                "数据配置": ["DATA_FOLDER", "OUTPUT_FOLDER", "WEB_DATA_FILE"],
                "分析配置": ["BATCH_SIZE", "MAX_WORKERS", "POOL_SIZE"],
                "延时配置": ["MIN_DELAY", "MAX_DELAY", "BATCH_DELAY"],
                "日志配置": ["LOG_LEVEL", "LOG_FILE"],
                "浏览器配置": ["AUTO_OPEN_BROWSER", "BROWSER_URL"]
            }
            
            for section_name, keys in sections.items():
                f.write(f"\n# {section_name}\n")
                for key in keys:
                    if key in self.config:
                        f.write(f"{key}={self.config[key]}\n")

# 全局配置实例
config = ConfigLoader()

def get_config() -> ConfigLoader:
    """获取全局配置实例"""
    return config 