#!/usr/bin/env python3
"""
数据分析脚本 - 分析data文件夹中的Excel文件
提取品牌总数和项目总数统计信息
"""

import os
import pandas as pd
import json
from typing import Dict, List, Set
from datetime import datetime
import glob

class DataAnalyzer:
    """Excel数据分析器"""
    
    def __init__(self, data_folder: str = "data"):
        """初始化分析器"""
        self.data_folder = data_folder
        self.sheet_name = "所有项目合并"
        self.all_brands = set()
        self.all_projects = set()
        self.file_stats = []
        
    def analyze_excel_files(self) -> Dict:
        """分析所有Excel文件"""
        print("开始分析Excel文件...")
        
        # 查找所有xlsx文件
        xlsx_pattern = os.path.join(self.data_folder, "*.xlsx")
        xlsx_files = glob.glob(xlsx_pattern)
        
        # 过滤掉临时文件
        xlsx_files = [f for f in xlsx_files if not os.path.basename(f).startswith('~$')]
        
        print(f"找到 {len(xlsx_files)} 个Excel文件")
        
        for file_path in xlsx_files:
            print(f"\n分析文件: {os.path.basename(file_path)}")
            self.analyze_single_file(file_path)
        
        # 生成统计结果
        result = {
            "analysis_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_files_processed": len(self.file_stats),
            "unique_brands_count": len(self.all_brands),
            "unique_projects_count": len(self.all_projects),
            "unique_brands": sorted(list(self.all_brands)),
            "file_details": self.file_stats
        }
        
        return result
    
    def analyze_single_file(self, file_path: str):
        """分析单个Excel文件"""
        file_info = {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "status": "unknown",
            "sheets": [],
            "brands_in_file": 0,
            "projects_in_file": 0,
            "error": None
        }
        
        try:
            # 读取Excel文件的所有sheet名称
            excel_file = pd.ExcelFile(file_path)
            file_info["sheets"] = excel_file.sheet_names
            
            # 检查是否存在目标sheet
            if self.sheet_name in excel_file.sheet_names:
                # 读取目标sheet
                df = pd.read_excel(file_path, sheet_name=self.sheet_name)
                
                print(f"  找到sheet '{self.sheet_name}', 共 {len(df)} 行数据")
                print(f"  字段列表: {list(df.columns)}")
                
                # 分析brand字段
                if 'brand' in df.columns:
                    brands = df['brand'].dropna().unique()
                    brand_set = set(str(b).strip() for b in brands if str(b).strip() and str(b) != 'nan')
                    self.all_brands.update(brand_set)
                    file_info["brands_in_file"] = len(brand_set)
                    print(f"  品牌数量: {len(brand_set)}")
                else:
                    print("  警告: 未找到'brand'字段")
                
                # 分析link字段
                if 'link' in df.columns:
                    links = df['link'].dropna().unique()
                    link_set = set(str(l).strip() for l in links if str(l).strip() and str(l) != 'nan')
                    self.all_projects.update(link_set)
                    file_info["projects_in_file"] = len(link_set)
                    print(f"  项目链接数量: {len(link_set)}")
                else:
                    print("  警告: 未找到'link'字段")
                
                file_info["status"] = "success"
                
                # 显示数据示例
                print("  数据示例:")
                for i, row in df.head(3).iterrows():
                    brand = row.get('brand', 'N/A')
                    link = row.get('link', 'N/A')
                    print(f"    行{i+1}: brand={brand}, link={str(link)[:50]}...")
                
            else:
                file_info["status"] = "no_target_sheet"
                print(f"  未找到目标sheet '{self.sheet_name}'")
                print(f"  可用sheets: {excel_file.sheet_names}")
                
        except Exception as e:
            file_info["status"] = "error"
            file_info["error"] = str(e)
            print(f"  错误: {e}")
        
        self.file_stats.append(file_info)
    
    def save_analysis_result(self, result: Dict, output_file: str = "data_analysis_result.json"):
        """保存分析结果"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n分析结果已保存到: {output_file}")
    
    def print_summary(self, result: Dict):
        """打印分析摘要"""
        print("\n" + "="*60)
        print("数据分析摘要")
        print("="*60)
        print(f"分析时间: {result['analysis_time']}")
        print(f"处理文件数: {result['total_files_processed']}")
        print(f"品牌总数: {result['unique_brands_count']}")
        print(f"项目总数: {result['unique_projects_count']}")
        
        print(f"\n文件处理详情:")
        for file_info in result['file_details']:
            status_map = {
                "success": "成功",
                "no_target_sheet": "缺少目标sheet",
                "error": "处理错误"
            }
            status = status_map.get(file_info['status'], file_info['status'])
            print(f"  {file_info['filename']}: {status}")
            if file_info['status'] == 'success':
                print(f"    - 品牌: {file_info['brands_in_file']} 个")
                print(f"    - 项目: {file_info['projects_in_file']} 个")
        
        if result['unique_brands_count'] > 0:
            print(f"\n品牌示例 (前10个):")
            for brand in sorted(result['unique_brands'])[:10]:
                print(f"  - {brand}")
            if len(result['unique_brands']) > 10:
                print(f"  ... 还有 {len(result['unique_brands']) - 10} 个品牌")


def main():
    """主函数"""
    analyzer = DataAnalyzer()
    
    # 检查data文件夹是否存在
    if not os.path.exists(analyzer.data_folder):
        print(f"错误: 未找到数据文件夹 '{analyzer.data_folder}'")
        return
    
    try:
        # 执行分析
        result = analyzer.analyze_excel_files()
        
        # 打印摘要
        analyzer.print_summary(result)
        
        # 保存结果
        analyzer.save_analysis_result(result)
        
        # 生成Web界面数据
        web_data = {
            "brands_count": result['unique_brands_count'],
            "projects_count": result['unique_projects_count'],
            "last_updated": result['analysis_time'],
            "total_files": result['total_files_processed']
        }
        
        with open("web_data.json", 'w', encoding='utf-8') as f:
            json.dump(web_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nWeb界面数据已生成: web_data.json")
        
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()