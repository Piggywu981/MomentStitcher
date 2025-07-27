#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 创建示例图片用于测试拼图功能
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_images():
    """创建测试图片"""
    input_dir = "input"
    os.makedirs(input_dir, exist_ok=True)
    
    # 创建不同颜色的测试图片
    colors = [
        (255, 100, 100),   # 红色
        (100, 255, 100),   # 绿色
        (100, 100, 255),   # 蓝色
        (255, 255, 100),   # 黄色
        (255, 100, 255),   # 紫色
        (100, 255, 255),   # 青色
        (255, 200, 100),   # 橙色
        (200, 100, 255),   # 紫红
        (100, 200, 255),   # 天蓝
    ]
    
    for i, color in enumerate(colors, 1):
        # 创建不同尺寸的图片
        width = 400 + (i % 3) * 100  # 400-600像素宽度
        height = 300 + (i % 3) * 50  # 300-400像素高度
        
        img = Image.new('RGB', (width, height), color)
        draw = ImageDraw.Draw(img)
        
        # 添加文字
        try:
            font = ImageFont.load_default()
            text = f"Test {i}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2
            draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
        except:
            draw.text((width//2-30, height//2), f"Test {i}", fill=(255, 255, 255))
        
        img.save(f"{input_dir}/test_{i:02d}.jpg", 'JPEG', quality=95)
        print(f"已创建: test_{i:02d}.jpg ({width}x{height})")

if __name__ == "__main__":
    create_test_images()
    print("测试图片创建完成！请运行: python image_stitcher.py")