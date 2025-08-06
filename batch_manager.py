#!/usr/bin/env python3
"""
批次文件管理工具
"""

import os
import json
from datetime import datetime

def list_batches():
    """列出所有批次文件"""
    details_dir = "output/details"
    index_file = os.path.join(details_dir, "batch_index.json")
    
    if not os.path.exists(details_dir):
        print("✗ 未找到details目录")
        return
    
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        print("=" * 60)
        print("批次文件列表")
        print("=" * 60)
        
        for batch in index_data.get("batches", []):
            print(f"批次ID: {batch['batch_id']}")
            print(f"文件路径: {batch['file_path']}")
            print(f"项目数量: {batch['project_count']}")
            print(f"创建时间: {batch['created_at']}")
            print("-" * 40)
    else:
        print("✗ 未找到批次索引文件")
        
        # 手动扫描目录
        batch_files = []
        for file in os.listdir(details_dir):
            if file.startswith("projects_batch_") and file.endswith(".json"):
                batch_files.append(file)
        
        if batch_files:
            print("发现以下批次文件:")
            for file in sorted(batch_files):
                print(f"  - {file}")
        else:
            print("未发现任何批次文件")

def view_batch(batch_id):
    """查看特定批次的内容"""
    details_dir = "output/details"
    index_file = os.path.join(details_dir, "batch_index.json")
    
    if not os.path.exists(index_file):
        print("✗ 未找到批次索引文件")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    # 查找指定批次
    target_batch = None
    for batch in index_data.get("batches", []):
        if batch["batch_id"] == batch_id:
            target_batch = batch
            break
    
    if not target_batch:
        print(f"✗ 未找到批次 {batch_id}")
        return
    
    # 读取批次文件
    batch_file = os.path.join(details_dir, target_batch["file_path"])
    if not os.path.exists(batch_file):
        print(f"✗ 批次文件不存在: {batch_file}")
        return
    
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch_data = json.load(f)
    
    print(f"=" * 60)
    print(f"批次 {batch_id} 详情")
    print(f"=" * 60)
    print(f"文件: {target_batch['file_path']}")
    print(f"项目数量: {target_batch['project_count']}")
    print(f"创建时间: {target_batch['created_at']}")
    print(f"批次信息: {batch_data['batch_info']}")
    print(f"\n项目列表:")
    
    for i, project in enumerate(batch_data['projects'][:5], 1):  # 只显示前5个
        print(f"{i}. {project.get('title', 'N/A')}")
        print(f"   URL: {project.get('url', 'N/A')}")
        print(f"   品牌: {project.get('brand', 'N/A')}")
        print(f"   代理商: {project.get('agency', 'N/A')}")
        print()
    
    if len(batch_data['projects']) > 5:
        print(f"... 还有 {len(batch_data['projects']) - 5} 个项目")

def cleanup_old_batches(keep_count=5):
    """清理旧的批次文件，只保留最新的几个"""
    details_dir = "output/details"
    index_file = os.path.join(details_dir, "batch_index.json")
    
    if not os.path.exists(index_file):
        print("✗ 未找到批次索引文件")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    batches = index_data.get("batches", [])
    if len(batches) <= keep_count:
        print(f"当前只有 {len(batches)} 个批次文件，无需清理")
        return
    
    # 按创建时间排序
    batches.sort(key=lambda x: x['created_at'], reverse=True)
    
    # 需要删除的批次
    to_delete = batches[keep_count:]
    
    print(f"将删除 {len(to_delete)} 个旧批次文件:")
    for batch in to_delete:
        print(f"  - {batch['file_path']} (创建于 {batch['created_at']})")
    
    # 确认删除
    confirm = input("\n确认删除？(y/N): ").strip().lower()
    if confirm != 'y':
        print("取消删除")
        return
    
    # 执行删除
    deleted_count = 0
    for batch in to_delete:
        file_path = os.path.join(details_dir, batch["file_path"])
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted_count += 1
            print(f"✓ 已删除: {batch['file_path']}")
    
    # 更新索引文件
    index_data["batches"] = batches[:keep_count]
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 清理完成，删除了 {deleted_count} 个文件")

def main():
    """主函数"""
    print("批次文件管理工具")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 列出所有批次")
        print("2. 查看特定批次")
        print("3. 清理旧批次文件")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            list_batches()
        elif choice == "2":
            batch_id = input("请输入批次ID (如: 001): ").strip()
            view_batch(batch_id)
        elif choice == "3":
            keep_count = input("保留最新的批次数量 (默认5): ").strip()
            keep_count = int(keep_count) if keep_count.isdigit() else 5
            cleanup_old_batches(keep_count)
        elif choice == "4":
            print("退出程序")
            break
        else:
            print("无效选择")

if __name__ == "__main__":
    main() 