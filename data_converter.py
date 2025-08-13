#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据转换器 - 将combined_projects.json转换为AI系统兼容格式
生成projects_index.json和global_search_index.json
"""

import os
import json
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

class DataConverter:
    """数据转换器 - 将合并数据转换为AI系统兼容格式"""
    
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.combined_json = os.path.join(output_dir, "combined_projects.json")
        self.projects_index_file = os.path.join(output_dir, "projects_index.json")
        self.global_index_file = os.path.join(output_dir, "global_search_index.json")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def convert_all(self):
        """执行完整的数据转换流程"""
        print("开始数据转换...")
        
        # 1. 读取合并数据
        combined_data = self._load_combined_data()
        if not combined_data:
            print("没有找到合并数据文件")
            return False
        
        # 2. 生成projects_index.json
        projects_success = self._generate_projects_index(combined_data)
        
        # 3. 生成global_search_index.json
        index_success = self._generate_global_search_index(combined_data)
        
        if projects_success and index_success:
            print("数据转换完成！")
            print(f"项目索引: {self.projects_index_file}")
            print(f"全局索引: {self.global_index_file}")
            return True
        else:
            print("数据转换失败！")
            return False
    
    def _load_combined_data(self) -> Dict:
        """加载合并数据"""
        if not os.path.exists(self.combined_json):
            print(f"合并数据文件不存在: {self.combined_json}")
            return {}
        
        try:
            with open(self.combined_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"加载合并数据: {data.get('total_projects', 0)} 个项目")
            return data
        except Exception as e:
            print(f"读取合并数据失败: {e}")
            return {}
    
    def _generate_projects_index(self, combined_data: Dict) -> bool:
        """生成projects_index.json - 兼容现有AI系统格式"""
        try:
            projects = combined_data.get('projects', [])
            
            # 转换为AI系统期望的格式
            converted_projects = []
            for project in projects:
                converted_project = {
                    'id': project.get('id'),
                    'url': project.get('url'),
                    'title': project.get('title', ''),
                    'brand': project.get('brand', ''),
                    'agency': project.get('agency', ''),
                    'publish_date': project.get('publish_date', ''),
                    'description': project.get('description', ''),
                    'images': project.get('images', []),
                    'category': project.get('category', ''),
                    'keywords': project.get('keywords', []),
                    'industry': project.get('industry', ''),
                    'campaign_type': project.get('campaign_type', ''),
                    'project_info': project.get('project_info', {})
                }
                converted_projects.append(converted_project)
            
            # 生成统计信息
            stats = self._generate_project_stats(converted_projects)
            
            # 构建最终数据结构
            projects_index = {
                'total_projects': len(converted_projects),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'master_projects.csv + web_scraping',
                'statistics': stats,
                'projects': converted_projects
            }
            
            # 保存文件
            with open(self.projects_index_file, 'w', encoding='utf-8') as f:
                json.dump(projects_index, f, ensure_ascii=False, indent=2)
            
            print(f"项目索引生成成功: {len(converted_projects)} 个项目")
            return True
            
        except Exception as e:
            print(f"生成项目索引失败: {e}")
            return False
    
    def _generate_project_stats(self, projects: List[Dict]) -> Dict:
        """生成项目统计信息"""
        total_projects = len(projects)
        
        # 基础统计
        brands = set()
        agencies = set()
        categories = set()
        industries = set()
        campaign_types = set()
        
        # 数据完整性统计
        with_brand = 0
        with_agency = 0
        with_description = 0
        with_images = 0
        with_category = 0
        
        for project in projects:
            # 收集唯一值
            if project.get('brand'):
                brands.add(project['brand'])
                with_brand += 1
            
            if project.get('agency'):
                agencies.add(project['agency'])
                with_agency += 1
                
            if project.get('category'):
                categories.add(project['category'])
                with_category += 1
                
            if project.get('industry'):
                industries.add(project['industry'])
                
            if project.get('campaign_type'):
                campaign_types.add(project['campaign_type'])
            
            # 内容完整性
            if project.get('description') and len(project['description']) > 50:
                with_description += 1
                
            if project.get('images') and len(project['images']) > 0:
                with_images += 1
        
        return {
            'unique_brands': len(brands),
            'unique_agencies': len(agencies),
            'unique_categories': len(categories),
            'unique_industries': len(industries),
            'unique_campaign_types': len(campaign_types),
            'completeness': {
                'brand_rate': round(with_brand / total_projects * 100, 1),
                'agency_rate': round(with_agency / total_projects * 100, 1),
                'description_rate': round(with_description / total_projects * 100, 1),
                'images_rate': round(with_images / total_projects * 100, 1),
                'category_rate': round(with_category / total_projects * 100, 1)
            }
        }
    
    def _generate_global_search_index(self, combined_data: Dict) -> bool:
        """生成global_search_index.json - 快速查询索引"""
        try:
            projects = combined_data.get('projects', [])
            
            # 初始化索引字典
            brand_index = defaultdict(list)
            agency_index = defaultdict(list)
            keyword_index = defaultdict(list)
            category_index = defaultdict(list)
            industry_index = defaultdict(list)
            campaign_type_index = defaultdict(list)
            date_index = defaultdict(list)
            
            # 构建索引
            for project in projects:
                project_id = project.get('id')
                
                # 品牌索引
                brand = project.get('brand')
                if brand and isinstance(brand, str) and brand.strip():
                    brand_index[brand.lower()].append(project_id)
                
                # 代理商索引
                agency = project.get('agency')
                if agency and isinstance(agency, str) and agency.strip():
                    agency_index[agency.lower()].append(project_id)
                
                # 分类索引
                category = project.get('category')
                if category and isinstance(category, str) and category.strip():
                    category_index[category.lower()].append(project_id)
                
                # 行业索引
                industry = project.get('industry')
                if industry and isinstance(industry, str) and industry.strip():
                    industry_index[industry.lower()].append(project_id)
                
                # 营销类型索引
                campaign_type = project.get('campaign_type')
                if campaign_type and isinstance(campaign_type, str) and campaign_type.strip():
                    campaign_type_index[campaign_type.lower()].append(project_id)
                
                # 关键词索引
                keywords = project.get('keywords', [])
                for keyword in keywords:
                    if isinstance(keyword, str):
                        keyword_index[keyword.lower()].append(project_id)
                
                # 日期索引 (按年月分组)
                publish_date = project.get('publish_date', '')
                if publish_date:
                    try:
                        # 提取年月信息
                        if len(publish_date) >= 7:  # YYYY-MM格式
                            year_month = publish_date[:7]
                            date_index[year_month].append(project_id)
                    except:
                        pass
                
                # 标题关键词索引
                title = project.get('title', '')
                if title:
                    # 简单的中文分词 - 提取常见关键词
                    title_keywords = self._extract_title_keywords(title)
                    for keyword in title_keywords:
                        keyword_index[keyword.lower()].append(project_id)
            
            # 构建全局索引数据结构
            global_index = {
                'total_projects': len(projects),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'index_stats': {
                    'brands': len(brand_index),
                    'agencies': len(agency_index),
                    'keywords': len(keyword_index),
                    'categories': len(category_index),
                    'industries': len(industry_index),
                    'campaign_types': len(campaign_type_index),
                    'date_groups': len(date_index)
                },
                'indices': {
                    'brand_index': dict(brand_index),
                    'agency_index': dict(agency_index),
                    'keyword_index': dict(keyword_index),
                    'category_index': dict(category_index),
                    'industry_index': dict(industry_index),
                    'campaign_type_index': dict(campaign_type_index),
                    'date_index': dict(date_index)
                }
            }
            
            # 保存文件
            with open(self.global_index_file, 'w', encoding='utf-8') as f:
                json.dump(global_index, f, ensure_ascii=False, indent=2)
            
            print(f"全局索引生成成功:")
            print(f"  品牌索引: {len(brand_index)} 项")
            print(f"  代理商索引: {len(agency_index)} 项")
            print(f"  关键词索引: {len(keyword_index)} 项")
            print(f"  分类索引: {len(category_index)} 项")
            return True
            
        except Exception as e:
            print(f"生成全局索引失败: {e}")
            return False
    
    def _extract_title_keywords(self, title: str) -> List[str]:
        """从标题中提取关键词 - 简化版本"""
        if not title:
            return []
        
        # 常见的营销关键词
        marketing_keywords = [
            '品牌', '营销', '广告', '推广', '活动', '创意', '设计',
            '传播', '宣传', '发布', '上市', '新品', '促销', '节日',
            '数字化', '社交', '媒体', '内容', '视频', '直播',
            '电商', '零售', '消费者', '用户', '体验', '互动'
        ]
        
        found_keywords = []
        title_lower = title.lower()
        
        for keyword in marketing_keywords:
            if keyword in title:
                found_keywords.append(keyword)
        
        return found_keywords[:5]  # 限制关键词数量
    
    def update_indices_incrementally(self, new_projects: List[Dict]):
        """增量更新索引 - 用于新批次数据"""
        print("增量更新索引...")
        
        # 重新生成完整索引（简化版本，生产环境应该优化为增量更新）
        fake_combined_data = {
            'projects': new_projects,
            'total_projects': len(new_projects)
        }
        
        return self._generate_global_search_index(fake_combined_data)

def main():
    """测试主函数"""
    try:
        converter = DataConverter()
        success = converter.convert_all()
        
        if success:
            print("\n数据转换成功完成!")
        else:
            print("\n数据转换失败!")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()