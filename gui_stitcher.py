#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
朋友圈拼图程序 - PyQt5图形界面版
将多张图片垂直拼接成长图的可视化工具
"""

__version__ = "2.2.1"

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QSpinBox, QProgressBar, QTextEdit, QMessageBox,
                             QGroupBox, QGridLayout, QListWidget, QListWidgetItem, 
                             QAbstractItemView, QSplitter, QSizePolicy, QProgressDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize
from PyQt5.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QFont, QIcon
from PIL import Image

class GroupWidget(QWidget):
    """分组组件，支持拖拽"""
    
    def __init__(self, group_name, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.images = []
        self.init_ui()
        self.setAcceptDrops(True)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 分组标题
        title_label = QLabel(self.group_name)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; background-color: #e0e0e0; padding: 5px;")
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(title_label)
        
        # 排序按钮区域 - 使用水平布局并设置伸缩
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(2)
        
        self.sort_name_btn = QPushButton("按名称")
        self.sort_name_btn.clicked.connect(lambda: self.sort_images('name'))
        self.sort_name_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sort_layout.addWidget(self.sort_name_btn)
        
        self.sort_size_btn = QPushButton("按大小")
        self.sort_size_btn.clicked.connect(lambda: self.sort_images('size'))
        self.sort_size_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sort_layout.addWidget(self.sort_size_btn)
        
        self.sort_time_btn = QPushButton("按时间")
        self.sort_time_btn.clicked.connect(lambda: self.sort_images('time'))
        self.sort_time_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sort_layout.addWidget(self.sort_time_btn)
        
        layout.addLayout(sort_layout)
        
        # 图片列表 - 设置为可伸缩
        self.image_list = QListWidget()
        self.image_list.setIconSize(QSize(50, 50))
        self.image_list.setStyleSheet("QListWidget::item { height: 60px; }")
        self.image_list.setDragEnabled(True)
        self.image_list.setAcceptDrops(True)
        self.image_list.setDefaultDropAction(Qt.MoveAction)
        self.image_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.image_list)
        
        # 删除按钮
        self.remove_btn = QPushButton("清空分组")
        self.remove_btn.clicked.connect(self.clear_group)
        self.remove_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.remove_btn)
    
    def add_image(self, image_path):
        """添加图片到分组"""
        item = QListWidgetItem()
        item.setText(os.path.basename(image_path))
        item.setData(Qt.UserRole, image_path)
        
        # 添加缩略图
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item.setIcon(QIcon(scaled))
        except Exception:
            pass
            
        self.image_list.addItem(item)
        self.images.append(image_path)
    
    def clear_group(self):
        """清空分组"""
        self.image_list.clear()
        self.images.clear()
        # 更新主窗口的总图片数量显示
        if hasattr(self.window(), 'update_total_images'):
            self.window().update_total_images()
    
    def get_images(self):
        """获取分组中的图片"""
        # 确保返回当前实际的图片列表
        current_images = []
        for i in range(self.image_list.count()):
            item = self.image_list.item(i)
            if item:
                current_images.append(item.data(Qt.UserRole))
        self.images = current_images  # 同步缓存
        return current_images
    
    def sort_images(self, sort_by='name'):
        """组内排序功能（带进度条）
        
        Args:
            sort_by: 排序方式 'name', 'size', 'time'
        """
        if not self.images:
            return
            
        # 创建进度对话框
        parent = self.window()
        progress = QProgressDialog("正在排序组内图片...", "取消", 0, 100, parent)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        progress.show()
        
        try:
            # 获取当前实际在列表中的图片
            current_images = []
            for i in range(self.image_list.count()):
                item = self.image_list.item(i)
                if item:
                    current_images.append(item.data(Qt.UserRole))
            
            if not current_images:
                progress.close()
                return
                
            total_images = len(current_images)
            progress.setMaximum(total_images)
            
            # 获取图片信息列表
            image_info = []
            for idx, img_path in enumerate(current_images):
                if progress.wasCanceled():
                    progress.close()
                    return
                    
                try:
                    stat = os.stat(img_path)
                    info = {
                        'path': img_path,
                        'name': os.path.basename(img_path),
                        'size': stat.st_size,
                        'mtime': stat.st_mtime
                    }
                    image_info.append(info)
                except (OSError, IOError):
                    image_info.append({
                        'path': img_path,
                        'name': os.path.basename(img_path),
                        'size': 0,
                        'mtime': 0
                    })
                
                progress.setValue(idx + 1)
                QApplication.processEvents()
            
            # 根据排序方式进行排序
            if sort_by == 'name':
                image_info.sort(key=lambda x: x['name'].lower())
            elif sort_by == 'size':
                image_info.sort(key=lambda x: x['size'], reverse=True)
            elif sort_by == 'time':
                image_info.sort(key=lambda x: x['mtime'], reverse=True)
            
            # 清空当前列表并重新添加排序后的图片
            self.image_list.clear()
            self.images.clear()
            
            for idx, info in enumerate(image_info):
                if progress.wasCanceled():
                    progress.close()
                    return
                    
                self.add_image(info['path'])
                progress.setValue(idx + 1)
                QApplication.processEvents()
                
            progress.close()
            
            # 通知主窗口更新
            if hasattr(self.window(), 'update_total_images'):
                self.window().update_total_images()
                
        except Exception as e:
            progress.close()
            print(f"排序失败: {e}")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    self.add_image(url.toLocalFile())
        elif event.mimeData().hasText():
            image_path = event.mimeData().text()
            if os.path.exists(image_path):
                self.add_image(image_path)
        event.acceptProposedAction()
        # 通知主窗口更新总图片数量
        if hasattr(self.window(), 'update_total_images'):
            self.window().update_total_images()

class ImageStitcherThread(QThread):
    """后台处理线程"""
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, output_dir, image_groups):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.image_groups = image_groups  # 现在是分组后的图片列表
        
    def run(self):
        """后台执行拼图操作（带详细进度）"""
        try:
            self.log_message.emit("开始处理图片...")
            self.output_dir.mkdir(exist_ok=True)
            
            total_groups = len(self.image_groups)
            if total_groups == 0:
                self.finished_signal.emit(False, "没有分组图片")
                return
            
            # 计算总处理步骤数
            total_steps = 0
            for group_images in self.image_groups:
                if len(group_images) >= 2:
                    total_steps += len(group_images) + 3  # 加载+缩放+创建+保存
            
            current_step = 0
            
            for group_num, group_images in enumerate(self.image_groups):
                if len(group_images) < 2:
                    self.log_message.emit(f"第{group_num+1}组图片数量不足，跳过")
                    continue
                
                self.log_message.emit(f"开始处理第{group_num+1}组图片（共{len(group_images)}张）...")
                
                # 加载并处理图片
                pil_images = []
                min_width = float('inf')
                
                for idx, img_path in enumerate(group_images):
                    try:
                        self.log_message.emit(f"  加载图片: {Path(img_path).name}")
                        img = Image.open(img_path)
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        pil_images.append((img, img_path))
                        min_width = min(min_width, img.width)
                        
                    except Exception as e:
                        self.log_message.emit(f"  处理图片 {Path(img_path).name} 时出错: {e}")
                        continue
                    
                    current_step += 1
                    progress = int(current_step / total_steps * 100)
                    self.progress_updated.emit(progress)
                
                if not pil_images:
                    continue
                
                # 缩放图片
                self.log_message.emit("  正在缩放图片...")
                resized_images = []
                total_height = 0
                
                for img, path in pil_images:
                    scale_ratio = min_width / img.width
                    new_height = int(img.height * scale_ratio)
                    
                    resized_img = img.resize((min_width, new_height), Image.Resampling.LANCZOS)
                    resized_images.append(resized_img)
                    total_height += new_height
                    
                    current_step += 1
                    progress = int(current_step / total_steps * 100)
                    self.progress_updated.emit(progress)
                
                # 创建长图
                self.log_message.emit("  正在拼接图片...")
                final_img = Image.new('RGB', (min_width, total_height), (255, 255, 255))
                
                y_offset = 0
                for img in resized_images:
                    final_img.paste(img, (0, y_offset))
                    y_offset += img.height
                
                current_step += 1
                progress = int(current_step / total_steps * 100)
                self.progress_updated.emit(progress)
                
                # 保存结果
                if total_groups == 1:
                    output_name = "stitched_long_image.jpg"
                else:
                    output_name = f"stitched_long_image_part{group_num + 1}.jpg"
                
                output_path = self.output_dir / output_name
                self.log_message.emit(f"  保存图片: {output_name}")
                final_img.save(output_path, 'JPEG', quality=95)
                
                current_step += 1
                progress = int(current_step / total_steps * 100)
                self.progress_updated.emit(progress)
                
                self.log_message.emit(f"已生成: {output_name} ({len(resized_images)}张图片)")
            
            self.finished_signal.emit(True, f"处理完成！共生成 {total_groups} 张长图")
            
        except Exception as e:
            self.finished_signal.emit(False, f"处理失败: {str(e)}")

class DragDropLabel(QLabel):
    """支持拖拽的自定义标签"""
    files_dropped = pyqtSignal(list)
    
    def __init__(self, text=""):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f9f9f9;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
        if files:
            self.files_dropped.emit(files)

class ImageStitcherGUI(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.input_dir = ""
        self.output_dir = ""
        self.thread = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('MomentStitcher - 朋友圈长图拼接工具')
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置最小窗口尺寸
        self.setMinimumSize(800, 600)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        central_widget.setLayout(main_layout)
        
        # 标题 - 设置伸缩性
        title = QLabel('MomentStitcher - 朋友圈长图拼接工具')
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        main_layout.addWidget(title)
        
        # 创建分割器 - 设置伸缩比例
        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 左侧分组管理区域
        left_widget = QWidget()
        left_widget.setMinimumWidth(400)
        left_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # 分组控制
        group_control_layout = QHBoxLayout()
        group_control_layout.addWidget(QLabel("每组图片数量:"))
        self.group_size_spinbox = QSpinBox()
        self.group_size_spinbox.setRange(2, 20)
        self.group_size_spinbox.setValue(9)
        self.group_size_spinbox.valueChanged.connect(self.on_group_size_changed)
        group_control_layout.addWidget(self.group_size_spinbox)

        self.auto_group_btn = QPushButton("自动分组")
        self.auto_group_btn.clicked.connect(lambda: self.auto_group_images())
        group_control_layout.addWidget(self.auto_group_btn)
        left_layout.addLayout(group_control_layout)

        # 图片数量显示
        self.total_images_label = QLabel("共 0 张输出图片")
        self.total_images_label.setAlignment(Qt.AlignCenter)
        self.total_images_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.total_images_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(self.total_images_label)

        # 分组显示区域
        groups_label = QLabel("图片分组:")
        groups_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(groups_label)

        # 创建分组网格布局容器
        self.groups_scroll = QWidget()
        self.groups_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.groups_layout = QGridLayout(self.groups_scroll)
        self.groups_layout.setContentsMargins(0, 0, 0, 0)
        self.groups_layout.setSpacing(10)
        left_layout.addWidget(self.groups_scroll)

        # 图片池（未分组图片）
        pool_label = QLabel("未分组图片:")
        pool_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        left_layout.addWidget(pool_label)
        
        # 未分组图片排序按钮
        pool_sort_layout = QHBoxLayout()
        pool_sort_layout.setSpacing(2)
        
        self.pool_sort_name_btn = QPushButton("按名称")
        self.pool_sort_name_btn.clicked.connect(lambda: self.sort_unassigned_images('name'))
        self.pool_sort_name_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pool_sort_layout.addWidget(self.pool_sort_name_btn)
        
        self.pool_sort_size_btn = QPushButton("按大小")
        self.pool_sort_size_btn.clicked.connect(lambda: self.sort_unassigned_images('size'))
        self.pool_sort_size_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pool_sort_layout.addWidget(self.pool_sort_size_btn)
        
        self.pool_sort_time_btn = QPushButton("按时间")
        self.pool_sort_time_btn.clicked.connect(lambda: self.sort_unassigned_images('time'))
        self.pool_sort_time_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pool_sort_layout.addWidget(self.pool_sort_time_btn)
        
        left_layout.addLayout(pool_sort_layout)
        
        self.image_pool = QListWidget()
        self.image_pool.setIconSize(QSize(60, 60))
        self.image_pool.setStyleSheet("QListWidget::item { height: 70px; }")
        self.image_pool.setDragEnabled(True)
        self.image_pool.setDefaultDropAction(Qt.MoveAction)
        self.image_pool.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.image_pool.setFixedHeight(150)
        left_layout.addWidget(self.image_pool)
        
        splitter.addWidget(left_widget)
        
        # 右侧参数设置和处理区域
        right_widget = QWidget()
        right_widget.setMinimumWidth(350)
        right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 参数设置区域
        params_group = QGroupBox("参数设置")
        params_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        params_layout = QGridLayout()
        params_layout.setContentsMargins(10, 10, 10, 10)
        params_group.setLayout(params_layout)
        
        # 输入目录
        params_layout.addWidget(QLabel("输入目录:"), 0, 0)
        self.input_label = QLabel("未选择")
        self.input_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_label.setMinimumWidth(150)
        params_layout.addWidget(self.input_label, 0, 1)
        self.input_btn = QPushButton("选择输入目录")
        self.input_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.input_btn.clicked.connect(self.select_input_dir)
        params_layout.addWidget(self.input_btn, 0, 2)
        
        # 输出目录
        params_layout.addWidget(QLabel("输出目录:"), 1, 0)
        self.output_label = QLabel("未选择")
        self.output_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.output_label.setMinimumWidth(150)
        params_layout.addWidget(self.output_label, 1, 1)
        self.output_btn = QPushButton("选择输出目录")
        self.output_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.output_btn.clicked.connect(self.select_output_dir)
        params_layout.addWidget(self.output_btn, 1, 2)
        
        right_layout.addWidget(params_group)
        
        # 拖拽区域
        self.drop_label = DragDropLabel("拖拽图片或文件夹到此处\n支持批量处理")
        self.drop_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.drop_label.setMinimumHeight(80)
        self.drop_label.setMaximumHeight(120)
        self.drop_label.files_dropped.connect(self.handle_dropped_files)
        right_layout.addWidget(self.drop_label)
        
        # 日志区域
        log_group = QGroupBox("处理日志")
        log_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setFixedHeight(150)
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        log_layout.addWidget(self.log_text)
        
        right_layout.addWidget(log_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.start_btn = QPushButton("开始拼图")
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.clicked.connect(self.start_stitching_from_groups)
        self.start_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.stop_btn.clicked.connect(self.stop_stitching)
        self.stop_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("清空输出目录")
        self.clear_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.clear_btn.clicked.connect(self.clear_output_dir)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.clear_btn)
        
        right_layout.addLayout(button_layout)
        
        splitter.addWidget(right_widget)
        
        main_layout.addWidget(splitter)
        
        # 设置默认目录
        self.set_default_dirs()
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 6)  # 左侧占60%
        splitter.setStretchFactor(1, 4)  # 右侧占40%
        
        # 设置分割器可调整
        splitter.setHandleWidth(5)
        splitter.setChildrenCollapsible(False)
    
    def set_default_dirs(self):
        """设置默认目录"""
        input_path = Path("input")
        output_path = Path("output")
        
        if input_path.exists():
            self.input_dir = str(input_path)
            self.input_label.setText(str(input_path))
            self.load_images_to_list()
        
        if output_path.exists():
            self.output_dir = str(output_path)
            self.output_label.setText(str(output_path))
        
        self.check_start_button()
    
    def select_input_dir(self):
        """选择输入目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if directory:
            self.input_dir = directory
            self.input_label.setText(directory)
            self.load_images_to_list()
            self.check_start_button()
    
    def select_output_dir(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir = directory
            self.output_label.setText(directory)
            self.check_start_button()
    
    def handle_dropped_files(self, files):
        """处理拖拽的文件"""
        if files:
            # 如果是文件夹，设置为输入目录
            if os.path.isdir(files[0]):
                self.input_dir = files[0]
                self.input_label.setText(files[0])
            else:
                # 如果是文件，设置为文件所在目录
                dir_path = os.path.dirname(files[0])
                self.input_dir = dir_path
                self.input_label.setText(dir_path)
            
            self.load_images_to_list()
            self.check_start_button()
    
    def check_start_button(self):
        """检查是否可以开始处理"""
        enabled = bool(self.input_dir and self.output_dir and self.image_list.count() > 0)
        self.start_btn.setEnabled(enabled)

    def load_images_to_pool(self):
        """加载图片到未分组池"""
        self.image_pool.clear()
        if not self.input_dir or not os.path.exists(self.input_dir):
            self.update_total_images()
            return
            
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        input_path = Path(self.input_dir)
        
        images = []
        for file in input_path.iterdir():
            if file.suffix.lower() in image_extensions:
                images.append(file)
        
        images.sort(key=lambda x: x.name)
        
        for img_path in images:
            item = QListWidgetItem()
            item.setText(img_path.name)
            item.setData(Qt.UserRole, str(img_path))
            
            # 创建缩略图
            try:
                pixmap = QPixmap(str(img_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    item.setIcon(QIcon(scaled))
            except Exception:
                pass
                
            self.image_pool.addItem(item)
            
        self.image_pool.setIconSize(QSize(60, 60))
        self.update_total_images()
        self.log_message(f"已加载 {len(images)} 张图片到未分组池")

    def update_total_images(self):
        """更新总图片数量显示（显示预期输出长图数量）"""
        total_output_images = 0
        
        # 计算分组中的输出图片数量（每个有效分组输出1张长图）
        for i in range(self.groups_layout.count()):
            item = self.groups_layout.itemAt(i)
            if item and isinstance(item.widget(), GroupWidget):
                widget = item.widget()
                if widget.get_images():
                    total_output_images += 1
        
        self.total_images_label.setText(f"共 {total_output_images} 张输出图片")

    def on_group_size_changed(self, new_value):
        """处理分组大小变化"""
        self.auto_group_images()

    def sort_unassigned_images(self, sort_by='name'):
        """对未分组图片进行排序（带进度条）
        
        Args:
            sort_by: 排序方式 'name', 'size', 'time'
        """
        if self.image_pool.count() == 0:
            return
            
        # 创建进度对话框
        progress = QProgressDialog("正在排序图片...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        progress.show()
        
        try:
            # 获取所有未分组图片路径
            image_paths = []
            for i in range(self.image_pool.count()):
                item = self.image_pool.item(i)
                if item:
                    img_path = item.data(Qt.UserRole)
                    image_paths.append(img_path)
            
            if not image_paths:
                progress.close()
                return
                
            total_images = len(image_paths)
            progress.setMaximum(total_images)
            
            # 获取图片信息并排序
            image_info = []
            for idx, img_path in enumerate(image_paths):
                if progress.wasCanceled():
                    progress.close()
                    return
                    
                try:
                    stat = os.stat(img_path)
                    info = {
                        'path': img_path,
                        'name': os.path.basename(img_path),
                        'size': stat.st_size,
                        'mtime': stat.st_mtime
                    }
                    image_info.append(info)
                except (OSError, IOError):
                    image_info.append({
                        'path': img_path,
                        'name': os.path.basename(img_path),
                        'size': 0,
                        'mtime': 0
                    })
                
                progress.setValue(idx + 1)
                QApplication.processEvents()
            
            # 根据排序方式进行排序
            if sort_by == 'name':
                image_info.sort(key=lambda x: x['name'].lower())
            elif sort_by == 'size':
                image_info.sort(key=lambda x: x['size'], reverse=True)
            elif sort_by == 'time':
                image_info.sort(key=lambda x: x['mtime'], reverse=True)
            
            # 清空并重新创建项目
            self.image_pool.clear()
            for info in image_info:
                item = QListWidgetItem()
                item.setText(info['name'])
                item.setData(Qt.UserRole, info['path'])
                
                # 添加缩略图
                try:
                    pixmap = QPixmap(info['path'])
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(scaled))
                except Exception:
                    pass
                    
                self.image_pool.addItem(item)
            
            progress.close()
            self.log_message(f"未分组图片已按{sort_by}排序")
            
        except Exception as e:
            progress.close()
            self.log_message(f"排序失败: {e}")

    def auto_group_images(self):
        """根据设定的每组图片数量自动分组（带进度条）"""
        # 创建进度对话框
        progress = QProgressDialog("正在重新分组图片...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.setValue(0)
        progress.show()
        
        try:
            # 收集所有图片（包括已分组的和未分组的）
            all_images = []
            
            # 收集未分组池中的图片
            for i in range(self.image_pool.count()):
                item = self.image_pool.item(i)
                all_images.append(item.data(Qt.UserRole))
            
            # 收集所有分组中的图片
            for i in range(self.groups_layout.count()):
                group_widget = self.groups_layout.itemAt(i).widget()
                if isinstance(group_widget, GroupWidget):
                    group_images = group_widget.get_images()
                    all_images.extend(group_images)
            
            # 清空现有分组和未分组池
            self.clear_all_groups()
            self.image_pool.clear()
            
            if not all_images:
                progress.close()
                self.update_total_images()
                return
            
            total_images = len(all_images)
            progress.setMaximum(total_images)
            
            # 将所有图片重新放入未分组池
            for idx, img_path in enumerate(all_images):
                if progress.wasCanceled():
                    progress.close()
                    return
                    
                item = QListWidgetItem()
                item.setText(os.path.basename(img_path))
                item.setData(Qt.UserRole, img_path)
                
                # 添加缩略图
                try:
                    pixmap = QPixmap(img_path)
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        item.setIcon(QIcon(scaled))
                except Exception:
                    pass
                    
                self.image_pool.addItem(item)
                progress.setValue(idx + 1)
                QApplication.processEvents()
            
            # 重新进行自动分组
            group_size = self.group_size_spinbox.value()
            total_groups = (total_images + group_size - 1) // group_size
            
            # 计算最佳列数
            cols = max(2, min(4, (total_groups + 1) // 2))
            
            # 创建分组
            for i in range(total_groups):
                if progress.wasCanceled():
                    progress.close()
                    return
                    
                start_idx = i * group_size
                end_idx = min(start_idx + group_size, total_images)
                group_images = all_images[start_idx:end_idx]
                
                group_widget = GroupWidget(f"分组 {i+1}")
                for img_path in group_images:
                    group_widget.add_image(img_path)
                
                row = i // cols
                col = i % cols
                self.groups_layout.addWidget(group_widget, row, col)
                
                # 更新进度
                progress.setValue(int((i + 1) / total_groups * total_images))
                QApplication.processEvents()
            
            # 从未分组池中移除已分组的图片
            for i in range(self.image_pool.count() - 1, -1, -1):
                item = self.image_pool.item(i)
                if item and item.data(Qt.UserRole) in all_images[:total_groups * group_size]:
                    self.image_pool.takeItem(i)
            
            progress.close()
            self.update_total_images()
            self.log_message(f"已将 {total_images} 张图片重新分组，共创建 {total_groups} 个分组")
            self.check_start_button()
            
        except Exception as e:
            progress.close()
            self.log_message(f"分组失败: {e}")

    def clear_all_groups(self):
        """清空所有分组"""
        while self.groups_layout.count():
            child = self.groups_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.update_total_images()
        self.check_start_button()

    def add_empty_group(self):
        """添加空分组"""
        group_name = f"分组 {self.groups_layout.count() + 1}"
        group_widget = GroupWidget(group_name)
        
        # 计算网格位置
        count = self.groups_layout.count()
        cols = max(2, min(4, (count + 1) // 2 + 1))  # 根据分组数量动态调整列数
        row = count // cols
        col = count % cols
        
        self.groups_layout.addWidget(group_widget, row, col)
        self.update_total_images()
        self.check_start_button()

    def get_all_groups(self):
        """获取所有分组信息"""
        groups = []
        for i in range(self.groups_layout.count()):
            widget = self.groups_layout.itemAt(i).widget()
            if isinstance(widget, GroupWidget) and widget.get_images():
                groups.append(widget.get_images())
        return groups

    def start_stitching_from_groups(self):
        """从分组开始处理"""
        groups = self.get_all_groups()
        if not groups:
            QMessageBox.warning(self, "警告", "没有可处理的分组")
            return
        
        # 重置界面
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 启动线程
        self.thread = ImageStitcherThread(self.output_dir, groups)
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.log_message.connect(self.log_message)
        self.thread.finished_signal.connect(self.stitching_finished)
        self.thread.start()

    def set_default_dirs(self):
        """设置默认目录"""
        input_path = Path("input")
        output_path = Path("output")
        
        if input_path.exists():
            self.input_dir = str(input_path)
            self.input_label.setText(str(input_path))
            self.load_images_to_pool()
        
        if output_path.exists():
            self.output_dir = str(output_path)
            self.output_label.setText(str(output_path))
        
        self.check_start_button()

    def select_input_dir(self):
        """选择输入目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输入目录")
        if directory:
            self.input_dir = directory
            self.input_label.setText(directory)
            self.clear_all_groups()
            self.load_images_to_pool()
            self.check_start_button()

    def handle_dropped_files(self, files):
        """处理拖拽的文件"""
        if not files:
            return
            
        if os.path.isdir(files[0]):
            self.input_dir = files[0]
            self.input_label.setText(files[0])
            self.clear_all_groups()
            self.load_images_to_pool()
        else:
            # 处理拖拽的文件
            for file_path in files:
                if os.path.isfile(file_path):
                    item = QListWidgetItem()
                    item.setText(os.path.basename(file_path))
                    item.setData(Qt.UserRole, file_path)
                    
                    try:
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setIcon(QIcon(scaled))
                    except Exception:
                        pass
                        
                    self.image_pool.addItem(item)
        
        self.check_start_button()

    def check_start_button(self):
        """检查开始按钮状态"""
        has_groups = len(self.get_all_groups()) > 0
        self.start_btn.setEnabled(has_groups)


    

    
    def stop_stitching(self):
        """停止处理"""
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            self.stitching_finished(False, "用户取消操作")
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def stitching_finished(self, success, message):
        """处理完成回调"""
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "完成", message)
            # 打开输出目录
            if self.output_dir:
                os.startfile(self.output_dir)
        else:
            QMessageBox.warning(self, "错误", message)
    
    def clear_output_dir(self):
        """清空输出目录"""
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return
        
        reply = QMessageBox.question(self, "确认", 
                                     f"确定要清空输出目录 {self.output_dir} 吗？\n(将保留 .gitkeep 文件)",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            import shutil
            try:
                deleted_count = 0
                for item in os.listdir(self.output_dir):
                    if item == '.gitkeep':
                        continue  # 跳过.gitkeep文件
                    
                    item_path = os.path.join(self.output_dir, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                        deleted_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        deleted_count += 1
                
                QMessageBox.information(self, "完成", f"输出目录已清空，共删除 {deleted_count} 个项目")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清空失败: {str(e)}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("MomentStitcher")
    app.setApplicationVersion(__version__)
    app.setStyle('Fusion')
    
    window = ImageStitcherGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()