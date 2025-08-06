"""
优化版项目详情页爬虫配置文件
支持更细粒度的配置管理
"""

import os
from typing import Dict, Any

# 爬虫基本设置
SCRAPER_CONFIG = {
    "headless": True,  # 是否无头模式
    "max_workers": 2,   # 最大并发线程数
    "output_dir": "output",  # 输出目录
    "batch_size": 50,  # 每批次项目数量（优化为更小批次）
    "pool_size": 3,    # WebDriver连接池大小
    "retry_times": 3,  # 失败重试次数
    "enable_statistics": True,  # 是否启用详细统计
}

# 延时设置（优化延时策略）
DELAY_CONFIG = {
    "min_delay": 2,     # 最小延时（秒）
    "max_delay": 4,     # 最大延时（秒）
    "batch_delay": 8,   # 批次间延时（秒）
    "page_load_delay": 3,  # 页面加载延时（秒）
    "error_retry_delay": 5,  # 错误重试延时（秒）
    "pool_wait_timeout": 30,  # 连接池等待超时（秒）
}

# 反爬虫设置（扩展User-Agent池）
ANTI_CRAWL_CONFIG = {
    "user_agents": [
        # Chrome
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
        # Safari
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        # Edge
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    ],
    "window_size": "1920,1080",
    "timeout": 15,  # 页面加载超时时间
    "max_idle_time": 300,  # WebDriver最大空闲时间（秒）
    "stealth_mode": True,  # 是否启用隐身模式
}

# 数据提取设置（优化提取参数）
EXTRACTION_CONFIG = {
    "max_description_length": 2000,  # 描述最大长度
    "max_images": 15,  # 最大图片数量
    "min_text_length": 10,  # 最小文本长度
    "max_text_length": 1500,  # 最大文本长度
    "max_creators": 10,  # 最大创作者数量
    "max_tags": 20,  # 最大标签数量
    "enable_content_validation": True,  # 是否启用内容验证
}

# 数英网特定设置
DIGITALING_CONFIG = {
    "base_url": "https://www.digitaling.com",
    "project_url_pattern": r"https://www\.digitaling\.com/projects/\d+\.html",
    "company_url_pattern": r"https://www\.digitaling\.com/company/projects/\d+",
    "trusted_domains": ["digitaling.com", "oss.digitaling.com"],
    "error_indicators": [
        "您访问的页面不存在",
        "页面未找到", 
        "404错误",
        "页面不存在或已被删除",
        "Page Not Found"
    ],
    "content_keywords": [
        "项目", "品牌", "营销", "创意", "活动", "广告",
        "设计", "传播", "推广", "策略", "概念", "理念"
    ]
}

# 文件路径设置
FILE_PATHS = {
    "urls_file": "project_urls.txt",
    "summary_file": "output/projects_summary.json",
    "metadata_file": "output/metadata.json",
    "progress_file": "output/scrape_progress.json",
    "batch_index_file": "output/details/batch_index.json",
    "logs_dir": "output/logs",
    "details_dir": "output/details",
}

# 日志设置
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(levelname)s - [%(threadName)s] %(message)s",
    "log_file": "output/logs/scraper.log",
    "max_log_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "enable_console_log": True,
    "enable_file_log": True,
}

# 验证设置
VALIDATION_CONFIG = {
    "test_batches": 1,  # 验证阶段抓取的批次数量
    "test_urls": 5,     # 验证阶段抓取的URL数量
    "success_rate_threshold": 0.7,  # 成功率阈值（调整为更现实的值）
    "min_valid_fields": 2,  # 最少有效字段数量
    "required_fields": ["title", "url"],  # 必需字段
}

# 性能优化设置
PERFORMANCE_CONFIG = {
    "enable_caching": True,  # 是否启用缓存
    "cache_size": 1000,  # 缓存大小
    "enable_compression": True,  # 是否启用压缩
    "memory_limit_mb": 512,  # 内存限制（MB）
    "disk_cache_size_mb": 100,  # 磁盘缓存大小（MB）
}

# 错误处理设置
ERROR_HANDLING_CONFIG = {
    "max_retry_attempts": 3,  # 最大重试次数
    "retry_delay_multiplier": 2,  # 重试延时倍增因子
    "error_threshold": 0.3,  # 错误率阈值
    "auto_recovery": True,  # 是否自动恢复
    "save_failed_urls": True,  # 是否保存失败URL
    "detailed_error_log": True,  # 是否记录详细错误日志
}


