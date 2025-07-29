#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证组内排序功能
"""

import os
import sys
import time
from PIL import Image

def create_test_images_for_sorting():
    """创建用于测试排序的图片"""
    test_dir = os.path.join(os.path.dirname(__file__), "test_sorting")
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建不同名称、大小、时间的测试图片
    images = [
        {"name": "z_image.jpg", "size": (400, 300), "color": (255, 0, 0)},
        {"name": "a_image.jpg", "size": (200, 150), "color": (0, 255, 0)},
        {"name": "m_image.jpg", "size": (600, 450), "color": (0, 0, 255)},
        {"name": "b_image.jpg", "size": (300, 225), "color": (255, 255, 0)},
    ]
    
    created_files = []
    for i, img_info in enumerate(images):
        file_path = os.path.join(test_dir, img_info["name"])
        
        # 创建图片
        img = Image.new('RGB', img_info["size"], img_info["color"])
        img.save(file_path, 'JPEG', quality=95)
        
        # 设置不同的修改时间
        new_mtime = time.time() + (i * 3600)  # 每小时一个文件
        os.utime(file_path, (new_mtime, new_mtime))
        
        created_files.append(file_path)
        print(f"创建测试图片: {file_path}")
    
    return test_dir, created_files

def test_sorting_functionality():
    """测试排序功能"""
    try:
        # 创建测试图片
        test_dir, test_files = create_test_images_for_sorting()
        
        # 模拟排序逻辑
        print("测试组内排序功能...")
        
        # 测试按名称排序
        files_by_name = sorted(test_files, key=lambda x: os.path.basename(x).lower())
        print(f"\n按名称排序:")
        for i, file_path in enumerate(files_by_name):
            print(f"  {i+1}. {os.path.basename(file_path)}")
        
        # 测试按大小排序
        files_by_size = sorted(test_files, key=lambda x: os.path.getsize(x), reverse=True)
        print(f"\n按大小排序:")
        for i, file_path in enumerate(files_by_size):
            size = os.path.getsize(file_path)
            print(f"  {i+1}. {os.path.basename(file_path)} ({size} bytes)")
        
        # 测试按时间排序
        files_by_time = sorted(test_files, key=lambda x: os.path.getmtime(x), reverse=True)
        print(f"\n按时间排序:")
        for i, file_path in enumerate(files_by_time):
            mtime = os.path.getmtime(file_path)
            print(f"  {i+1}. {os.path.basename(file_path)} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))})")
        
        print(f"\n✅ 组内排序功能逻辑测试完成！")
        
        # 清理测试文件
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sorting_functionality()