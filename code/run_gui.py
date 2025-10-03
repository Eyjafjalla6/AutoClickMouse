#!/usr/bin/env python3
"""
启动智能自动点击器GUI界面
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from autoclick_gui import main
    print("正在启动智能自动点击器...")
    print("功能说明:")
    print("1. 图片匹配点击 - 通过图像识别自动点击指定位置")
    print("2. 时间延迟 - 在操作序列中添加等待时间")  
    print("3. 鼠标拖动匹配 - 拖动屏幕直到找到目标图片并点击")
    print("4. 支持保存/加载配置，操作序列管理")
    print()
    print("请确保已安装以下依赖:")
    print("- tkinter (Python GUI库)")
    print("- opencv-python (图像处理)")
    print("- pyautogui (自动化控制)")
    print("- Pillow (图像处理)")
    print()
    main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有必要的依赖包:")
    print("pip install opencv-python pyautogui Pillow")
except Exception as e:
    print(f"启动失败: {e}")
