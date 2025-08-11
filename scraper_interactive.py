#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数英网项目详情爬虫 - 交互式版本
===============================================
功能特点：
  * 交互式用户界面，提供6个操作选项
  * 断点续传 - 支持从任意位置中断恢复
  * 智能数据整合 - 自动分析Excel数据源
  * 实时进度跟踪 - 精确显示完成进度
  * 单线程稳定爬取 - 适合长期运行
  * AI系统兼容 - 自动生成索引文件

适用场景：
  ✓ 需要交互式控制的场景
  ✓ 长期稳定的大规模爬取
  ✓ 需要详细进度监控
  ✓ 初次使用或调试

使用方法：
  python scraper_interactive.py
  
数据源：基于master_projects.csv (7000+项目)
输出：output/文件夹中的批次文件 + AI索引
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入核心组件
from batch_manager import BatchManager, BatchInfo, ScrapeStatus
from project_scraper_enhanced import ProjectDetailScraperEnhanced
from digitaling_parser_enhanced import DigitalingEnhancedParser
from driver_pool import get_global_pool, close_global_pool
from data_converter import DataConverter
from excel_integrator import ExcelIntegrator
from config_optimized import SCRAPER_CONFIG

class EnhancedScraperV3:
    """增强版爬虫v3 - 支持大规模爬取和断点续传"""
    
    def __init__(self, batch_size=50):
        self.batch_size = batch_size
        
        # 在初始化之前先进行数据源分析和整合
        self._auto_integrate_data_sources()
        
        # 初始化组件
        self.batch_manager = BatchManager(batch_size=batch_size)
        self.data_converter = DataConverter()
        self.scraper = None
        
        # 统计信息
        self.session_stats = {
            'start_time': datetime.now(),
            'batches_processed': 0,
            'projects_completed': 0,
            'projects_failed': 0,
            'total_time_seconds': 0
        }
    
    def display_banner(self):
        """显示启动横幅"""
        print("=" * 70)
        print("        数英网项目详情爬虫 - 增强版 v3.0")
        print("=" * 70)
        print("核心特性:")
        print("  * 基于 master_projects.csv 的7000+项目爬取")
        print("  * 断点续传 - 任何时候中断都能从断点继续")
        print("  * 实时进度跟踪 - 精确知道爬了多少还剩多少")
        print("  * 智能数据合并 - Excel准确信息+网页丰富内容")
        print("  * AI系统兼容 - 自动生成索引文件")
        print("  * 批次调度优化 - 支持2天长时间执行")
        print("=" * 70)
        print("相比v2的改进:")
        print("  + 数据源统一: 基于 master_projects.csv")
        print("  + 断点续传: 支持任意位置中断恢复")
        print("  + 进度可视化: 实时显示完成进度和预估时间")
        print("  + 数据准确性: Excel + 网页内容完美结合")
        print("  + 一键式操作: 自动数据源分析和整合")
        print("=" * 70)
    
    def show_current_progress(self):
        """显示当前进度"""
        self.batch_manager.display_progress()
        
        # 显示本次会话统计
        if self.session_stats['batches_processed'] > 0:
            print(f"\n本次会话统计:")
            print(f"  已处理批次: {self.session_stats['batches_processed']}")
            print(f"  成功项目: {self.session_stats['projects_completed']}")
            print(f"  失败项目: {self.session_stats['projects_failed']}")
            elapsed = (datetime.now() - self.session_stats['start_time']).total_seconds()
            print(f"  运行时间: {int(elapsed//3600)}小时{int((elapsed%3600)//60)}分钟")
    
    def get_operation_mode(self) -> str:
        """获取操作模式"""
        print("\n请选择操作模式:")
        print("1. 继续爬取 (从断点继续)")
        print("2. 重新开始 (清空进度重新开始)")
        print("3. 只处理失败项目 (重试失败的项目)")
        print("4. 查看详细进度")
        print("5. 数据转换 (生成AI索引文件)")
        print("6. 退出")
        
        while True:
            choice = input("\n请输入选择 (1-6): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6']:
                return choice
            print("无效选择，请输入1-6之间的数字")
    
    def continue_scraping(self):
        """继续爬取 - 从断点开始"""
        print("\n从断点继续爬取...")
        
        # 显示当前进度
        progress = self.batch_manager.get_progress_summary()
        if progress['progress_rate'] >= 100:
            print("所有项目已完成爬取！")
            return
        
        print(f"当前进度: {progress['progress_rate']:.1f}% ({progress['completed']}/{progress['total_projects']})")
        print(f"预计剩余时间: {progress['estimated_remaining_time']}")
        
        confirm = input("\n确认开始爬取? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            return
        
        self._run_scraping_loop()
    
    def restart_scraping(self):
        """重新开始爬取"""
        print("\n警告：重新开始将清空所有进度数据！")
        confirm = input("确认重新开始? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            return
        
        # 清理现有进度文件
        files_to_remove = [
            'scraped_projects.csv',
            'output/batch_status.json',
            'output/combined_projects.json'
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"删除: {file_path}")
        
        # 重新初始化批次管理器
        self.batch_manager = BatchManager(batch_size=self.batch_size)
        print("✓ 进度数据已清空，重新开始...")
        
        self._run_scraping_loop()
    
    def retry_failed_projects(self):
        """重试失败的项目"""
        failed_projects = self.batch_manager.get_failed_projects()
        
        if not failed_projects:
            print("没有失败的项目需要重试")
            return
        
        print(f"\n发现 {len(failed_projects)} 个失败项目:")
        for project in failed_projects[:5]:  # 显示前5个
            print(f"  • {project['title'][:50]}... (重试次数: {project['retry_count']})")
        
        if len(failed_projects) > 5:
            print(f"  ... 还有 {len(failed_projects)-5} 个失败项目")
        
        confirm = input(f"\n确认重试这 {len(failed_projects)} 个失败项目? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            return
        
        # 重置失败项目状态
        self.batch_manager.reset_failed_projects()
        
        # 继续正常的爬取流程
        self._run_scraping_loop()
    
    def show_detailed_progress(self):
        """显示详细进度"""
        self.show_current_progress()
        
        # 显示失败项目详情
        failed_projects = self.batch_manager.get_failed_projects()
        if failed_projects:
            print(f"\n🔴 失败项目详情 (前10个):")
            for i, project in enumerate(failed_projects[:10], 1):
                print(f"{i:2d}. {project['title'][:40]}...")
                print(f"     错误: {project['error_message'][:60]}")
                print(f"     重试次数: {project['retry_count']}")
    
    def convert_data(self):
        """数据转换 - 生成AI索引文件"""
        print("\n数据转换...")
        
        # 检查是否有合并数据
        combined_file = "output/combined_projects.json"
        if not os.path.exists(combined_file):
            print(f"没有找到合并数据文件: {combined_file}")
            print("请先完成一些批次的爬取")
            return
        
        success = self.data_converter.convert_all()
        if success:
            print("✓ 数据转换完成，AI系统可以使用新的索引文件")
        else:
            print("✗ 数据转换失败")
    
    def _run_scraping_loop(self):
        """运行爬取循环"""
        try:
            # 初始化爬虫
            self._initialize_scraper()
            
            print(f"\n开始批次爬取循环...")
            batch_count = 0
            
            while True:
                # 获取下一个批次
                batch_info = self.batch_manager.get_next_batch()
                if not batch_info:
                    print("\n所有批次已完成！")
                    break
                
                print(f"\n{'='*60}")
                print(f"开始处理批次 {batch_info.batch_id}")
                print(f"项目范围: {batch_info.start_index+1}-{batch_info.end_index}")
                print('='*60)
                
                # 处理批次
                success = self._process_batch(batch_info)
                
                if success:
                    self.session_stats['batches_processed'] += 1
                    batch_count += 1
                    
                    # 每处理5个批次后进行数据转换
                    if batch_count % 5 == 0:
                        print(f"\n已完成 {batch_count} 个批次，进行数据转换...")
                        self.data_converter.convert_all()
                
                # 显示进度
                self.show_current_progress()
                
                # 批次间休息
                print(f"\n等待30秒后继续下一批次...")
                time.sleep(30)
            
            # 最终数据转换和完整性检查
            print(f"\n执行最终数据转换和索引生成...")
            self._final_data_integration()
            
            print(f"\n爬取任务完成！")
            self._display_final_summary()
            
        except KeyboardInterrupt:
            print(f"\n\n用户中断操作")
            print(f"进度已自动保存，下次启动时可以继续")
        except Exception as e:
            print(f"\n运行出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.scraper:
                close_global_pool()
    
    def _initialize_scraper(self):
        """初始化爬虫组件"""
        if self.scraper is None:
            print("初始化爬虫组件...")
            self.scraper = ProjectDetailScraperEnhanced(
                headless=True,
                max_workers=2,
                output_dir="output",
                pool_size=3
            )
            print("✓ 爬虫组件初始化完成")
    
    def _process_batch(self, batch_info: BatchInfo) -> bool:
        """处理单个批次"""
        try:
            # 开始批次
            batch_projects = self.batch_manager.start_batch(batch_info)
            
            # 转换为爬虫需要的URL格式
            urls = [project['url'] for project in batch_projects]
            
            # 执行批次爬取
            batch_results = []
            success_count = 0
            failed_count = 0
            
            print(f"开始爬取 {len(urls)} 个项目...")
            
            # 使用现有的scraper逻辑
            for i, project in enumerate(batch_projects, 1):
                project_id = project['project_id']
                url = project['url']
                
                print(f"  处理项目 {i}/{len(batch_projects)}: {project_id}")
                
                try:
                    # 爬取单个项目（复用现有逻辑）
                    scraped_data = self._scrape_single_project(url, project)
                    
                    if scraped_data:
                        batch_results.append(scraped_data)
                        self.batch_manager.complete_project(project_id, True)
                        success_count += 1
                        self.session_stats['projects_completed'] += 1
                    else:
                        self.batch_manager.complete_project(project_id, False, error_message="数据提取失败")
                        failed_count += 1
                        self.session_stats['projects_failed'] += 1
                
                except Exception as e:
                    error_msg = str(e)[:100]
                    self.batch_manager.complete_project(project_id, False, error_message=error_msg)
                    failed_count += 1
                    self.session_stats['projects_failed'] += 1
                    print(f"    错误: {error_msg}")
                
                # 项目间小延迟
                time.sleep(2)
            
            # 完成批次
            batch_info.success_count = success_count
            batch_info.failed_count = failed_count
            batch_info.completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.batch_manager.complete_batch(batch_info, batch_results)
            
            print(f"批次 {batch_info.batch_id} 完成: 成功 {success_count}, 失败 {failed_count}")
            return True
            
        except Exception as e:
            print(f"批次处理失败: {e}")
            return False
    
    def _scrape_single_project(self, url: str, master_project: Dict) -> Optional[Dict]:
        """爬取单个项目 - 复用现有解析逻辑"""
        try:
            # 获取WebDriver
            driver_pool = get_global_pool()
            driver = driver_pool.get_driver()
            
            try:
                # 访问页面
                driver.get(url)
                time.sleep(3)
                
                # 使用增强解析器
                parser = DigitalingEnhancedParser(driver)
                
                # 提取项目信息
                project_data = parser.parse_project_detail(url)
                
                if project_data:
                    # 合并master数据和爬取数据
                    final_data = {
                        'id': master_project['project_id'],
                        'url': url,
                        'title': master_project['title'],
                        'brand': master_project['brand'],  # 来自Excel
                        'agency': master_project['agency'],  # 来自Excel
                        'publish_date': master_project.get('publish_date', ''),
                        'description': project_data.get('description', ''),
                        'images': project_data.get('images', []),
                        'category': project_data.get('category', ''),
                        'keywords': project_data.get('keywords', []),
                        'industry': project_data.get('industry', ''),
                        'campaign_type': project_data.get('campaign_type', ''),
                        'project_info': project_data.get('project_info', {})
                    }
                    
                    return final_data
                
            finally:
                driver_pool.return_driver(driver)
                
        except Exception as e:
            print(f"爬取项目失败 {url}: {e}")
        
        return None
    
    def _display_final_summary(self):
        """显示最终总结"""
        elapsed = (datetime.now() - self.session_stats['start_time']).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"           最终统计报告")
        print(f"{'='*60}")
        print(f"本次会话:")
        print(f"  处理批次: {self.session_stats['batches_processed']}")
        print(f"  成功项目: {self.session_stats['projects_completed']}")
        print(f"  失败项目: {self.session_stats['projects_failed']}")
        print(f"  总运行时间: {int(elapsed//3600)}小时{int((elapsed%3600)//60)}分钟")
        
        # 显示总体进度
        progress = self.batch_manager.get_progress_summary()
        print(f"\n总体进度:")
        print(f"  完成率: {progress['progress_rate']:.1f}%")
        print(f"  已完成: {progress['completed']:,} 项目")
        print(f"  待处理: {progress['pending']:,} 项目")
        print("="*60)
    
    def _auto_integrate_data_sources(self):
        """自动分析data文件夹中的数据源并整合"""
        print("\n" + "="*60)
        print("           自动数据源分析和整合")
        print("="*60)
        
        # 1. 检查data文件夹中的Excel文件
        data_dir = "data"
        excel_files = []
        
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.xlsx') and not file.startswith('~$'):
                    excel_files.append(file)
        
        print(f"发现Excel文件: {len(excel_files)} 个")
        for file in excel_files:
            print(f"  * {file}")
        
        if not excel_files:
            print("警告: 没有发现Excel数据文件")
            print("请将Excel文件放入data/文件夹中")
            return
        
        # 2. 检查是否需要重新整合
        master_file = "master_projects.csv"
        need_update = False
        
        if not os.path.exists(master_file):
            print(f"\n未找到 {master_file}，需要创建")
            need_update = True
        else:
            # 检查master文件是否比Excel文件旧
            master_time = os.path.getmtime(master_file)
            
            for excel_file in excel_files:
                excel_path = os.path.join(data_dir, excel_file)
                excel_time = os.path.getmtime(excel_path)
                
                if excel_time > master_time:
                    print(f"\n发现更新的Excel文件: {excel_file}")
                    need_update = True
                    break
        
        # 3. 如果需要，执行数据整合
        if need_update:
            print(f"\n开始自动数据整合...")
            try:
                integrator = ExcelIntegrator()
                success = integrator.run()
                
                if success:
                    print("* 数据整合完成")
                else:
                    print("* 数据整合失败，请检查Excel文件格式")
                    
            except Exception as e:
                print(f"* 数据整合出错: {e}")
        else:
            print(f"\n数据源已是最新，无需重新整合")
        
        # 4. 显示最终数据源状态
        if os.path.exists(master_file):
            import pandas as pd
            df = pd.read_csv(master_file)
            print(f"\n最终数据源状态:")
            print(f"  * master_projects.csv: {len(df):,} 个项目")
            print(f"  * 数据源: data文件夹中的 {len(excel_files)} 个Excel文件")
            
        print("="*60)
    
    def _final_data_integration(self):
        """最终数据整合 - 生成完整的JSON数据表"""
        print("\n执行最终数据整合...")
        
        try:
            # 1. 强制合并所有批次数据
            print("1. 合并所有批次数据...")
            if hasattr(self.batch_manager, '_merge_completed_data'):
                self.batch_manager._merge_completed_data()
            
            # 2. 转换为AI兼容格式
            print("2. 生成AI兼容的JSON格式...")
            conversion_success = self.data_converter.convert_all()
            
            if conversion_success:
                print("* projects_index.json 已生成")
                print("* global_search_index.json 已生成")
            
            # 3. 数据质量报告
            print("3. 数据质量检查...")
            self._generate_data_quality_report()
            
            print("\n一键式数据整合完成！")
            print("* 数据已准备就绪，AI系统可以直接使用")
            
        except Exception as e:
            print(f"最终数据整合出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_data_quality_report(self):
        """生成数据质量报告"""
        try:
            # 检查最终生成的文件
            files_to_check = {
                'output/projects_index.json': 'AI项目索引',
                'output/global_search_index.json': '全局搜索索引',
                'output/combined_projects.json': '合并项目数据'
            }
            
            print("最终数据文件状态:")
            total_projects = 0
            
            for file_path, desc in files_to_check.items():
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  * {desc}: {size/1024:.1f}KB")
                    
                    # 获取项目数量
                    if 'projects_index.json' in file_path:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            total_projects = data.get('total_projects', 0)
                else:
                    print(f"  * {desc}: 未生成")
            
            if total_projects > 0:
                print(f"\n数据整合摘要:")
                print(f"  * 总项目数: {total_projects:,}")
                print(f"  * 数据格式: AI系统兼容")
                print(f"  * 状态: 准备就绪")
                
        except Exception as e:
            print(f"数据质量检查出错: {e}")
    
    def run(self):
        """运行主程序"""
        try:
            self.display_banner()
            self.show_current_progress()
            
            while True:
                mode = self.get_operation_mode()
                
                if mode == "1":
                    self.continue_scraping()
                elif mode == "2":
                    self.restart_scraping()
                elif mode == "3":
                    self.retry_failed_projects()
                elif mode == "4":
                    self.show_detailed_progress()
                elif mode == "5":
                    self.convert_data()
                elif mode == "6":
                    print("退出程序")
                    break
                
                if mode not in ["4", "5", "6"]:  # 非查看类操作后询问是否继续
                    if input("\n继续其他操作? (y/N): ").strip().lower() not in ['y', 'yes']:
                        break
            
            print("\n感谢使用增强版爬虫v3!")
            
        except Exception as e:
            print(f"\n程序出错: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    scraper = EnhancedScraperV3()
    scraper.run()

if __name__ == "__main__":
    main()