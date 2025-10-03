import time
import pyautogui
import cv2
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from PIL import Image, ImageTk
import threading

class AutoClickGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("智能自动点击器")
        self.root.geometry("800x600")
        
        # 存储操作序列
        self.operations = []
        self.current_operation = None
        self.is_running = False
        
        # 创建界面
        self.create_widgets()
        
        # 基础目录
        self.base_dir = "./code"
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 操作类型选择
        operation_frame = ttk.LabelFrame(main_frame, text="添加操作节点", padding="5")
        operation_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(operation_frame, text="图片匹配点击", 
                  command=self.add_image_click_node).grid(row=0, column=0, padx=5)
        ttk.Button(operation_frame, text="时间延迟", 
                  command=self.add_delay_node).grid(row=0, column=1, padx=5)
        ttk.Button(operation_frame, text="鼠标拖动", 
                  command=self.add_drag_node).grid(row=0, column=2, padx=5)
        
        # 操作序列显示
        sequence_frame = ttk.LabelFrame(main_frame, text="操作序列", padding="5")
        sequence_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        sequence_frame.columnconfigure(0, weight=1)
        sequence_frame.rowconfigure(0, weight=1)
        
        # 操作列表
        self.operation_listbox = tk.Listbox(sequence_frame, height=10)
        self.operation_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 操作列表滚动条
        scrollbar = ttk.Scrollbar(sequence_frame, orient=tk.VERTICAL, command=self.operation_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.operation_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 操作控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame, text="上移", command=self.move_up).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="下移", command=self.move_down).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="删除", command=self.delete_operation).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="清空", command=self.clear_operations).grid(row=0, column=3, padx=5)
        
        # 执行控制按钮
        execute_frame = ttk.Frame(main_frame)
        execute_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.start_button = ttk.Button(execute_frame, text="开始执行", command=self.start_execution)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(execute_frame, text="停止执行", command=self.stop_execution, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # 保存/加载按钮
        ttk.Button(execute_frame, text="保存配置", command=self.save_config).grid(row=0, column=2, padx=5)
        ttk.Button(execute_frame, text="加载配置", command=self.load_config).grid(row=0, column=3, padx=5)
        
        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
    def add_image_click_node(self):
        """添加图片匹配点击节点"""
        dialog = ImageClickDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_delay_node(self):
        """添加时间延迟节点"""
        dialog = DelayDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_drag_node(self):
        """添加鼠标拖动节点"""
        dialog = DragDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_operation(self, operation):
        """添加操作到序列"""
        self.operations.append(operation)
        self.update_operation_list()
        
    def update_operation_list(self):
        """更新操作列表显示"""
        self.operation_listbox.delete(0, tk.END)
        for i, op in enumerate(self.operations):
            if op['type'] == 'image_click':
                self.operation_listbox.insert(tk.END, f"{i+1}. 图片点击: {op['name']} - {op['image_path']}")
            elif op['type'] == 'delay':
                self.operation_listbox.insert(tk.END, f"{i+1}. 延迟: {op['duration']}秒")
            elif op['type'] == 'drag_click':
                self.operation_listbox.insert(tk.END, f"{i+1}. 拖动匹配: {op['name']} - {op['image_path']}")
            elif op['type'] == 'drag':
                direction_text = {'left': '左', 'right': '右', 'up': '上', 'down': '下'}
                self.operation_listbox.insert(tk.END, f"{i+1}. 拖动: {op['name']} - {direction_text[op['direction']]} {op['distance']}px {op['duration']}秒")
    
    def move_up(self):
        """上移选中操作"""
        selected = self.operation_listbox.curselection()
        if selected and selected[0] > 0:
            index = selected[0]
            self.operations[index], self.operations[index-1] = self.operations[index-1], self.operations[index]
            self.update_operation_list()
            self.operation_listbox.selection_set(index-1)
    
    def move_down(self):
        """下移选中操作"""
        selected = self.operation_listbox.curselection()
        if selected and selected[0] < len(self.operations) - 1:
            index = selected[0]
            self.operations[index], self.operations[index+1] = self.operations[index+1], self.operations[index]
            self.update_operation_list()
            self.operation_listbox.selection_set(index+1)
    
    def delete_operation(self):
        """删除选中操作"""
        selected = self.operation_listbox.curselection()
        if selected:
            index = selected[0]
            del self.operations[index]
            self.update_operation_list()
    
    def clear_operations(self):
        """清空所有操作"""
        if messagebox.askyesno("确认", "确定要清空所有操作吗？"):
            self.operations.clear()
            self.update_operation_list()
    
    def start_execution(self):
        """开始执行操作序列"""
        if not self.operations:
            messagebox.showwarning("警告", "请先添加操作序列")
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 在新线程中执行
        thread = threading.Thread(target=self.execute_operations)
        thread.daemon = True
        thread.start()
    
    def stop_execution(self):
        """停止执行"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("已停止")
    
    def execute_operations(self):
        """执行操作序列"""
        for i, operation in enumerate(self.operations):
            if not self.is_running:
                break
                
            self.status_var.set(f"执行第 {i+1}/{len(self.operations)} 个操作")
            
            if operation['type'] == 'image_click':
                self.execute_image_click(operation)
            elif operation['type'] == 'delay':
                self.execute_delay(operation)
            elif operation['type'] == 'drag_click':
                self.execute_drag_click(operation)
            elif operation['type'] == 'drag':
                self.execute_drag(operation)
        
        if self.is_running:
            self.status_var.set("执行完成")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_running = False
    
    def execute_image_click(self, operation):
        """执行图片匹配点击"""
        image_path = operation['image_path']
        threshold = operation.get('threshold', 0.1)
        max_attempts = operation.get('max_attempts', 1)
        
        for attempt in range(max_attempts):
            if not self.is_running:
                return
                
            avg = self.get_xy(image_path, threshold)
            if avg:
                self.auto_click(avg)
                self.status_var.set(f"已点击: {operation['name']}")
                return
            else:
                self.status_var.set(f"未找到: {operation['name']} (尝试 {attempt+1}/{max_attempts})")
                time.sleep(1)
        
        self.status_var.set(f"失败: 无法找到 {operation['name']}")
    
    def execute_delay(self, operation):
        """执行时间延迟"""
        duration = operation['duration']
        for i in range(duration):
            if not self.is_running:
                return
            self.status_var.set(f"延迟中... {duration - i}秒")
            time.sleep(1)
    
    def execute_drag_click(self, operation):
        """执行鼠标拖动匹配点击"""
        image_path = operation['image_path']
        threshold = operation.get('threshold', 0.1)
        max_swipes = operation.get('max_swipes', 5)
        swipe_distance = operation.get('swipe_distance', 400)
        
        for swipe in range(max_swipes):
            if not self.is_running:
                return
                
            avg = self.get_xy(image_path, threshold)
            if avg:
                self.auto_click(avg)
                self.status_var.set(f"已找到并点击: {operation['name']}")
                return
            else:
                self.status_var.set(f"未找到 {operation['name']}，执行第 {swipe+1} 次滑动...")
                # 执行拖动
                screen_width, screen_height = pyautogui.size()
                drag_start_x = screen_width / 2
                drag_start_y = screen_height / 2
                pyautogui.moveTo(drag_start_x, drag_start_y)
                pyautogui.dragRel(-swipe_distance, 0, duration=0.5)
                time.sleep(1)
        
        self.status_var.set(f"失败: 滑动 {max_swipes} 次后仍然未找到 {operation['name']}")
    
    def execute_drag(self, operation):
        """执行鼠标拖动"""
        direction = operation['direction']
        distance = operation['distance']
        drag_duration = operation['duration']
        
        self.status_var.set(f"执行拖动: {operation['name']}")
        
        # 获取屏幕中心点作为拖动起点
        screen_width, screen_height = pyautogui.size()
        drag_start_x = screen_width / 2
        drag_start_y = screen_height / 2
        
        # 根据方向计算拖动距离
        if direction == 'left':
            drag_x = -distance
            drag_y = 0
        elif direction == 'right':
            drag_x = distance
            drag_y = 0
        elif direction == 'up':
            drag_x = 0
            drag_y = -distance
        elif direction == 'down':
            drag_x = 0
            drag_y = distance
        else:
            self.status_var.set(f"错误: 未知拖动方向 {direction}")
            return
        
        # 执行拖动
        pyautogui.moveTo(drag_start_x, drag_start_y)
        pyautogui.dragRel(drag_x, drag_y, duration=drag_duration)
        
        self.status_var.set(f"完成拖动: {operation['name']}")
        time.sleep(1)  # 拖动后等待1秒
    
    def get_xy(self, img_model_path, threshold=0.1):
        """获取图片匹配坐标"""
        try:
            # 截图
            pyautogui.screenshot().save("./code/pic/screenshot.png")
            img = cv2.imread("./code/pic/screenshot.png")
            img_terminal = cv2.imread(img_model_path)
            
            if img_terminal is None:
                print(f"错误: 模板图片未找到于 {img_model_path}")
                return None
            
            height, width, channel = img_terminal.shape
            result = cv2.matchTemplate(img, img_terminal, cv2.TM_SQDIFF_NORMED)
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)

            if min_val < threshold:
                upper_left = min_loc
                lower_right = (upper_left[0] + width, upper_left[1] + height)
                avg = (int((upper_left[0] + lower_right[0]) / 2), int((upper_left[1] + lower_right[1]) / 2))
                return avg
            else:
                return None
        except Exception as e:
            print(f"图片匹配错误: {e}")
            return None
    
    def auto_click(self, var_avg):
        """自动点击"""
        pyautogui.click(var_avg[0], var_avg[1], button='left')
        time.sleep(1)
    
    def save_config(self):
        """保存配置到文件"""
        if not self.operations:
            messagebox.showwarning("警告", "没有操作可以保存")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.operations, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", "配置已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
    
    def load_config(self):
        """从文件加载配置"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.operations = json.load(f)
                self.update_operation_list()
                messagebox.showinfo("成功", "配置已加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {e}")


class ImageClickDialog:
    """图片匹配点击对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加图片匹配点击")
        self.top.geometry("400x300")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.image_path = tk.StringVar()
        self.name = tk.StringVar(value="未命名操作")
        self.threshold = tk.DoubleVar(value=0.1)
        self.max_attempts = tk.IntVar(value=1)
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self.top, text="操作名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="图片路径:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.image_path).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(self.top, text="浏览", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(self.top, text="匹配阈值:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Scale(self.top, from_=0.01, to=0.5, variable=self.threshold, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Label(self.top, textvariable=self.threshold).grid(row=2, column=2, padx=5, pady=5)
        
        ttk.Label(self.top, text="最大尝试次数:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=1, to=100, textvariable=self.max_attempts).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def browse_image(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if filename:
            self.image_path.set(filename)
    
    def ok(self):
        if not self.image_path.get():
            messagebox.showwarning("警告", "请选择图片")
            return
        
        operation = {
            'type': 'image_click',
            'name': self.name.get(),
            'image_path': self.image_path.get(),
            'threshold': self.threshold.get(),
            'max_attempts': self.max_attempts.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


class DelayDialog:
    """时间延迟对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加时间延迟")
        self.top.geometry("300x200")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.duration = tk.IntVar(value=1)
        self.name = tk.StringVar(value="延迟操作")
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self.top, text="操作名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="延迟时间(秒):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=1, to=3600, textvariable=self.duration).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def ok(self):
        operation = {
            'type': 'delay',
            'name': self.name.get(),
            'duration': self.duration.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


class DragClickDialog:
    """鼠标拖动匹配点击对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加鼠标拖动匹配点击")
        self.top.geometry("400x350")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.image_path = tk.StringVar()
        self.name = tk.StringVar(value="未命名拖动操作")
        self.threshold = tk.DoubleVar(value=0.1)
        self.max_swipes = tk.IntVar(value=5)
        self.swipe_distance = tk.IntVar(value=400)
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self.top, text="操作名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="图片路径:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.image_path).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(self.top, text="浏览", command=self.browse_image).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Label(self.top, text="匹配阈值:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Scale(self.top, from_=0.01, to=0.5, variable=self.threshold, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Label(self.top, textvariable=self.threshold).grid(row=2, column=2, padx=5, pady=5)
        
        ttk.Label(self.top, text="最大滑动次数:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=1, to=50, textvariable=self.max_swipes).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="滑动距离(像素):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=100, to=1000, textvariable=self.swipe_distance).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def browse_image(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
        )
        if filename:
            self.image_path.set(filename)
    
    def ok(self):
        if not self.image_path.get():
            messagebox.showwarning("警告", "请选择图片")
            return
        
        operation = {
            'type': 'drag_click',
            'name': self.name.get(),
            'image_path': self.image_path.get(),
            'threshold': self.threshold.get(),
            'max_swipes': self.max_swipes.get(),
            'swipe_distance': self.swipe_distance.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


class DragDialog:
    """鼠标拖动对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加鼠标拖动")
        self.top.geometry("400x300")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.name = tk.StringVar(value="拖动操作")
        self.direction = tk.StringVar(value="left")
        self.distance = tk.IntVar(value=400)
        self.duration = tk.DoubleVar(value=0.5)
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self.top, text="操作名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="拖动方向:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        direction_frame = ttk.Frame(self.top)
        direction_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Radiobutton(direction_frame, text="向左", variable=self.direction, value="left").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(direction_frame, text="向右", variable=self.direction, value="right").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(direction_frame, text="向上", variable=self.direction, value="up").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(direction_frame, text="向下", variable=self.direction, value="down").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.top, text="拖动距离(像素):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=10, to=2000, textvariable=self.distance).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="拖动用时(秒):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        #ttk.Scale(self.top, from_=0.1, to=5.0, variable=self.duration, orient=tk.HORIZONTAL).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        #ttk.Label(self.top, textvariable=self.duration).grid(row=3, column=2, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=10, to=2000, textvariable=self.duration).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)


        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def ok(self):
        operation = {
            'type': 'drag',
            'name': self.name.get(),
            'direction': self.direction.get(),
            'distance': self.distance.get(),
            'duration': self.duration.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = AutoClickGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
