#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成索引文件
基于现有的batch文件重新生成projects_index.json和global_search_index.json
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

class IndexRegenerator:
    """索引重新生成器"""
    
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.details_dir = os.path.join(output_dir, "details")
        self.projects_index_file = os.path.join(output_dir, "projects_index.json")
        self.global_index_file = os.path.join(output_dir, "global_search_index.json")
        self.master_csv = "master_projects.csv"
    
    def regenerate_all(self):
        """重新生成所有索引"""
        print("=== 重新生成索引文件 ===")
        
        # 1. 扫描现有batch文件
        batch_data = self._load_all_batch_data()
        if not batch_data:
            print("没有找到有效的batch数据")
            return False
        
        # 2. 加载master数据用于补充基本信息
        master_data = self._load_master_data()
        
        # 3. 合并数据
        merged_projects = self._merge_data(batch_data, master_data)
        
        # 4. 生成projects_index.json
        self._generate_projects_index(merged_projects)
        
        # 5. 生成global_search_index.json  
        self._generate_global_index(merged_projects)
        
        print("索引重新生成完成！")
        return True
    
    def _load_all_batch_data(self) -> List[Dict]:
        """加载所有batch文件数据"""
        if not os.path.exists(self.details_dir):
            print(f"详细数据目录不存在: {self.details_dir}")
            return []
        
        all_projects = []
        batch_files = [f for f in os.listdir(self.details_dir) 
                      if f.startswith('batch_') and f.endswith('.json') and f != 'batch_metadata.json']
        
        print(f"发现 {len(batch_files)} 个batch文件")
        
        for batch_file in batch_files:
            file_path = os.path.join(self.details_dir, batch_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                projects = data.get('projects', [])
                batch_name = batch_file.replace('.json', '')
                
                # 为每个项目添加batch信息
                for project in projects:
                    project['_batch'] = batch_name
                
                all_projects.extend(projects)
                print(f"[OK] {batch_file}: {len(projects)} 个项目")
                
            except json.JSONDecodeError as e:
                print(f"[ERROR] {batch_file}: JSON解析失败 - {e}")
            except Exception as e:
                print(f"[ERROR] {batch_file}: 读取失败 - {e}")
        
        print(f"总共加载: {len(all_projects)} 个项目")
        return all_projects
    
    def _load_master_data(self) -> Dict:
        """加载master项目数据"""
        if not os.path.exists(self.master_csv):
            print(f"Warning: master文件不存在: {self.master_csv}")
            return {}
        
        try:
            df = pd.read_csv(self.master_csv)
            master_dict = {}
            for _, row in df.iterrows():
                master_dict[str(row['project_id'])] = row.to_dict()
            print(f"加载master数据: {len(master_dict)} 个项目")
            return master_dict
        except Exception as e:
            print(f"读取master数据失败: {e}")
            return {}
    
    def _merge_data(self, batch_projects: List[Dict], master_data: Dict) -> List[Dict]:
        """合并batch数据和master数据"""
        merged = []
        
        for project in batch_projects:
            project_id = str(project.get('id', ''))
            master_info = master_data.get(project_id, {})
            
            # 合并数据，batch数据优先
            merged_project = {
                'id': project_id,
                'url': project.get('url', master_info.get('url', '')),
                'title': project.get('title', master_info.get('title', '')),
                'brand': project.get('brand', master_info.get('brand', '')),
                'agency': project.get('agency', master_info.get('agency', '')),
                'publish_date': project.get('publish_date', master_info.get('publish_date', '')),
                'description': project.get('description', ''),
                'images': project.get('images', []),
                'category': project.get('category', ''),
                'keywords': project.get('keywords', []),
                'industry': project.get('industry', ''),
                'campaign_type': project.get('campaign_type', ''),
                'project_info': project.get('project_info', {}),
                '_batch': project.get('_batch', '')
            }
            merged.append(merged_project)
        
        return merged
    
    def _generate_projects_index(self, projects: List[Dict]):
        """生成projects_index.json"""
        try:
            # 生成统计信息
            stats = {
                'total_brands': len(set(p.get('brand', '') for p in projects if p.get('brand'))),
                'total_agencies': len(set(p.get('agency', '') for p in projects if p.get('agency'))),
                'total_categories': len(set(p.get('category', '') for p in projects if p.get('category'))),
                'avg_description_length': sum(len(p.get('description', '')) for p in projects) / len(projects) if projects else 0
            }
            
            projects_index = {
                'total_projects': len(projects),
                'total_batches': len(set(p.get('_batch', '') for p in projects if p.get('_batch'))),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_source': 'batch_files + master_projects.csv',
                'statistics': stats,
                'projects': projects
            }
            
            with open(self.projects_index_file, 'w', encoding='utf-8') as f:
                json.dump(projects_index, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] projects_index.json 已生成: {len(projects)} 个项目")
            
        except Exception as e:
            print(f"[ERROR] 生成projects_index.json失败: {e}")
    
    def _generate_global_index(self, projects: List[Dict]):
        """生成global_search_index.json"""
        try:
            brand_index = defaultdict(list)
            keyword_index = defaultdict(list)
            category_index = defaultdict(list)
            industry_index = defaultdict(list)
            
            # 构建各种索引
            for project in projects:
                project_ref = {
                    'batch': project.get('_batch', ''),
                    'id': project.get('id', ''),
                    'title': project.get('title', ''),
                    'score': 1.0
                }
                
                # 品牌索引
                brand = project.get('brand', '').strip()
                if brand:
                    brand_index[brand].append(project_ref.copy())
                
                # 关键词索引
                keywords = project.get('keywords', [])
                if isinstance(keywords, list):
                    for keyword in keywords:
                        if keyword.strip():
                            keyword_index[keyword.strip()].append(project_ref.copy())
                
                # 分类索引
                category = project.get('category', '').strip()
                if category:
                    category_index[category].append(project_ref.copy())
                
                # 行业索引
                industry = project.get('industry', '').strip()
                if industry:
                    industry_index[industry].append(project_ref.copy())
            
            # 构建最终索引
            global_index = {
                'metadata': {
                    'total_projects': len(projects),
                    'processed_batches': len(set(p.get('_batch', '') for p in projects if p.get('_batch'))),
                    'unique_brands': len(brand_index),
                    'unique_keywords': len(keyword_index),
                    'unique_categories': len(category_index),
                    'unique_industries': len(industry_index),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'index_version': '2.0'
                },
                'brand_index': dict(brand_index),
                'keyword_index': dict(keyword_index),
                'category_index': dict(category_index),
                'industry_index': dict(industry_index)
            }
            
            with open(self.global_index_file, 'w', encoding='utf-8') as f:
                json.dump(global_index, f, ensure_ascii=False, indent=2)
            
            print(f"[OK] global_search_index.json 已生成:")
            print(f"    - 品牌: {len(brand_index)} 个")
            print(f"    - 关键词: {len(keyword_index)} 个") 
            print(f"    - 分类: {len(category_index)} 个")
            print(f"    - 行业: {len(industry_index)} 个")
            
        except Exception as e:
            print(f"[ERROR] 生成global_search_index.json失败: {e}")

def main():
    """主函数"""
    regenerator = IndexRegenerator()
    success = regenerator.regenerate_all()
    
    if success:
        print("\n✅ 索引重新生成成功！")
        print("AI系统现在可以正确访问所有可用的项目数据。")
    else:
        print("\n❌ 索引重新生成失败！")

if __name__ == "__main__":
    main()