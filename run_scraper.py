#!/usr/bin/env python3
"""
优化版项目详情页爬虫运行脚本
统一入口，支持多种运行模式和详细配置
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# 导入优化后的模块
from project_scraper_optimized import ProjectDetailScraperOptimized
from driver_pool import close_global_pool
from config_optimized import SCRAPER_CONFIG, VALIDATION_CONFIG, DELAY_CONFIG, EXTRACTION_CONFIG


class ScraperController:
    """爬虫控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.scraper = None
        self.config = self._load_runtime_config()
    
    def _load_runtime_config(self) -> Dict[str, Any]:
        """加载运行时配置"""
        return {
            "headless": SCRAPER_CONFIG.get("headless", True),
            "max_workers": SCRAPER_CONFIG.get("max_workers", 2),
            "output_dir": SCRAPER_CONFIG.get("output_dir", "output"),
            "batch_size": SCRAPER_CONFIG.get("batch_size", 100),
            "pool_size": SCRAPER_CONFIG.get("max_workers", 2),  # 默认与工作线程数相同
            "urls_file": "project_urls.txt",
            "auto_close_pool": True
        }
    
    def display_banner(self):
        """显示横幅信息"""
        print("=" * 70)
        print("        数英网项目详情页爬虫 - 优化版")
        print("=" * 70)
        print("✨ 新特性:")
        print("  • WebDriver连接池 - 减少资源消耗")
        print("  • 智能页面解析器 - 提高提取准确率")
        print("  • 优化错误处理 - 更稳定的运行")
        print("  • 详细统计信息 - 实时监控进度")
        print("=" * 70)
    
    def check_prerequisites(self) -> bool:
        """检查运行前提条件"""
        # 检查URL文件
        if not os.path.exists(self.config["urls_file"]):
            print(f"✗ 未找到URL文件: {self.config['urls_file']}")
            print("请创建 project_urls.txt 文件并添加项目URL")
            print("\n文件格式示例:")
            print("https://www.digitaling.com/projects/12345.html")
            print("https://www.digitaling.com/projects/12346.html")
            return False
        
        # 检查ChromeDriver
        print("正在检查WebDriver环境...")
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            # 尝试创建测试WebDriver
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            test_driver = webdriver.Chrome(options=options)
            test_driver.quit()
            print("✓ WebDriver环境检查通过")
            return True
            
        except Exception as e:
            print(f"✗ WebDriver环境检查失败: {e}")
            print("\n解决方案:")
            print("1. 确保Chrome浏览器已安装")
            print("2. 下载ChromeDriver并放在项目目录")
            print("3. 或安装: pip install webdriver-manager")
            return False
    
    def display_current_config(self):
        """显示当前配置"""
        print(f"\n📋 当前配置:")
        print(f"  无头模式: {'是' if self.config['headless'] else '否'}")
        print(f"  并发线程数: {self.config['max_workers']}")
        print(f"  连接池大小: {self.config['pool_size']}")
        print(f"  批次大小: {self.config['batch_size']}")
        print(f"  输出目录: {self.config['output_dir']}")
        print(f"  URL文件: {self.config['urls_file']}")
    
    def get_run_mode(self) -> str:
        """获取运行模式"""
        print("\n🚀 请选择运行模式:")
        print("1. 验证模式 (抓取1个批次，用于测试)")
        print("2. 完整模式 (抓取所有批次)")
        print("3. 自定义模式 (指定起始批次和数量)")
        print("4. 统计模式 (查看已抓取数据统计)")
        print("5. 配置模式 (调整运行参数)")
        
        while True:
            choice = input("\n请输入选择 (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return choice
            print("✗ 无效选择，请输入1-5之间的数字")
    
    def run_validation_mode(self):
        """验证模式"""
        print("\n🧪 启动验证模式...")
        print("将抓取1个批次用于测试系统稳定性")
        
        self._create_scraper()
        self.scraper.run(
            self.config["urls_file"], 
            start_batch=1, 
            max_batches=1
        )
        
        # 显示验证结果
        stats = self.scraper.get_statistics()
        self._display_validation_result(stats)
    
    def run_full_mode(self):
        """完整模式"""
        print("\n🔄 启动完整模式...")
        print("将抓取所有未处理的URL")
        
        # 确认操作
        confirm = input("确认开始完整抓取? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("操作已取消")
            return
        
        self._create_scraper()
        self.scraper.run(self.config["urls_file"])
    
    def run_custom_mode(self):
        """自定义模式"""
        print("\n⚙️ 自定义模式配置:")
        
        try:
            start_batch = input("起始批次 (默认1): ").strip()
            start_batch = int(start_batch) if start_batch else 1
            
            max_batches = input("最大批次数 (留空表示全部): ").strip()
            max_batches = int(max_batches) if max_batches else None
            
            print(f"\n📋 自定义配置:")
            print(f"  起始批次: {start_batch}")
            print(f"  最大批次数: {max_batches or '无限制'}")
            
            confirm = input("\n确认开始抓取? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("操作已取消")
                return
            
            self._create_scraper()
            self.scraper.run(
                self.config["urls_file"],
                start_batch=start_batch,
                max_batches=max_batches
            )
            
        except ValueError:
            print("✗ 输入格式错误，请输入有效数字")
    
    def run_statistics_mode(self):
        """统计模式"""
        print("\n📊 统计信息模式...")
        
        self._create_scraper()
        stats = self.scraper.get_statistics()
        
        print(f"\n📈 项目抓取统计:")
        print(f"  总项目数: {stats['total_projects']}")
        print(f"  总批次数: {stats['total_batches']}")
        print(f"  最后更新: {stats['last_updated'] or '未知'}")
        
        print(f"\n🔄 当前会话:")
        print(f"  已完成: {stats['current_session']['completed']}")
        print(f"  失败数: {stats['current_session']['failed']}")
        print(f"  成功率: {stats['current_session']['success_rate']}%")
        
        print(f"\n🔗 WebDriver连接池:")
        print(f"  可用连接: {stats['driver_pool']['available']}")
        print(f"  忙碌连接: {stats['driver_pool']['busy']}")
        print(f"  总连接数: {stats['driver_pool']['total']}/{stats['driver_pool']['max_size']}")
        
        print(f"\n⚙️ 配置信息:")
        for key, value in stats['config'].items():
            print(f"  {key}: {value}")
    
    def run_config_mode(self):
        """配置模式"""
        print("\n⚙️ 配置调整模式...")
        
        print("\n当前配置:")
        for key, value in self.config.items():
            if key not in ['auto_close_pool']:  # 跳过内部配置
                print(f"  {key}: {value}")
        
        print("\n可调整的配置项:")
        print("1. headless - 无头模式 (True/False)")
        print("2. max_workers - 并发线程数 (1-10)")
        print("3. pool_size - 连接池大小 (1-10)")
        print("4. batch_size - 批次大小 (10-500)")
        
        config_key = input("\n请输入要修改的配置项名称 (或回车跳过): ").strip()
        if not config_key:
            return
        
        if config_key not in ['headless', 'max_workers', 'pool_size', 'batch_size']:
            print("✗ 无效的配置项")
            return
        
        new_value = input(f"请输入新值 (当前: {self.config[config_key]}): ").strip()
        if not new_value:
            return
        
        try:
            if config_key == 'headless':
                self.config[config_key] = new_value.lower() in ['true', '1', 'yes', 'y']
            else:
                value = int(new_value)
                if config_key in ['max_workers', 'pool_size'] and not (1 <= value <= 10):
                    print("✗ 值必须在1-10之间")
                    return
                elif config_key == 'batch_size' and not (10 <= value <= 500):
                    print("✗ 值必须在10-500之间")
                    return
                self.config[config_key] = value
            
            print(f"✓ 配置已更新: {config_key} = {self.config[config_key]}")
            
        except ValueError:
            print("✗ 无效的值格式")
    
    def _create_scraper(self):
        """创建爬虫实例"""
        if self.scraper is None:
            print("正在初始化爬虫...")
            self.scraper = ProjectDetailScraperOptimized(
                headless=self.config["headless"],
                max_workers=self.config["max_workers"],
                output_dir=self.config["output_dir"],
                pool_size=self.config["pool_size"]
            )
            print("✓ 爬虫初始化完成")
    
    def _display_validation_result(self, stats: Dict):
        """显示验证结果"""
        print(f"\n🧪 验证结果:")
        session = stats['current_session']
        total = session['completed'] + session['failed']
        
        if total > 0:
            print(f"  成功抓取: {session['completed']}/{total}")
            print(f"  失败数量: {session['failed']}/{total}")
            print(f"  成功率: {session['success_rate']}%")
            
            if session['success_rate'] >= 80:
                print("  ✅ 验证通过 - 系统运行正常")
                print("  建议可以进行完整抓取")
            elif session['success_rate'] >= 50:
                print("  ⚠️  验证警告 - 成功率偏低")
                print("  建议检查网络连接和目标网站状态")
            else:
                print("  ❌ 验证失败 - 系统存在问题")
                print("  建议检查配置和网络环境")
        else:
            print("  ❌ 未处理任何URL")
    
    def cleanup(self):
        """清理资源"""
        if self.config.get("auto_close_pool", True):
            print("\n正在清理资源...")
            close_global_pool()
            print("✓ 资源清理完成")
    
    def run(self):
        """运行主程序"""
        try:
            # 显示横幅
            self.display_banner()
            
            # 检查前提条件
            if not self.check_prerequisites():
                return
            
            # 显示配置
            self.display_current_config()
            
            # 主循环
            while True:
                mode = self.get_run_mode()
                
                if mode == "1":
                    self.run_validation_mode()
                elif mode == "2":
                    self.run_full_mode()
                elif mode == "3":
                    self.run_custom_mode()
                elif mode == "4":
                    self.run_statistics_mode()
                elif mode == "5":
                    self.run_config_mode()
                    continue  # 配置后返回主菜单
                
                # 询问是否继续
                if input("\n是否继续其他操作? (y/N): ").strip().lower() not in ['y', 'yes']:
                    break
            
            print("\n👋 感谢使用数英网项目爬虫!")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断操作")
        except Exception as e:
            print(f"\n❌ 运行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()


def main():
    """主函数"""
    controller = ScraperController()
    controller.run()


if __name__ == "__main__":
    main() 