def get_config_value(config_name: str, key: str, default: Any = None) -> Any:
    """
    获取配置值的通用函数
    
    Args:
        config_name: 配置组名称
        key: 配置键
        default: 默认值
        
    Returns:
        配置值
    """
    config_map = {
        "scraper": SCRAPER_CONFIG,
        "delay": DELAY_CONFIG,
        "anti_crawl": ANTI_CRAWL_CONFIG,
        "extraction": EXTRACTION_CONFIG,
        "digitaling": DIGITALING_CONFIG,
        "file_paths": FILE_PATHS,
        "logging": LOGGING_CONFIG,
        "validation": VALIDATION_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "error_handling": ERROR_HANDLING_CONFIG,
    }
    
    config = config_map.get(config_name, {})
    return config.get(key, default)


def update_config_value(config_name: str, key: str, value: Any) -> bool:
    """
    更新配置值
    
    Args:
        config_name: 配置组名称
        key: 配置键
        value: 新值
        
    Returns:
        是否更新成功
    """
    config_map = {
        "scraper": SCRAPER_CONFIG,
        "delay": DELAY_CONFIG,
        "anti_crawl": ANTI_CRAWL_CONFIG,
        "extraction": EXTRACTION_CONFIG,
        "digitaling": DIGITALING_CONFIG,
        "file_paths": FILE_PATHS,
        "logging": LOGGING_CONFIG,
        "validation": VALIDATION_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "error_handling": ERROR_HANDLING_CONFIG,
    }
    
    config = config_map.get(config_name)
    if config is not None and key in config:
        config[key] = value
        return True
    return False


def validate_config() -> Dict[str, Any]:
    """
    验证配置的有效性
    
    Returns:
        验证结果字典
    """
    results = {
        "valid": True,
        "warnings": [],
        "errors": []
    }
    
    # 验证基本配置
    if SCRAPER_CONFIG["max_workers"] < 1 or SCRAPER_CONFIG["max_workers"] > 10:
        results["warnings"].append("max_workers应该在1-10之间")
    
    if SCRAPER_CONFIG["batch_size"] < 10 or SCRAPER_CONFIG["batch_size"] > 500:
        results["warnings"].append("batch_size应该在10-500之间")
    
    # 验证文件路径
    output_dir = SCRAPER_CONFIG["output_dir"]
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            results["errors"].append(f"无法创建输出目录 {output_dir}: {e}")
            results["valid"] = False
    
    # 验证延时设置
    if DELAY_CONFIG["min_delay"] >= DELAY_CONFIG["max_delay"]:
        results["warnings"].append("min_delay应该小于max_delay")
    
    return results


def get_runtime_config() -> Dict[str, Any]:
    """
    获取运行时配置摘要
    
    Returns:
        运行时配置字典
    """
    return {
        "scraper": SCRAPER_CONFIG,
        "delay": DELAY_CONFIG,
        "extraction": EXTRACTION_CONFIG,
        "validation": VALIDATION_CONFIG,
        "version": "2.0-optimized",
        "config_validation": validate_config()
    }


# 配置预设
CONFIG_PRESETS = {
    "development": {
        "headless": False,
        "max_workers": 1,
        "batch_size": 10,
        "pool_size": 1,
        "min_delay": 3,
        "max_delay": 5,
        "batch_delay": 5,
    },
    "testing": {
        "headless": True,
        "max_workers": 2,
        "batch_size": 20,
        "pool_size": 2,
        "min_delay": 2,
        "max_delay": 4,
        "batch_delay": 3,
    },
    "production": {
        "headless": True,
        "max_workers": 3,
        "batch_size": 50,
        "pool_size": 3,
        "min_delay": 2,
        "max_delay": 4,
        "batch_delay": 8,
    },
    "aggressive": {
        "headless": True,
        "max_workers": 5,
        "batch_size": 100,
        "pool_size": 5,
        "min_delay": 1,
        "max_delay": 2,
        "batch_delay": 3,
    }
}


def apply_preset(preset_name: str) -> bool:
    """
    应用预设配置
    
    Args:
        preset_name: 预设名称
        
    Returns:
        是否成功应用
    """
    if preset_name not in CONFIG_PRESETS:
        return False
    
    preset = CONFIG_PRESETS[preset_name]
    
    # 更新爬虫配置
    for key, value in preset.items():
        if key in SCRAPER_CONFIG:
            SCRAPER_CONFIG[key] = value
        elif key in DELAY_CONFIG:
            DELAY_CONFIG[key] = value
    
    return True