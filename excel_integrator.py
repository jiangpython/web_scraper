#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel数据整合器
整合data文件夹下所有Excel文件，生成master_projects.csv统一数据源
"""

import pandas as pd
import os
import re
from datetime import datetime
import glob

class ExcelIntegrator:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.master_data = {}  # 使用project_id作为键的字典
        self.stats = {
            'total_files': 0,
            'total_records': 0,
            'unique_projects': 0,
            'duplicates_removed': 0
        }
    
    def _clean_field_value(self, value):
        """清理字段值，确保返回字符串"""
        if pd.isna(value):
            return ""
        if not isinstance(value, str):
            return str(value)
        return value.strip()
    
    def extract_project_id(self, url):
        """从URL中提取项目ID"""
        if pd.isna(url) or not isinstance(url, str):
            return None
        
        match = re.search(r'/projects/(\d+)\.html', url)
        return match.group(1) if match else None
    
    def extract_timestamp_from_filename(self, filename):
        """从文件名中提取时间戳"""
        # 匹配格式：digitaling_projects_final_20250806_095833.xlsx
        match = re.search(r'(\d{8})_(\d{6})', filename)
        if match:
            date_str = match.group(1) + match.group(2)  # 20250806095833
            try:
                return datetime.strptime(date_str, '%Y%m%d%H%M%S')
            except:
                pass
        
        # 备用匹配：只有日期
        match = re.search(r'(\d{8})', filename)
        if match:
            date_str = match.group(1)
            try:
                return datetime.strptime(date_str, '%Y%m%d')
            except:
                pass
        
        return datetime.min  # 默认最早时间
    
    def load_all_excel_files(self):
        """加载所有Excel文件"""
        excel_files = glob.glob(os.path.join(self.data_dir, "*.xlsx"))
        excel_files = [f for f in excel_files if not os.path.basename(f).startswith('~$')]
        
        # 按时间戳排序，早的文件先处理
        excel_files.sort(key=lambda x: self.extract_timestamp_from_filename(os.path.basename(x)))
        
        print(f"找到 {len(excel_files)} 个Excel文件")
        
        for file_path in excel_files:
            self.process_excel_file(file_path)
        
        self.stats['total_files'] = len(excel_files)
        self.stats['unique_projects'] = len(self.master_data)
        
        return self.master_data
    
    def process_excel_file(self, file_path):
        """处理单个Excel文件"""
        filename = os.path.basename(file_path)
        timestamp = self.extract_timestamp_from_filename(filename)
        
        print(f"处理文件: {filename}")
        
        try:
            # 检查是否有"所有项目合并"sheet
            xl_file = pd.ExcelFile(file_path)
            if '所有项目合并' not in xl_file.sheet_names:
                print(f"  警告: {filename} 没有'所有项目合并'sheet，跳过")
                return
            
            # 读取数据
            df = pd.read_excel(file_path, sheet_name='所有项目合并')
            print(f"  读取到 {len(df)} 条记录")
            
            # 处理每一行数据
            processed_count = 0
            for _, row in df.iterrows():
                project_id = self.extract_project_id(row.get('link'))
                if not project_id:
                    continue
                
                # 创建项目记录 - 确保所有字段都是字符串类型
                project_record = {
                    'project_id': project_id,
                    'url': self._clean_field_value(row.get('link', '')),
                    'brand': self._clean_field_value(row.get('brand', '')),
                    'agency': self._clean_field_value(row.get('agency', '')),
                    'title': self._clean_field_value(row.get('title', '')),
                    'publish_date': self._clean_field_value(row.get('publish_date', '')),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 如果项目ID已存在，比较时间戳，保留更新的
                if project_id in self.master_data:
                    existing_timestamp = self.master_data[project_id].get('_file_timestamp', datetime.min)
                    if timestamp > existing_timestamp:
                        self.master_data[project_id] = project_record
                        self.master_data[project_id]['_file_timestamp'] = timestamp
                        self.stats['duplicates_removed'] += 1
                    else:
                        self.stats['duplicates_removed'] += 1
                else:
                    self.master_data[project_id] = project_record
                    self.master_data[project_id]['_file_timestamp'] = timestamp
                
                processed_count += 1
                self.stats['total_records'] += 1
            
            print(f"  处理完成: {processed_count} 条记录")
            
        except Exception as e:
            print(f"  错误: 处理文件 {filename} 时出错: {e}")
    
    def clean_and_validate(self):
        """数据清理和验证"""
        print("开始数据清理和验证...")
        
        cleaned_count = 0
        for project_id, record in self.master_data.items():
            # 清理agency字段中的HTML标签和特殊字符
            if record.get('agency'):
                agency = str(record['agency'])
                # 移除HTML实体和标签
                agency = re.sub(r'&nbsp;|&amp;|&lt;|&gt;', '', agency)
                agency = re.sub(r'<[^>]+>', '', agency)
                agency = agency.strip()
                record['agency'] = agency if agency else ''
            
            # 标准化日期格式
            if record.get('publish_date'):
                # 这里可以添加日期格式标准化逻辑
                pass
            
            # 移除临时字段
            if '_file_timestamp' in record:
                del record['_file_timestamp']
            
            cleaned_count += 1
        
        print(f"清理完成: {cleaned_count} 条记录")
    
    def export_master_csv(self, output_path="master_projects.csv"):
        """导出Master CSV文件"""
        if not self.master_data:
            print("没有数据可导出")
            return False
        
        # 转换为DataFrame
        df = pd.DataFrame.from_dict(self.master_data, orient='index')
        
        # 重新排序列
        column_order = ['project_id', 'url', 'brand', 'agency', 'title', 'publish_date', 'last_updated']
        df = df[column_order]
        
        # 导出CSV
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"导出完成: {output_path}")
        print(f"总记录数: {len(df)}")
        
        return True
    
    def print_stats(self):
        """打印统计信息"""
        print("\n=== 数据整合统计 ===")
        print(f"处理文件数: {self.stats['total_files']}")
        print(f"总记录数: {self.stats['total_records']}")
        print(f"唯一项目数: {self.stats['unique_projects']}")
        print(f"去重数量: {self.stats['duplicates_removed']}")
        
        # 品牌和代理商统计
        brands = set()
        agencies = set()
        empty_agency_count = 0
        
        for record in self.master_data.values():
            if record.get('brand'):
                brands.add(record['brand'])
            if record.get('agency'):
                agencies.add(record['agency'])
            else:
                empty_agency_count += 1
        
        print(f"唯一品牌数: {len(brands)}")
        print(f"唯一代理商数: {len(agencies)}")
        print(f"无代理商记录: {empty_agency_count}")
    
    def run(self):
        """执行完整的整合流程"""
        print("开始Excel数据整合...")
        
        # 1. 加载所有Excel文件
        self.load_all_excel_files()
        
        # 2. 数据清理和验证
        self.clean_and_validate()
        
        # 3. 导出Master CSV
        success = self.export_master_csv()
        
        # 4. 打印统计信息
        self.print_stats()
        
        return success

def main():
    integrator = ExcelIntegrator()
    success = integrator.run()
    
    if success:
        print("\n数据整合完成！")
    else:
        print("\n数据整合失败！")

if __name__ == "__main__":
    main()