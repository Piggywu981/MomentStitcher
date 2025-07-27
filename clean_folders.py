#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件夹清理工具
用于清空input或output文件夹内的文件
"""

import os
import sys
from pathlib import Path

def clear_folder(folder_path, folder_name):
    """清空指定文件夹内的所有文件"""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"文件夹 {folder_name} ({folder_path}) 不存在")
        return False
    
    if not folder.is_dir():
        print(f"{folder_name} ({folder_path}) 不是有效的文件夹")
        return False
    
    # 获取文件夹内的所有文件
    files = list(folder.iterdir())
    
    if not files:
        print(f"文件夹 {folder_name} ({folder_path}) 已经是空的")
        return True
    
    print(f"文件夹 {folder_name} ({folder_path}) 包含以下文件：")
    file_count = 0
    for file in files:
        if file.is_file():
            print(f"  - {file.name}")
            file_count += 1
    
    if file_count == 0:
        print("文件夹内没有文件")
        return True
    
    # 确认删除
    confirm = input(f"\n确认要删除 {folder_name} 文件夹内的 {file_count} 个文件吗？(y/n): ").strip().lower()
    
    if confirm in ('y', 'yes'):
        deleted_count = 0
        for file in files:
            if file.is_file():
                try:
                    file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"删除文件 {file.name} 时出错: {e}")
        
        print(f"已成功删除 {deleted_count} 个文件")
        return True
    else:
        print("已取消操作")
        return False

def main():
    """主函数 - 交互式菜单"""
    print("=== 文件夹清理工具 ===")
    print("用于清空input或output文件夹内的文件")
    print()
    
    try:
        while True:
            print("\n请选择操作：")
            print("1. 清空input文件夹")
            print("2. 清空output文件夹")
            print("3. 清空input和output两个文件夹")
            print("4. 退出")
            
            choice = input("\n请输入选项 (1-4): ").strip()
            
            if choice == '1':
                clear_folder("input", "input")
            elif choice == '2':
                clear_folder("output", "output")
            elif choice == '3':
                print("\n--- 清空input文件夹 ---")
                clear_folder("input", "input")
                print("\n--- 清空output文件夹 ---")
                clear_folder("output", "output")
            elif choice == '4':
                print("感谢使用，再见！")
                break
            else:
                print("请输入有效的选项 (1-4)")
                
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()