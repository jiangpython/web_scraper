#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次管理器 - 支持断点续传和状态跟踪
处理7000+项目的大规模爬取任务
"""

import os
import json
import pandas as pd
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

class ScrapeStatus(Enum):
    """爬取状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BatchInfo:
    """批次信息"""
    batch_id: str
    start_index: int
    end_index: int
    project_count: int
    status: ScrapeStatus
    created_at: str = ""
    completed_at: str = ""
    success_count: int = 0
    failed_count: int = 0
    
class BatchManager:
    """批次管理器 - 支持断点续传"""
    
    def __init__(self, master_csv="master_projects.csv", batch_size=50, output_dir="output"):
        self.master_csv = master_csv
        self.batch_size = batch_size
        self.output_dir = output_dir
        
        # 核心文件路径
        self.scraped_csv = "scraped_projects.csv"
        self.batch_status_file = os.path.join(output_dir, "batch_status.json")
        self.combined_json = os.path.join(output_dir, "combined_projects.json")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "details"), exist_ok=True)
        
        # 初始化状态
        self.master_projects = []
        self.scraped_df = None
        self.batch_status = {}
        
        # 加载数据
        self._load_master_projects()
        self._initialize_scraped_projects()
        self._load_batch_status()
    
    def _load_master_projects(self):
        """加载master项目数据"""
        if not os.path.exists(self.master_csv):
            raise FileNotFoundError(f"Master项目文件不存在: {self.master_csv}")
        
        df = pd.read_csv(self.master_csv)
        self.master_projects = df.to_dict('records')
        print(f"加载Master项目: {len(self.master_projects)} 个")
    
    def _initialize_scraped_projects(self):
        """初始化或加载爬取进度表"""
        if os.path.exists(self.scraped_csv):
            # 加载现有进度
            self.scraped_df = pd.read_csv(self.scraped_csv)
            print(f"加载现有进度: {len(self.scraped_df)} 个项目")
        else:
            # 创建新的进度表
            print("创建新的进度跟踪表...")
            scraped_data = []
            
            for i, project in enumerate(self.master_projects):
                scraped_data.append({
                    'project_id': project['project_id'],
                    'url': project['url'],
                    'scrape_status': ScrapeStatus.PENDING.value,
                    'batch_id': '',
                    'scraped_at': '',
                    'retry_count': 0,
                    'error_message': ''
                })
            
            self.scraped_df = pd.DataFrame(scraped_data)
            self.scraped_df.to_csv(self.scraped_csv, index=False, encoding='utf-8-sig')
            print(f"创建进度表: {len(scraped_data)} 个项目")
    
    def _load_batch_status(self):
        """加载批次状态"""
        if os.path.exists(self.batch_status_file):
            with open(self.batch_status_file, 'r', encoding='utf-8') as f:
                self.batch_status = json.load(f)
            print(f"加载批次状态: 当前批次 {self.batch_status.get('current_batch', 1)}")
        else:
            # 初始化批次状态
            total_projects = len(self.master_projects)
            total_batches = (total_projects + self.batch_size - 1) // self.batch_size
            
            self.batch_status = {
                'current_batch': 1,
                'total_batches': total_batches,
                'total_projects': total_projects,
                'completed_batches': [],
                'failed_batches': [],
                'last_update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'batch_size': self.batch_size
            }
            self._save_batch_status()
            print(f"初始化批次状态: 总共 {total_batches} 个批次")
    
    def _save_batch_status(self):
        """保存批次状态"""
        self.batch_status['last_update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.batch_status_file, 'w', encoding='utf-8') as f:
            json.dump(self.batch_status, f, ensure_ascii=False, indent=2)
    
    def get_progress_summary(self) -> Dict:
        """获取进度摘要"""
        status_counts = self.scraped_df['scrape_status'].value_counts().to_dict()
        
        pending_count = status_counts.get(ScrapeStatus.PENDING.value, 0)
        completed_count = status_counts.get(ScrapeStatus.COMPLETED.value, 0)
        failed_count = status_counts.get(ScrapeStatus.FAILED.value, 0)
        processing_count = status_counts.get(ScrapeStatus.PROCESSING.value, 0)
        
        total_projects = len(self.master_projects)
        progress_rate = (completed_count / total_projects * 100) if total_projects > 0 else 0
        
        return {
            'total_projects': total_projects,
            'completed': completed_count,
            'failed': failed_count,
            'pending': pending_count,
            'processing': processing_count,
            'progress_rate': round(progress_rate, 2),
            'current_batch': self.batch_status.get('current_batch', 1),
            'total_batches': self.batch_status.get('total_batches', 0),
            'completed_batches': len(self.batch_status.get('completed_batches', [])),
            'estimated_remaining_time': self._estimate_remaining_time()
        }
    
    def _estimate_remaining_time(self) -> str:
        """估算剩余时间"""
        completed_batches = len(self.batch_status.get('completed_batches', []))
        total_batches = self.batch_status.get('total_batches', 0)
        
        if completed_batches == 0:
            return "未知"
        
        # 假设每个批次平均需要30分钟
        avg_time_per_batch = 30  # 分钟
        remaining_batches = total_batches - completed_batches
        remaining_minutes = remaining_batches * avg_time_per_batch
        
        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60
        
        if hours > 24:
            days = hours // 24
            hours = hours % 24
            return f"约 {days} 天 {hours} 小时"
        elif hours > 0:
            return f"约 {hours} 小时 {minutes} 分钟"
        else:
            return f"约 {minutes} 分钟"
    
    def get_next_batch(self) -> Optional[BatchInfo]:
        """获取下一个待处理批次"""
        current_batch = self.batch_status['current_batch']
        total_batches = self.batch_status['total_batches']
        
        if current_batch > total_batches:
            return None  # 所有批次已完成
        
        # 计算批次范围
        start_index = (current_batch - 1) * self.batch_size
        end_index = min(start_index + self.batch_size, len(self.master_projects))
        project_count = end_index - start_index
        
        batch_info = BatchInfo(
            batch_id=f"{current_batch:03d}",
            start_index=start_index,
            end_index=end_index,
            project_count=project_count,
            status=ScrapeStatus.PENDING,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return batch_info
    
    def start_batch(self, batch_info: BatchInfo) -> List[Dict]:
        """开始处理批次，返回批次中的项目列表"""
        print(f"开始批次 {batch_info.batch_id}: 项目 {batch_info.start_index+1}-{batch_info.end_index}")
        
        # 获取批次项目
        batch_projects = self.master_projects[batch_info.start_index:batch_info.end_index]
        
        # 更新项目状态为PROCESSING
        project_ids = [p['project_id'] for p in batch_projects]
        mask = self.scraped_df['project_id'].isin(project_ids)
        self.scraped_df.loc[mask, 'scrape_status'] = ScrapeStatus.PROCESSING.value
        self.scraped_df.loc[mask, 'batch_id'] = batch_info.batch_id
        
        # 保存进度
        self.scraped_df.to_csv(self.scraped_csv, index=False, encoding='utf-8-sig')
        
        return batch_projects
    
    def complete_project(self, project_id: str, success: bool, scraped_data: Dict = None, error_message: str = ""):
        """完成单个项目的处理"""
        mask = self.scraped_df['project_id'] == project_id
        
        if success:
            self.scraped_df.loc[mask, 'scrape_status'] = ScrapeStatus.COMPLETED.value
            self.scraped_df.loc[mask, 'scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.scraped_df.loc[mask, 'error_message'] = ''
        else:
            self.scraped_df.loc[mask, 'scrape_status'] = ScrapeStatus.FAILED.value
            self.scraped_df.loc[mask, 'retry_count'] = self.scraped_df.loc[mask, 'retry_count'] + 1
            self.scraped_df.loc[mask, 'error_message'] = error_message
        
        # 实时保存进度
        self.scraped_df.to_csv(self.scraped_csv, index=False, encoding='utf-8-sig')
    
    def complete_batch(self, batch_info: BatchInfo, batch_results: List[Dict]):
        """完成批次处理"""
        # 保存批次详细数据
        batch_file = os.path.join(self.output_dir, "details", f"batch_{batch_info.batch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # 修复：手动转换枚举为字符串，确保JSON可序列化
        batch_info_dict = asdict(batch_info)
        batch_info_dict['status'] = batch_info.status.value  # 转换枚举为字符串值
        
        batch_data = {
            'batch_info': batch_info_dict,
            'projects': batch_results,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(batch_file), exist_ok=True)
        
        try:
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, ensure_ascii=False, indent=2)
            print(f"✓ 批次数据已保存: {batch_file}")
        except Exception as e:
            print(f"❌ 保存批次数据失败: {e}")
            raise
        
        # 更新批次状态
        self.batch_status['completed_batches'].append(batch_info.batch_id)
        self.batch_status['current_batch'] += 1
        self._save_batch_status()
        
        print(f"批次 {batch_info.batch_id} 完成: 成功 {batch_info.success_count}, 失败 {batch_info.failed_count}")
        
        # 定期合并数据（每5个批次）
        if len(self.batch_status['completed_batches']) % 5 == 0:
            self._merge_completed_data()
    
    def _merge_completed_data(self):
        """合并已完成的数据"""
        print("合并已完成的批次数据...")
        
        # 读取所有已完成的批次文件
        combined_data = []
        details_dir = os.path.join(self.output_dir, "details")
        
        for batch_id in self.batch_status['completed_batches']:
            batch_files = [f for f in os.listdir(details_dir) if f.startswith(f"batch_{batch_id}_")]
            
            if batch_files:
                batch_file = os.path.join(details_dir, batch_files[-1])  # 取最新文件
                try:
                    with open(batch_file, 'r', encoding='utf-8') as f:
                        batch_data = json.load(f)
                    combined_data.extend(batch_data.get('projects', []))
                except Exception as e:
                    print(f"读取批次文件失败: {batch_file}, 错误: {e}")
        
        # 与master数据合并
        final_data = []
        for master_project in self.master_projects:
            project_id = master_project['project_id']
            
            # 查找对应的爬取数据
            scraped_project = next((p for p in combined_data if p.get('id') == project_id), None)
            
            # 合并数据
            merged_project = {
                'id': project_id,
                'url': master_project['url'],
                'title': master_project['title'],
                'brand': master_project['brand'],  # 来自Excel，准确
                'agency': master_project['agency'],  # 来自Excel，准确
                'publish_date': master_project.get('publish_date', ''),
                'last_updated': master_project.get('last_updated', '')
            }
            
            # 添加爬取的网页内容
            if scraped_project:
                merged_project.update({
                    'description': scraped_project.get('description', ''),
                    'images': scraped_project.get('images', []),
                    'category': scraped_project.get('category', ''),
                    'keywords': scraped_project.get('keywords', []),
                    'industry': scraped_project.get('industry', ''),
                    'campaign_type': scraped_project.get('campaign_type', ''),
                    'project_info': scraped_project.get('project_info', {})
                })
            
            final_data.append(merged_project)
        
        # 保存合并数据
        with open(self.combined_json, 'w', encoding='utf-8') as f:
            json.dump({
                'total_projects': len(final_data),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'projects': final_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"数据合并完成: {len(final_data)} 个项目")
    
    def get_failed_projects(self) -> List[Dict]:
        """获取失败的项目列表，用于重试"""
        failed_df = self.scraped_df[self.scraped_df['scrape_status'] == ScrapeStatus.FAILED.value]
        failed_projects = []
        
        for _, row in failed_df.iterrows():
            project_id = row['project_id']
            master_project = next((p for p in self.master_projects if p['project_id'] == project_id), None)
            if master_project:
                failed_projects.append({
                    **master_project,
                    'retry_count': row['retry_count'],
                    'error_message': row['error_message']
                })
        
        return failed_projects
    
    def reset_failed_projects(self):
        """重置失败项目状态，准备重试"""
        mask = self.scraped_df['scrape_status'] == ScrapeStatus.FAILED.value
        self.scraped_df.loc[mask, 'scrape_status'] = ScrapeStatus.PENDING.value
        self.scraped_df.loc[mask, 'batch_id'] = ''
        self.scraped_df.loc[mask, 'error_message'] = ''
        
        self.scraped_df.to_csv(self.scraped_csv, index=False, encoding='utf-8-sig')
        print("已重置失败项目状态")
    
    def display_progress(self):
        """显示进度信息"""
        progress = self.get_progress_summary()
        
        print("\n" + "="*60)
        print("           批次管理器 - 进度报告")
        print("="*60)
        print(f"总项目数:     {progress['total_projects']:,}")
        print(f"已完成:       {progress['completed']:,} ({progress['progress_rate']:.1f}%)")
        print(f"失败:         {progress['failed']:,}")
        print(f"待处理:       {progress['pending']:,}")
        print(f"处理中:       {progress['processing']:,}")
        print("-"*60)
        print(f"当前批次:     {progress['current_batch']}/{progress['total_batches']}")
        print(f"已完成批次:   {progress['completed_batches']}")
        print(f"预计剩余时间: {progress['estimated_remaining_time']}")
        print("="*60)

def main():
    """测试主函数"""
    try:
        manager = BatchManager()
        manager.display_progress()
        
        # 显示下一个批次信息
        next_batch = manager.get_next_batch()
        if next_batch:
            print(f"\n下一个批次: {next_batch.batch_id}")
            print(f"包含项目: {next_batch.project_count} 个")
        else:
            print("\n所有批次已完成！")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()