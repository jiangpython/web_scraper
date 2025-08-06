"""
增强版项目详情页爬虫
支持完整信息提取，去除不需要的字段
"""

import json
import time
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from driver_pool import get_global_pool, close_global_pool
from digitaling_parser_enhanced import DigitalingEnhancedParser
from config_optimized import SCRAPER_CONFIG, DELAY_CONFIG, EXTRACTION_CONFIG, FILE_PATHS


@dataclass
class ProjectInfo:
    """简化的项目信息数据结构"""
    id: str
    url: str
    title: str
    brand: str = ""
    agency: str = ""
    publish_date: str = ""
    description: str = ""
    category: str = ""
    images: List[str] = None
    project_info: Dict[str, str] = None  # 项目信息区域的其他信息
    scraped_at: str = ""
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.project_info is None:
            self.project_info = {}
        if not self.scraped_at:
            self.scraped_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@dataclass
class BatchInfo:
    """批次信息"""
    batch_id: str
    start_time: str
    end_time: str = ""
    total_projects: int = 0
    success_count: int = 0
    error_count: int = 0
    failed_urls: List[str] = None
    
    def __post_init__(self):
        if self.failed_urls is None:
            self.failed_urls = []


class ProjectDetailScraperEnhanced:
    """增强版项目详情页爬虫"""
    
    def __init__(self, headless=True, max_workers=3, output_dir="output", pool_size=None):
        """
        初始化爬虫
        
        Args:
            headless: 是否无头模式
            max_workers: 最大并发线程数
            output_dir: 输出目录
            pool_size: WebDriver连接池大小，None则使用max_workers
        """
        self.headless = headless
        self.max_workers = max_workers
        self.output_dir = output_dir
        self.pool_size = pool_size or max_workers
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "details"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "logs"), exist_ok=True)
        
        # 配置文件路径
        self.summary_file = os.path.join(output_dir, "projects_summary.json")
        self.metadata_file = os.path.join(output_dir, "metadata.json")
        self.progress_file = os.path.join(output_dir, "scrape_progress.json")
        
        # 统计信息
        self.total_projects = 0
        self.completed_projects = 0
        self.failed_projects = 0
        
        # 批次信息
        self.current_batch = None
        self.batch_size = SCRAPER_CONFIG.get("batch_size", 100)
        
        # 线程锁
        self.stats_lock = threading.Lock()
        
        # 获取全局WebDriver连接池
        self.driver_pool = get_global_pool(
            pool_size=self.pool_size, 
            headless=self.headless
        )
    
    def scrape_project_detail(self, url: str) -> Optional[ProjectInfo]:
        """
        抓取单个项目详情（使用连接池和增强解析器）
        
        Args:
            url: 项目详情页URL
            
        Returns:
            项目信息或None
        """
        try:
            # 从连接池获取WebDriver
            with self.driver_pool.get_driver() as driver:
                # 创建增强解析器实例
                parser = DigitalingEnhancedParser(driver)
                
                # 解析项目详情
                project_data = parser.parse_project_detail(url)
                
                if not project_data:
                    return None
                
                # 从project_info中提取字段，如果主字段为空的话
                project_info_data = project_data.get('project_info', {})
                
                # 创建ProjectInfo对象
                project = ProjectInfo(
                    id=project_data['id'],
                    url=project_data['url'],
                    title=project_data['title'],
                    brand=project_data.get('brand') or project_info_data.get('brand', ''),
                    agency=project_data.get('agency') or project_info_data.get('agency', ''),
                    publish_date=project_data.get('publish_date') or project_info_data.get('publish_date', ''),
                    description=project_data.get('description', ''),
                    category=project_info_data.get('category', ''),
                    images=project_data.get('images', []),
                    project_info=project_info_data  # 保存完整的项目信息区域数据
                )
                
                return project
                
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            return None
    
    def load_urls_from_file(self, filename: str) -> List[str]:
        """从文件加载URL列表"""
        urls = []
        
        if not os.path.exists(filename):
            print(f"文件不存在: {filename}")
            return urls
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
        
        print(f"从 {filename} 加载了 {len(urls)} 个URL")
        return urls
    
    def load_existing_summary(self) -> dict:
        """加载现有的汇总信息"""
        if os.path.exists(self.summary_file):
            try:
                with open(self.summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                print(f"加载现有汇总信息: {len(summary.get('projects', []))} 个项目")
                return summary
            except Exception as e:
                print(f"加载现有汇总信息失败: {e}")
        
        return {
            "total_projects": 0,
            "total_batches": 0,
            "last_updated": "",
            "projects": []
        }
    
    def get_existing_urls(self) -> set:
        """获取已抓取的URL集合"""
        summary = self.load_existing_summary()
        existing_urls = set()
        
        for project in summary.get('projects', []):
            if 'url' in project:
                existing_urls.add(project['url'])
        
        print(f"已抓取 {len(existing_urls)} 个URL")
        return existing_urls
    
    def filter_new_urls(self, urls: List[str]) -> List[str]:
        """过滤出新的URL"""
        existing_urls = self.get_existing_urls()
        new_urls = [url for url in urls if url not in existing_urls]
        
        skipped_count = len(urls) - len(new_urls)
        if skipped_count > 0:
            print(f"跳过 {skipped_count} 个已抓取的URL")
        
        return new_urls
    
    def save_batch_data(self, batch_info: BatchInfo, projects: List[ProjectInfo]):
        """保存批次数据（增量保存）"""
        # 生成唯一的批次文件名（使用时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_file = os.path.join(self.output_dir, "details", f"projects_batch_{batch_info.batch_id}_{timestamp}.json")
        
        batch_data = {
            "batch_info": asdict(batch_info),
            "projects": [asdict(project) for project in projects]
        }
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        
        print(f"批次数据已保存: {batch_file}")
        
        # 同时更新批次索引文件
        self.update_batch_index(batch_info.batch_id, batch_file, len(projects))
    
    def update_batch_index(self, batch_id: str, batch_file: str, project_count: int):
        """更新批次索引文件"""
        index_file = os.path.join(self.output_dir, "details", "batch_index.json")
        
        # 加载现有索引
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            except:
                index_data = {"batches": []}
        else:
            index_data = {"batches": []}
        
        # 添加新批次信息
        batch_info = {
            "batch_id": batch_id,
            "file_path": os.path.basename(batch_file),
            "project_count": project_count,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 检查是否已存在相同batch_id的记录，如果存在则更新
        existing_batch = None
        for i, batch in enumerate(index_data["batches"]):
            if batch["batch_id"] == batch_id:
                existing_batch = i
                break
        
        if existing_batch is not None:
            index_data["batches"][existing_batch] = batch_info
        else:
            index_data["batches"].append(batch_info)
        
        # 保存索引文件
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"批次索引已更新: {index_file}")
    
    def update_summary(self, new_projects: List[ProjectInfo]):
        """更新汇总信息（合并现有数据）"""
        # 加载现有汇总信息
        existing_summary = self.load_existing_summary()
        existing_projects = existing_summary.get('projects', [])
        
        # 创建现有项目的URL集合，用于去重
        existing_urls = {p.get('url', '') for p in existing_projects}
        
        # 添加新项目（去重）
        added_count = 0
        for project in new_projects:
            if project.url not in existing_urls:
                project_summary = {
                    "id": project.id,
                    "url": project.url,
                    "title": project.title,
                    "brand": project.brand,
                    "agency": project.agency,
                    "publish_date": project.publish_date,
                    "category": project.category,
                    "description": project.description[:200] + "..." if len(project.description) > 200 else project.description,  # 摘要
                    "image_count": len(project.images),
                    "batch_id": project.scraped_at.split(' ')[0].replace('-', ''),
                    "scraped_at": project.scraped_at
                }
                existing_projects.append(project_summary)
                existing_urls.add(project.url)
                added_count += 1
        
        # 更新汇总信息
        summary_data = {
            "total_projects": len(existing_projects),
            "total_batches": (len(existing_projects) + self.batch_size - 1) // self.batch_size,
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "scraper_config": {
                "headless": self.headless,
                "max_workers": self.max_workers,
                "pool_size": self.pool_size,
                "batch_size": self.batch_size,
                "version": "enhanced-2.0"
            },
            "projects": existing_projects
        }
        
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"汇总信息已更新: {self.summary_file}")
        print(f"  - 新增 {added_count} 个项目")
        print(f"  - 总计 {len(existing_projects)} 个项目")
    
    def scrape_batch(self, urls: List[str], batch_id: str) -> Tuple[BatchInfo, List[ProjectInfo]]:
        """抓取一个批次的项目"""
        batch_info = BatchInfo(
            batch_id=batch_id,
            start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_projects=len(urls)
        )
        
        projects = []
        
        # 显示连接池状态
        pool_status = self.driver_pool.get_pool_status()
        print(f"WebDriver连接池状态: {pool_status}")
        
        # 使用线程池并发抓取，复用WebDriver连接池
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_project_detail, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    project = future.result()
                    if project:
                        projects.append(project)
                        with self.stats_lock:
                            batch_info.success_count += 1
                        print(f"完成 {batch_info.success_count}/{len(urls)}: {project.title[:40]}...")
                    else:
                        with self.stats_lock:
                            batch_info.error_count += 1
                            batch_info.failed_urls.append(url)
                        print(f"失败 {batch_info.error_count}: {url}")
                        
                except Exception as e:
                    print(f"抓取异常 {url}: {e}")
                    with self.stats_lock:
                        batch_info.error_count += 1
                        batch_info.failed_urls.append(url)
        
        batch_info.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 显示批次结束后的连接池状态
        pool_status = self.driver_pool.get_pool_status()
        print(f"批次完成后连接池状态: {pool_status}")
        
        return batch_info, projects
    
    def run(self, urls_file: str, start_batch: int = 1, max_batches: int = None):
        """运行爬虫"""
        print("=" * 60)
        print("增强版项目详情页爬虫启动")
        print(f"✨ 新功能: 完整信息提取，简化数据结构")
        print(f"WebDriver连接池大小: {self.pool_size}")
        print(f"最大并发线程数: {self.max_workers}")
        print("=" * 60)
        
        # 加载URL列表
        urls = self.load_urls_from_file(urls_file)
        if not urls:
            print("没有找到要抓取的URL")
            return
        
        # 过滤新URL（去重）
        new_urls = self.filter_new_urls(urls)
        if not new_urls:
            print("所有URL都已抓取过，无需重复抓取")
            return
        
        print(f"需要抓取 {len(new_urls)} 个新URL")
        
        try:
            all_new_projects = []
            total_batches = (len(new_urls) + self.batch_size - 1) // self.batch_size
            
            if max_batches:
                total_batches = min(total_batches, max_batches)
                print(f"限制抓取批次数: {max_batches}")
            
            print(f"新URL分为 {total_batches} 个批次")
            print(f"从第 {start_batch} 批次开始抓取")
            
            for batch_num in range(start_batch, start_batch + total_batches):
                start_idx = (batch_num - 1) * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(new_urls))
                batch_urls = new_urls[start_idx:end_idx]
                
                print(f"\n{'=' * 60}")
                print(f"开始抓取第 {batch_num}/{total_batches} 批次")
                print(f"本批次包含 {len(batch_urls)} 个项目")
                print('=' * 60)
                
                # 抓取批次
                batch_info, projects = self.scrape_batch(batch_urls, f"{batch_num:03d}")
                
                # 保存批次数据
                self.save_batch_data(batch_info, projects)
                
                # 更新统计
                all_new_projects.extend(projects)
                self.completed_projects += batch_info.success_count
                self.failed_projects += batch_info.error_count
                
                print(f"\n批次 {batch_num} 完成:")
                print(f"  成功: {batch_info.success_count}")
                print(f"  失败: {batch_info.error_count}")
                print(f"  耗时: {self._calculate_batch_duration(batch_info)}")
                
                # 显示完整信息提取效果
                if projects:
                    sample_project = projects[0]
                    print(f"  📊 信息提取示例:")
                    print(f"    标题: {sample_project.title[:30]}...")
                    print(f"    品牌: {sample_project.brand or '未识别'}")
                    print(f"    代理商: {sample_project.agency or '未识别'}")
                    print(f"    描述长度: {len(sample_project.description)} 字符")
                    print(f"    图片数量: {len(sample_project.images)} 张")
                
                # 批次间休息
                if batch_num < start_batch + total_batches - 1:
                    delay = DELAY_CONFIG.get("batch_delay", 10)
                    print(f"等待{delay}秒后继续下一批次...")
                    time.sleep(delay)
            
            # 更新汇总信息（合并现有数据）
            if all_new_projects:
                self.update_summary(all_new_projects)
            
            print(f"\n{'=' * 60}")
            print("增强版抓取完成！")
            print(f"本次新增: {len(all_new_projects)} 个项目")
            print(f"成功: {self.completed_projects}")
            print(f"失败: {self.failed_projects}")
            print(f"成功率: {self.completed_projects/(self.completed_projects+self.failed_projects)*100:.1f}%" if (self.completed_projects+self.failed_projects) > 0 else "N/A")
            print(f"信息完整性大幅提升")
            print('=' * 60)
            
        except KeyboardInterrupt:
            print("\n\n用户中断操作")
            print("正在保存当前进度...")
            # 即使中断也保存已抓取的数据
            if all_new_projects:
                self.update_summary(all_new_projects)
            print("进度已保存")
        
        except Exception as e:
            print(f"\n运行过程中出现错误: {e}")
            # 保存已抓取的数据
            if all_new_projects:
                self.update_summary(all_new_projects)
        
        finally:
            # 不需要手动关闭连接池，由全局管理
            pass
    
    def _calculate_batch_duration(self, batch_info: BatchInfo) -> str:
        """计算批次持续时间"""
        try:
            start_time = datetime.strptime(batch_info.start_time, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(batch_info.end_time, '%Y-%m-%d %H:%M:%S')
            duration = end_time - start_time
            
            minutes = int(duration.total_seconds() // 60)
            seconds = int(duration.total_seconds() % 60)
            
            if minutes > 0:
                return f"{minutes}分{seconds}秒"
            else:
                return f"{seconds}秒"
        except:
            return "未知"
    
    def get_statistics(self) -> Dict:
        """获取爬虫统计信息"""
        summary = self.load_existing_summary()
        pool_status = self.driver_pool.get_pool_status()
        
        return {
            "total_projects": summary.get("total_projects", 0),
            "total_batches": summary.get("total_batches", 0),
            "last_updated": summary.get("last_updated", ""),
            "current_session": {
                "completed": self.completed_projects,
                "failed": self.failed_projects,
                "success_rate": round(self.completed_projects/(self.completed_projects+self.failed_projects)*100, 2) if (self.completed_projects+self.failed_projects) > 0 else 0
            },
            "driver_pool": pool_status,
            "config": {
                "headless": self.headless,
                "max_workers": self.max_workers,
                "batch_size": self.batch_size,
                "pool_size": self.pool_size,
                "version": "enhanced-2.0"
            }
        }
    
    def __del__(self):
        """析构函数"""
        # WebDriver连接池由全局管理，这里不需要手动关闭
        pass


if __name__ == "__main__":
    # 创建增强版爬虫实例
    scraper = ProjectDetailScraperEnhanced(
        headless=SCRAPER_CONFIG.get("headless", True),
        max_workers=SCRAPER_CONFIG.get("max_workers", 2),
        output_dir=SCRAPER_CONFIG.get("output_dir", "output"),
        pool_size=3  # WebDriver连接池大小
    )
    
    try:
        # 运行爬虫（验证模式）
        scraper.run("project_urls.txt", start_batch=1, max_batches=1)
        
        # 显示统计信息
        stats = scraper.get_statistics()
        print(f"\n统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭全局连接池
        close_global_pool()
        print("资源清理完成")