#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数英网项目详情爬虫 - 高并发版本
===============================================
功能特点：
  * 命令行参数控制，适合自动化脚本
  * 高并发多线程爬取，性能提升5-10倍
  * 智能配置预设(conservative/balanced/aggressive/extreme/auto)
  * 简洁高效，专注于爬取性能
  * 断点续传支持
  * 自动配置验证和性能优化

适用场景：
  ✓ 需要高速爬取的场景
  ✓ 脚本自动化调用
  ✓ 服务器环境批量处理
  ✓ 对性能要求较高的任务

使用方法：
  python scraper_parallel.py                    # 自动配置
  python scraper_parallel.py --preset balanced  # 均衡模式
  python scraper_parallel.py --max-workers 8    # 指定线程数
  python scraper_parallel.py --dry-run          # 测试配置

数据源：基于master_projects.csv (7000+项目)
输出：output/文件夹中的批次文件 + AI索引
"""

import os
import sys
import time
import argparse
from datetime import datetime

# 确保项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project_scraper_parallel import AdvancedProjectScraper
from batch_manager import BatchManager
from data_converter import DataConverter
from parallel_config import ParallelConfig
from driver_pool import close_global_pool


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='高并发网页爬虫工具')
    parser.add_argument('--preset', choices=['conservative', 'balanced', 'aggressive', 'extreme', 'auto'], 
                       default='auto', help='并发配置预设')
    parser.add_argument('--max-workers', type=int, help='最大并发线程数')
    parser.add_argument('--dry-run', action='store_true', help='只显示配置不执行爬取')
    
    args = parser.parse_args()
    
    print("高并发网页爬虫系统")
    print("=" * 50)
    
    try:
        # 1. 获取配置
        if args.preset == 'auto':
            config = ParallelConfig.get_auto_config()
        else:
            config = ParallelConfig.get_preset(args.preset)
        
        # 应用覆盖参数
        if args.max_workers:
            config['max_workers'] = args.max_workers
        
        # 2. 验证配置
        validation = ParallelConfig.validate_config(config)
        print(f"\n配置验证: {'通过' if validation['valid'] else '失败'}")
        
        if not validation['valid']:
            for issue in validation['issues']:
                print(f"  问题: {issue}")
            return
        
        # 显示配置
        print(f"\n配置信息:")
        print(f"  模式: {config['name']}")
        print(f"  线程数: {config['max_workers']}")
        print(f"  驱动池: {config['pool_size']}")
        print(f"  批次: {config['batch_size']}")
        
        if args.dry_run:
            print("\n模拟运行模式，不执行实际爬取")
            return
        
        # 3. 初始化批次管理
        print(f"\n初始化批次管理...")
        batch_manager = BatchManager()
        
        status = batch_manager.get_progress_summary()
        print(f"进度摘要:")
        print(f"  总项目: {status['total_projects']}")
        print(f"  已完成: {status['completed']}")
        print(f"  待处理: {status['pending']}")
        print(f"  当前批次: {status['current_batch']}/{status['total_batches']}")
        print(f"  完成率: {status['progress_rate']}%")
        
        if status['pending'] == 0:
            print("所有项目已完成!")
            return
        
        # 确认继续
        response = input(f"开始处理批次? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            return
        
        # 4. 创建爬虫
        print(f"\n创建高并发爬虫...")
        scraper = AdvancedProjectScraper(
            max_workers=config['max_workers'],
            pool_size=config['pool_size'],
            batch_size=config['batch_size'],
            headless=True,
            output_dir="output"
        )
        
        # 5. 执行爬取
        total_success = 0
        total_failed = 0
        batch_count = 0
        
        while True:
            batch_info = batch_manager.get_next_batch()
            if batch_info is None:
                break
            
            batch_count += 1
            print(f"\n处理批次 {batch_count}: {batch_info.batch_id}")
            print(f"  项目数量: {batch_info.project_count}")
            
            try:
                # 获取项目列表
                batch_projects = batch_manager.start_batch(batch_info)
                urls = [p['url'] for p in batch_projects]
                
                # 并发爬取
                results = scraper.scrape_projects_parallel(urls)
                
                # 完成批次
                batch_manager.complete_batch(batch_info, results['results'])
                
                total_success += len(results['results'])
                total_failed += len(results['failed_urls'])
                
                print(f"  批次完成: 成功{len(results['results'])} 失败{len(results['failed_urls'])}")
                
            except KeyboardInterrupt:
                print(f"\n用户中断")
                break
            except Exception as e:
                print(f"  批次失败: {e}")
                continue
        
        # 6. 生成AI数据
        print(f"\n生成AI兼容数据...")
        try:
            converter = DataConverter()
            if converter.convert_all():
                print("  AI数据生成成功")
        except Exception as e:
            print(f"  AI数据生成失败: {e}")
        
        # 7. 统计
        print(f"\n最终统计:")
        print(f"  成功: {total_success}")
        print(f"  失败: {total_failed}")
        if total_success + total_failed > 0:
            print(f"  成功率: {total_success/(total_success+total_failed)*100:.1f}%")
        
    except KeyboardInterrupt:
        print(f"\n程序被中断")
    except Exception as e:
        print(f"\n程序异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n清理资源...")
        close_global_pool()
        print("程序结束")


if __name__ == "__main__":
    main()