#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件结构分析器
用于分析data文件夹中Excel文件的结构和内容
"""

import pandas as pd
import os
import sys
from pathlib import Path

def analyze_excel_file(file_path):
    """分析单个Excel文件"""
    print(f"\n{'='*60}")
    print(f"分析文件: {file_path}")
    print(f"{'='*60}")
    
    try:
        # 获取所有sheet名称
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"Sheet数量: {len(sheet_names)}")
        print(f"Sheet名称: {sheet_names}")
        
        # 检查是否有"所有项目合并"sheet
        target_sheet = "所有项目合并"
        has_target_sheet = target_sheet in sheet_names
        print(f"是否包含'{target_sheet}' sheet: {has_target_sheet}")
        
        if has_target_sheet:
            # 读取目标sheet
            df = pd.read_excel(file_path, sheet_name=target_sheet)
            print(f"\n'{target_sheet}' Sheet分析:")
            print(f"数据行数: {len(df)}")
            print(f"数据列数: {len(df.columns)}")
            print(f"列名: {list(df.columns)}")
            
            # 检查brand和link字段
            brand_exists = 'brand' in df.columns
            link_exists = 'link' in df.columns
            print(f"\n字段检查:")
            print(f"包含 'brand' 字段: {brand_exists}")
            print(f"包含 'link' 字段: {link_exists}")
            
            # 如果存在这些字段，展示一些样本数据
            if brand_exists:
                print(f"\n'brand' 字段分析:")
                print(f"非空值数量: {df['brand'].notna().sum()}")
                print(f"唯一值数量: {df['brand'].nunique()}")
                brand_samples = df['brand'].dropna().head(5).tolist()
                print(f"样本值: {brand_samples}")
            
            if link_exists:
                print(f"\n'link' 字段分析:")
                print(f"非空值数量: {df['link'].notna().sum()}")
                print(f"唯一值数量: {df['link'].nunique()}")
                link_samples = df['link'].dropna().head(3).tolist()
                print(f"样本值: {link_samples}")
            
            # 展示前几行数据的结构
            print(f"\n数据样本 (前3行):")
            print(df.head(3).to_string(max_cols=10, max_colwidth=50))
            
            # 数据质量检查
            print(f"\n数据质量分析:")
            total_rows = len(df)
            for col in df.columns:
                null_count = df[col].isnull().sum()
                null_percent = (null_count / total_rows) * 100
                print(f"{col}: 缺失值 {null_count}/{total_rows} ({null_percent:.1f}%)")
        
        else:
            # 如果没有目标sheet，查看其他sheet的基本信息
            print(f"\n没有找到'{target_sheet}' sheet，查看其他sheet:")
            for sheet in sheet_names[:2]:  # 只查看前2个sheet
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    print(f"\nSheet '{sheet}':")
                    print(f"  行数: {len(df)}")
                    print(f"  列数: {len(df.columns)}")
                    print(f"  列名: {list(df.columns)[:10]}")  # 只显示前10列
                except Exception as e:
                    print(f"  读取失败: {e}")
        
    except Exception as e:
        print(f"分析文件时出错: {e}")

def main():
    """主函数"""
    data_folder = Path("D:/项目/网页爬虫/data")
    
    if not data_folder.exists():
        print(f"数据文件夹不存在: {data_folder}")
        return
    
    # 获取所有xlsx文件
    excel_files = list(data_folder.glob("*.xlsx"))
    excel_files = [f for f in excel_files if not f.name.startswith("~$")]  # 排除临时文件
    
    print(f"找到 {len(excel_files)} 个Excel文件")
    
    # 选择3个文件进行分析
    files_to_analyze = [
        "digitaling_all_projects_20250721_170404.xlsx",
        "digitaling_projects_final_20250729_141757.xlsx", 
        "digitaling_projects_final_20250806_095833.xlsx"
    ]
    
    for filename in files_to_analyze:
        file_path = data_folder / filename
        if file_path.exists():
            analyze_excel_file(str(file_path))
        else:
            print(f"\n文件不存在: {filename}")

if __name__ == "__main__":
    main()