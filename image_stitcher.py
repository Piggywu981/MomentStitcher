#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朋友圈拼图程序
将多张图片垂直拼接成长图
"""

import os
import sys
from PIL import Image
from pathlib import Path

class ImageStitcher:
    def __init__(self, input_dir="input", output_dir="output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_images(self):
        """获取input文件夹中的所有图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        images = []
        
        if not self.input_dir.exists():
            print(f"输入文件夹 {self.input_dir} 不存在")
            return images
            
        for file in self.input_dir.iterdir():
            if file.suffix.lower() in image_extensions:
                images.append(file)
        
        images.sort(key=lambda x: x.name)
        return images
    
    def stitch_images(self, images_per_group=9):
        """将图片拼接成长图"""
        all_images = self.get_images()
        
        if not all_images:
            print("没有找到图片文件")
            return
        
        # 计算需要生成多少组长图
        total_groups = (len(all_images) + images_per_group - 1) // images_per_group
        
        for group_num in range(total_groups):
            start_idx = group_num * images_per_group
            end_idx = min((group_num + 1) * images_per_group, len(all_images))
            group_images = all_images[start_idx:end_idx]
            
            if not group_images:
                continue
            
            # 加载并处理图片
            pil_images = []
            
            # 首先加载所有图片并找到最短横边
            temp_images = []
            min_width = float('inf')
            
            for img_path in group_images:
                try:
                    img = Image.open(img_path)
                    # 转换为RGB模式（处理RGBA图片）
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    temp_images.append(img)
                    min_width = min(min_width, img.width)
                    
                except Exception as e:
                    print(f"处理图片 {img_path.name} 时出错: {e}")
                    continue
            
            if not temp_images:
                continue
            
            print(f"组{group_num + 1}: 最短横边为 {min_width} 像素")
            
            # 将所有图片缩放到最短横边，保持宽高比
            total_height = 0
            for img in temp_images:
                # 计算缩放后的高度
                scale_ratio = min_width / img.width
                new_height = int(img.height * scale_ratio)
                
                # 缩放图片
                resized_img = img.resize((min_width, new_height), Image.Resampling.LANCZOS)
                pil_images.append(resized_img)
                total_height += new_height
            
            if not pil_images:
                continue
            
            # 创建长图
            final_img = Image.new('RGB', (min_width, total_height), (255, 255, 255))
            
            # 拼接图片
            y_offset = 0
            for img in pil_images:
                final_img.paste(img, (0, y_offset))
                y_offset += img.height
            
            # 保存结果
            if total_groups == 1:
                output_name = "stitched_long_image.jpg"
            else:
                output_name = f"stitched_long_image_part{group_num + 1}.jpg"
            
            output_path = self.output_dir / output_name
            final_img.save(output_path, 'JPEG', quality=95)
            print(f"已生成: {output_name} ({len(pil_images)}张图片)")
    
    def run(self, images_per_group=9):
        """运行拼图程序"""
        print(f"开始处理图片...")
        print(f"输入目录: {self.input_dir}")
        print(f"输出目录: {self.output_dir}")
        print(f"每组图片数量: {images_per_group}")
        
        self.stitch_images(images_per_group)
        
        print("处理完成！")

def main():
    print("=== 朋友圈拼图程序 ===")
    print("欢迎使用交互式拼图系统！")
    print()
    
    # 交互式输入参数
    try:
        # 输入文件夹
        input_dir = input("请输入输入图片文件夹路径 (直接回车使用默认值 'input'): ").strip()
        if not input_dir:
            input_dir = "input"
        
        # 输出文件夹
        output_dir = input("请输入输出图片文件夹路径 (直接回车使用默认值 'output'): ").strip()
        if not output_dir:
            output_dir = "output"
        
        # 每组图片数量
        while True:
            try:
                num_str = input("请输入每组拼接的图片数量 (直接回车使用默认值 9): ").strip()
                if not num_str:
                    images_per_group = 9
                else:
                    images_per_group = int(num_str)
                
                if images_per_group <= 0:
                    print("请输入大于0的数字")
                    continue
                break
            except ValueError:
                print("请输入有效的数字")
                continue
        
        print()
        print("配置完成：")
        print(f"输入文件夹: {input_dir}")
        print(f"输出文件夹: {output_dir}")
        print(f"每组图片数量: {images_per_group}")
        print()
        
        # 确认继续
        confirm = input("确认开始拼图吗？(y/n，默认y): ").strip().lower()
        if confirm in ('', 'y', 'yes'):
            stitcher = ImageStitcher(input_dir, output_dir)
            stitcher.run(images_per_group)
        else:
            print("已取消操作")
            
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()