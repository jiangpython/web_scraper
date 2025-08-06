"""
项目数据管理器
管理项目数据的加载、索引、搜索和查询功能
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import jieba
import jieba.analyse


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    projects: List[Dict]
    total_count: int
    query_info: Dict[str, Any]
    search_time: float


class ProjectDataManager:
    """项目数据管理器"""
    
    def __init__(self, data_path: str = "output/projects_summary.json"):
        """
        初始化数据管理器
        
        Args:
            data_path: 项目数据文件路径
        """
        self.data_path = data_path
        self.projects = []
        self.brand_index = defaultdict(list)
        self.agency_index = defaultdict(list)
        self.title_index = defaultdict(list)
        self.keyword_index = defaultdict(list)
        self.date_index = defaultdict(list)
        
        # 加载数据
        self.load_data()
        self._build_indexes()
        
        print(f"✅ 数据管理器初始化完成，加载 {len(self.projects)} 个项目")
    
    def load_data(self) -> bool:
        """加载项目数据"""
        if not os.path.exists(self.data_path):
            print(f"⚠️ 数据文件不存在: {self.data_path}")
            return False
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.projects = data.get('projects', [])
            self.last_updated = data.get('last_updated', '')
            self.total_projects = data.get('total_projects', len(self.projects))
            
            print(f"✅ 成功加载 {len(self.projects)} 个项目")
            return True
            
        except Exception as e:
            print(f"❌ 加载数据失败: {e}")
            return False
    
    def _build_indexes(self):
        """构建索引以提高查询性能"""
        print("🔍 构建数据索引...")
        
        for i, project in enumerate(self.projects):
            # 品牌索引
            brand = project.get('brand', '').strip()
            if brand:
                self.brand_index[brand.lower()].append(i)
            
            # 代理商索引
            agency = project.get('agency', '').strip()
            if agency:
                self.agency_index[agency.lower()].append(i)
            
            # 标题索引（分词）
            title = project.get('title', '').strip()
            if title:
                words = jieba.lcut(title)
                for word in words:
                    if len(word.strip()) > 1:  # 过滤单字符
                        self.title_index[word.lower()].append(i)
            
            # 关键词索引
            keywords = jieba.analyse.extract_tags(title, topK=10)
            for keyword in keywords:
                self.keyword_index[keyword.lower()].append(i)
            
            # 日期索引
            date = project.get('publish_date', '').strip()
            if date:
                try:
                    date_obj = datetime.strptime(date[:10], '%Y-%m-%d')
                    year_month = date_obj.strftime('%Y-%m')
                    self.date_index[year_month].append(i)
                except:
                    pass
        
        print(f"✅ 索引构建完成: {len(self.brand_index)} 品牌, {len(self.agency_index)} 代理商")
    
    def search_by_brand(self, brand_name: str, fuzzy: bool = True) -> List[Dict]:
        """按品牌搜索"""
        brand_name = brand_name.lower().strip()
        results = []
        
        if not fuzzy:
            # 精确匹配
            indices = self.brand_index.get(brand_name, [])
            results = [self.projects[i] for i in indices]
        else:
            # 模糊匹配
            for brand, indices in self.brand_index.items():
                if brand_name in brand or brand in brand_name:
                    results.extend([self.projects[i] for i in indices])
        
        return self._deduplicate_projects(results)
    
    def search_by_agency(self, agency_name: str, fuzzy: bool = True) -> List[Dict]:
        """按代理商搜索"""
        agency_name = agency_name.lower().strip()
        results = []
        
        if not fuzzy:
            indices = self.agency_index.get(agency_name, [])
            results = [self.projects[i] for i in indices]
        else:
            for agency, indices in self.agency_index.items():
                if agency_name in agency or agency in agency_name:
                    results.extend([self.projects[i] for i in indices])
        
        return self._deduplicate_projects(results)
    
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """按关键词搜索（标题和关键词索引）"""
        keyword = keyword.lower().strip()
        results = []
        
        # 搜索标题索引
        for word, indices in self.title_index.items():
            if keyword in word or word in keyword:
                results.extend([self.projects[i] for i in indices])
        
        # 搜索关键词索引
        for kw, indices in self.keyword_index.items():
            if keyword in kw or kw in keyword:
                results.extend([self.projects[i] for i in indices])
        
        # 全文搜索作为补充
        for project in self.projects:
            title = project.get('title', '').lower()
            description = project.get('description', '').lower()
            
            if (keyword in title or keyword in description) and project not in results:
                results.append(project)
        
        return self._deduplicate_projects(results)
    
    def search_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """按日期范围搜索"""
        results = []
        
        try:
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_dt = datetime.min
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_dt = datetime.max
            
            for project in self.projects:
                date_str = project.get('publish_date', '').strip()
                if not date_str:
                    continue
                
                try:
                    project_dt = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    if start_dt <= project_dt <= end_dt:
                        results.append(project)
                except:
                    continue
        
        except Exception as e:
            print(f"⚠️ 日期搜索出错: {e}")
        
        return results
    
    def search_recent_projects(self, days: int = 30) -> List[Dict]:
        """搜索最近的项目"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        return self.search_by_date_range(start_date, end_date)
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """根据项目ID获取项目"""
        for project in self.projects:
            if project.get('id') == project_id:
                return project
        return None
    
    def get_project_by_url(self, url: str) -> Optional[Dict]:
        """根据URL获取项目"""
        for project in self.projects:
            if project.get('url') == url:
                return project
        return None
    
    def advanced_search(self, 
                       brand: str = None,
                       agency: str = None, 
                       keyword: str = None,
                       start_date: str = None,
                       end_date: str = None,
                       limit: int = None) -> SearchResult:
        """
        高级搜索，支持多条件组合
        
        Args:
            brand: 品牌名称
            agency: 代理商名称
            keyword: 关键词
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 结果数量限制
            
        Returns:
            SearchResult对象
        """
        start_time = datetime.now()
        
        # 收集所有候选项目
        candidate_projects = set(range(len(self.projects)))
        
        query_info = {
            "brand": brand,
            "agency": agency,
            "keyword": keyword,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        }
        
        # 按品牌筛选
        if brand:
            brand_projects = self.search_by_brand(brand)
            brand_indices = {self.projects.index(p) for p in brand_projects if p in self.projects}
            candidate_projects &= brand_indices
        
        # 按代理商筛选
        if agency:
            agency_projects = self.search_by_agency(agency)
            agency_indices = {self.projects.index(p) for p in agency_projects if p in self.projects}
            candidate_projects &= agency_indices
        
        # 按关键词筛选
        if keyword:
            keyword_projects = self.search_by_keyword(keyword)
            keyword_indices = {self.projects.index(p) for p in keyword_projects if p in self.projects}
            candidate_projects &= keyword_indices
        
        # 按日期范围筛选
        if start_date or end_date:
            date_projects = self.search_by_date_range(start_date, end_date)
            date_indices = {self.projects.index(p) for p in date_projects if p in self.projects}
            candidate_projects &= date_indices
        
        # 转换为项目列表
        results = [self.projects[i] for i in candidate_projects]
        
        # 按日期排序（最新的在前）
        results.sort(key=lambda x: x.get('publish_date', ''), reverse=True)
        
        # 应用数量限制
        if limit and len(results) > limit:
            results = results[:limit]
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResult(
            projects=results,
            total_count=len(results),
            query_info=query_info,
            search_time=search_time
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        stats = {
            "total_projects": len(self.projects),
            "total_brands": len(self.brand_index),
            "total_agencies": len(self.agency_index),
            "last_updated": self.last_updated,
            "date_range": self._get_date_range(),
            "top_brands": self._get_top_brands(10),
            "top_agencies": self._get_top_agencies(10),
            "monthly_distribution": self._get_monthly_distribution()
        }
        return stats
    
    def _get_date_range(self) -> Dict[str, str]:
        """获取项目日期范围"""
        dates = []
        for project in self.projects:
            date_str = project.get('publish_date', '').strip()
            if date_str:
                try:
                    dates.append(datetime.strptime(date_str[:10], '%Y-%m-%d'))
                except:
                    continue
        
        if dates:
            return {
                "earliest": min(dates).strftime('%Y-%m-%d'),
                "latest": max(dates).strftime('%Y-%m-%d')
            }
        return {"earliest": "", "latest": ""}
    
    def _get_top_brands(self, limit: int = 10) -> List[Tuple[str, int]]:
        """获取项目数量最多的品牌"""
        brand_counts = [(brand, len(indices)) for brand, indices in self.brand_index.items()]
        brand_counts.sort(key=lambda x: x[1], reverse=True)
        return brand_counts[:limit]
    
    def _get_top_agencies(self, limit: int = 10) -> List[Tuple[str, int]]:
        """获取项目数量最多的代理商"""
        agency_counts = [(agency, len(indices)) for agency, indices in self.agency_index.items()]
        agency_counts.sort(key=lambda x: x[1], reverse=True)
        return agency_counts[:limit]
    
    def _get_monthly_distribution(self) -> Dict[str, int]:
        """获取项目按月份分布"""
        return {month: len(indices) for month, indices in self.date_index.items()}
    
    def _deduplicate_projects(self, projects: List[Dict]) -> List[Dict]:
        """去重项目列表"""
        seen_urls = set()
        unique_projects = []
        
        for project in projects:
            url = project.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_projects.append(project)
        
        return unique_projects
    
    def refresh_data(self) -> bool:
        """刷新数据（重新加载和构建索引）"""
        print("🔄 刷新数据...")
        
        # 清空现有数据和索引
        self.projects = []
        self.brand_index.clear()
        self.agency_index.clear()
        self.title_index.clear()
        self.keyword_index.clear()
        self.date_index.clear()
        
        # 重新加载
        if self.load_data():
            self._build_indexes()
            print("✅ 数据刷新完成")
            return True
        else:
            print("❌ 数据刷新失败")
            return False


if __name__ == "__main__":
    # 测试数据管理器
    manager = ProjectDataManager()
    
    # 测试基本功能
    print("\n🧪 测试数据管理器功能:")
    
    # 获取统计信息
    stats = manager.get_statistics()
    print(f"📊 统计信息: {stats['total_projects']} 个项目, {stats['total_brands']} 个品牌")
    
    # 测试搜索功能
    if len(manager.projects) > 0:
        # 随机选择一个项目进行测试
        sample_project = manager.projects[0]
        brand = sample_project.get('brand', '')
        
        if brand:
            print(f"\n🔍 测试品牌搜索: '{brand}'")
            brand_results = manager.search_by_brand(brand)
            print(f"找到 {len(brand_results)} 个相关项目")
        
        # 测试关键词搜索
        print(f"\n🔍 测试关键词搜索: '营销'")
        keyword_results = manager.search_by_keyword('营销')
        print(f"找到 {len(keyword_results)} 个相关项目")
        
        # 测试高级搜索
        print(f"\n🔍 测试高级搜索:")
        search_result = manager.advanced_search(keyword='创意', limit=5)
        print(f"找到 {search_result.total_count} 个项目, 耗时 {search_result.search_time:.3f}秒")
    
    print("\n✅ 数据管理器测试完成")