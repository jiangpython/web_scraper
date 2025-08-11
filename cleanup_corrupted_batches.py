#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理损坏的batch文件
"""

import os
import json

def cleanup_corrupted_batch_files():
    """清理损坏的batch JSON文件"""
    details_dir = "output/details"
    
    if not os.path.exists(details_dir):
        print("details目录不存在")
        return
    
    print("=== 清理损坏的batch文件 ===")
    
    batch_files = [f for f in os.listdir(details_dir) 
                   if f.startswith('batch_') and f.endswith('.json')]
    
    print(f"发现 {len(batch_files)} 个batch文件")
    
    valid_files = []
    corrupted_files = []
    
    for batch_file in batch_files:
        file_path = os.path.join(details_dir, batch_file)
        file_size = os.path.getsize(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            valid_files.append((batch_file, file_size))
            print(f"[OK] 正常: {batch_file} ({file_size} bytes)")
        except json.JSONDecodeError:
            corrupted_files.append((batch_file, file_size))
            print(f"[BAD] 损坏: {batch_file} ({file_size} bytes)")
    
    print(f"\n总结:")
    print(f"  正常文件: {len(valid_files)} 个")
    print(f"  损坏文件: {len(corrupted_files)} 个")
    
    if corrupted_files:
        print(f"\n是否删除损坏文件? (y/N)")
        choice = input().strip().lower()
        
        if choice in ['y', 'yes']:
            deleted_count = 0
            for batch_file, file_size in corrupted_files:
                file_path = os.path.join(details_dir, batch_file)
                try:
                    os.remove(file_path)
                    print(f"已删除: {batch_file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除失败 {batch_file}: {e}")
            
            print(f"\n已删除 {deleted_count} 个损坏文件")
        else:
            print("跳过删除操作")
    
    print("\n=== 清理完成 ===")

if __name__ == "__main__":
    cleanup_corrupted_batch_files()