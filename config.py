"""
项目详情页爬虫配置文件
"""

# 爬虫基本设置
SCRAPER_CONFIG = {
    "headless": True,  # 是否无头模式
    "max_workers": 2,   # 最大并发线程数
    "output_dir": "output",  # 输出目录
    "batch_size": 100,  # 每批次项目数量
}

# 延时设置
DELAY_CONFIG = {
    "min_delay": 3,     # 最小延时（秒）
    "max_delay": 6,     # 最大延时（秒）
    "batch_delay": 10,  # 批次间延时（秒）
    "page_load_delay": 2,  # 页面加载延时（秒）
}

# 反爬虫设置
ANTI_CRAWL_CONFIG = {
    "user_agents": [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ],
    "window_size": "1920,1080",
    "timeout": 15,  # 页面加载超时时间
}

# 数据提取设置
EXTRACTION_CONFIG = {
    "max_description_length": 3000,  # 描述最大长度
    "max_images": 10,  # 最大图片数量
    "min_text_length": 20,  # 最小文本长度
    "max_text_length": 2000,  # 最大文本长度
}

# 文件路径设置
FILE_PATHS = {
    "urls_file": "project_urls.txt",
    "summary_file": "output/projects_summary.json",
    "metadata_file": "output/metadata.json",
    "progress_file": "output/scrape_progress.json",
    "logs_dir": "output/logs",
    "details_dir": "output/details",
}

# 日志设置
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(levelname)s - %(message)s",
    "log_file": "output/logs/scraper.log",
}

# 验证设置
VALIDATION_CONFIG = {
    "test_batches": 1,  # 验证阶段抓取的批次数量
    "test_urls": 3,     # 验证阶段抓取的URL数量
    "success_rate_threshold": 0.8,  # 成功率阈值
} 