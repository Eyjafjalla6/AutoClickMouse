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
        
        # 全局存储节点返回值
        self.node_results = {}
        
        # 循环和条件判断状态
        self.loop_stack = []  # 存储循环信息
        self.condition_stack = []  # 存储条件判断状态
        self.break_flag = False  # 循环中断标志
        
        # 创建界面
        self.create_widgets()
        
        # 基础目录
        self.base_dir = "./code"
        
    def safe_move_to(self, x, y, duration=0.5):
        """
        安全的鼠标移动函数，避免触发fail-safe
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except pyautogui.FailSafeException:
            print("检测到fail-safe触发，正在重新定位鼠标...")
            # 将鼠标移动到屏幕中心
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            pyautogui.moveTo(center_x, center_y, duration=0.5)
            return False

    def safe_drag_rel(self, x_offset, y_offset, duration=0.5):
        """
        安全的鼠标拖动函数，避免触发fail-safe
        """
        try:
            pyautogui.dragRel(x_offset, y_offset, duration=duration)
            return True
        except pyautogui.FailSafeException:
            print("检测到fail-safe触发，正在重新定位鼠标...")
            # 将鼠标移动到屏幕中心
            screen_width, screen_height = pyautogui.size()
            center_x = screen_width // 2
            center_y = screen_height // 2
            pyautogui.moveTo(center_x, center_y, duration=0.5)
            return False

    def get_safe_screen_center(self):
        """
        获取安全的屏幕中心坐标，避免太靠近边缘
        """
        screen_width, screen_height = pyautogui.size()
        # 在屏幕中心创建一个安全区域，避免太靠近边缘
        margin = 100  # 安全边距
        center_x = max(margin, min(screen_width - margin, screen_width // 2))
        center_y = max(margin, min(screen_height - margin, screen_height // 2))
        return center_x, center_y
        
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
        ttk.Button(operation_frame, text="点击", 
                  command=self.add_click_node).grid(row=0, column=3, padx=5)
        ttk.Button(operation_frame, text="条件判断(IF)", 
                  command=self.add_if_node).grid(row=1, column=0, padx=5)
        ttk.Button(operation_frame, text="条件结束(ELSE)", 
                  command=self.add_else_node).grid(row=1, column=1, padx=5)
        ttk.Button(operation_frame, text="循环开始", 
                  command=self.add_loop_start_node).grid(row=1, column=2, padx=5)
        ttk.Button(operation_frame, text="循环结束", 
                  command=self.add_loop_end_node).grid(row=1, column=3, padx=5)
        ttk.Button(operation_frame, text="循环中断(BREAK)", 
                  command=self.add_break_node).grid(row=2, column=0, padx=5)
        
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
        
        
    def add_click_node(self):
        """添加点击节点"""
        dialog = ClickDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_drag_node(self):
        """添加鼠标拖动节点"""
        dialog = DragDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_if_node(self):
        """添加条件判断节点"""
        dialog = IfDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_else_node(self):
        """添加条件结束节点"""
        operation = {
            'type': 'else',
            'name': '条件结束'
        }
        self.add_operation(operation)
        
    def add_loop_start_node(self):
        """添加循环开始节点"""
        dialog = LoopStartDialog(self.root, self)
        self.root.wait_window(dialog.top)
        
    def add_loop_end_node(self):
        """添加循环结束节点"""
        operation = {
            'type': 'loop_end',
            'name': '循环结束'
        }
        self.add_operation(operation)
        
    def add_break_node(self):
        """添加循环中断节点"""
        operation = {
            'type': 'break',
            'name': '循环中断'
        }
        self.add_operation(operation)
        
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
                start_position_text = {
                    'screen_center': '屏幕中心',
                    'current_mouse': '当前位置',
                    'custom': f"自定义({op.get('custom_x', 0)},{op.get('custom_y', 0)})"
                }
                position_info = start_position_text.get(op.get('start_position', 'screen_center'), '屏幕中心')
                self.operation_listbox.insert(tk.END, f"{i+1}. 拖动: {op['name']} - {direction_text[op['direction']]} {op['distance']}px {op['duration']}秒 ({position_info})")
            elif op['type'] == 'click':
                button_text = {'left': '左键', 'right': '右键'}
                self.operation_listbox.insert(tk.END, f"{i+1}. 点击: {op['name']} - ({op['x']}, {op['y']}) {button_text[op['button']]}")
            elif op['type'] == 'if':
                condition_type = op.get('condition_type', '==')
                condition_value = op.get('condition_value', 'True')
                condition_text = f"判断 {op['target_node']} {condition_type} {condition_value}"
                self.operation_listbox.insert(tk.END, f"{i+1}. 条件判断: {op['name']} - {condition_text}")
            elif op['type'] == 'break':
                self.operation_listbox.insert(tk.END, f"{i+1}. 循环中断: {op['name']}")
            elif op['type'] == 'else':
                self.operation_listbox.insert(tk.END, f"{i+1}. 条件结束: {op['name']}")
            elif op['type'] == 'loop_start':
                self.operation_listbox.insert(tk.END, f"{i+1}. 循环开始: {op['name']} - 循环 {op['iterations']} 次")
            elif op['type'] == 'loop_end':
                self.operation_listbox.insert(tk.END, f"{i+1}. 循环结束: {op['name']}")
    
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
        i = 0
        while i < len(self.operations) and self.is_running:
            operation = self.operations[i]
            self.status_var.set(f"执行第 {i+1}/{len(self.operations)} 个操作")
            
            # 处理条件判断
            if self.condition_stack and not self.condition_stack[-1]:
                # 当前处于条件判断的false分支，跳过执行直到遇到else
                if operation['type'] == 'else':
                    self.condition_stack[-1] = True  # 切换到else分支
                elif operation['type'] == 'loop_end':
                    # 跳过循环结束标记
                    pass
                else:
                    i += 1
                    continue
            
            # 处理循环
            if self.loop_stack:
                loop_info = self.loop_stack[-1]
                
                # 检查是否遇到break节点
                if operation['type'] == 'break':
                    self.status_var.set(f"循环中断: {operation['name']} - 提前结束循环")
                    # 弹出当前循环信息，结束循环
                    self.loop_stack.pop()
                    # 找到对应的循环结束节点并跳转到该节点之后
                    i = self.find_loop_end_index(i)
                    continue
                
                if operation['type'] == 'loop_end':
                    loop_info['current_iteration'] += 1
                    if loop_info['current_iteration'] < loop_info['iterations']:
                        # 继续循环，跳回到循环开始
                        i = loop_info['start_index']
                    else:
                        # 循环结束，弹出循环信息
                        self.loop_stack.pop()
                    i += 1
                    continue
            
            # 执行具体操作
            if operation['type'] == 'image_click':
                self.execute_image_click(operation)
            elif operation['type'] == 'delay':
                self.execute_delay(operation)
            elif operation['type'] == 'drag_click':
                self.execute_drag_click(operation)
            elif operation['type'] == 'drag':
                self.execute_drag(operation)
            elif operation['type'] == 'click':
                self.execute_click(operation)
            elif operation['type'] == 'if':
                self.execute_if(operation)
            elif operation['type'] == 'else':
                # else节点只是标记，不需要执行具体操作
                pass
            elif operation['type'] == 'loop_start':
                self.execute_loop_start(operation, i)
            elif operation['type'] == 'loop_end':
                # loop_end节点只是标记，不需要执行具体操作
                pass
            
            i += 1
        
        if self.is_running:
            self.status_var.set("执行完成")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_running = False
            # 清理状态
            self.loop_stack.clear()
            self.condition_stack.clear()
    
    def execute_if(self, operation):
        """执行条件判断，支持复杂表达式"""
        target_node = operation['target_node']
        condition_type = operation.get('condition_type', '==')
        condition_value = operation.get('condition_value', '1')
        
        condition_result = False
        
        # 检查目标节点的返回值
        if target_node in self.node_results:
            #print(target_node)
            target_value = self.node_results[target_node]#target_value是节点返回值
            
            # 根据条件类型进行比较
            try:
                if condition_type == '==':
                    if  int(condition_value) == target_value:
                        condition_result = 1
                        #print(1)
                    else:
                        condition_result = 0
                        #print(0)
                elif  condition_type == '!=':
                    if  int(condition_value) != target_value:
                        condition_result = 1
                    else:
                        condition_result = 0
                elif condition_type == '>':
                    condition_result = (target_value > int(condition_value))
                elif condition_type == '<':
                    condition_result = (target_value < int(condition_value))
                elif condition_type == '>=':
                    condition_result = (target_value >= int(condition_value))
                elif condition_type == '<=':
                    condition_result = (target_value <= int(condition_value))
            except (ValueError, TypeError):
                # 如果转换失败，使用字符串比较
                condition_result = str(target_value) == condition_value
            except Exception as e:
                print(f"条件判断错误: {e}")
                condition_result = 0
        
        self.status_var.set(f"条件判断: {operation['name']} - {target_node} {condition_type} {condition_value} = {condition_result}")
        
        # 将条件结果压入栈中
        self.condition_stack.append(condition_result)
    
    def find_loop_end_index(self, current_index):
        """
        从当前位置开始查找对应的循环结束节点
        :param current_index: 当前节点索引
        :return: 循环结束节点后的索引，如果没有找到则返回列表长度
        """
        loop_depth = 1  # 当前循环深度，从1开始
        i = current_index + 1
        
        while i < len(self.operations):
            operation = self.operations[i]
            
            if operation['type'] == 'loop_start':
                loop_depth += 1
            elif operation['type'] == 'loop_end':
                loop_depth -= 1
                if loop_depth == 0:
                    # 找到对应的循环结束节点，返回该节点后的索引
                    return i + 1
            
            i += 1
        
        # 如果没有找到对应的循环结束节点，返回列表长度（即结束执行）
        return len(self.operations)
    
    def execute_loop_start(self, operation, current_index):
        """执行循环开始"""
        iterations = operation['iterations']
        
        # 将循环信息压入栈中
        loop_info = {
            'start_index': current_index,
            'iterations': iterations,
            'current_iteration': 0
        }
        self.loop_stack.append(loop_info)
        
        self.status_var.set(f"循环开始: {operation['name']} - 第 1/{iterations} 次循环")
    

    def execute_image_click(self, operation):
        """执行图片匹配点击，返回1（成功）或0（失败）"""
        image_path = operation['image_path']
        threshold = operation.get('threshold', 0.1)
        max_attempts = operation.get('max_attempts', 1)
        
        for attempt in range(max_attempts):
            if not self.is_running:
                return 0
                
            avg = self.get_xy(image_path, threshold)
            if avg:
                self.auto_click(avg)
                self.status_var.set(f"已点击: {operation['name']}")
                # 存储节点返回值到全局变量
                self.node_results[operation['name']] = 1
                return 1
            else:
                self.status_var.set(f"未找到: {operation['name']} (尝试 {attempt+1}/{max_attempts})")
                time.sleep(1)
        
        self.status_var.set(f"失败: 无法找到 {operation['name']}")
        # 存储节点返回值到全局变量
        self.node_results[operation['name']] = 0
        return 0
    
    def execute_delay(self, operation):
        """执行时间延迟"""
        duration = operation['duration']
        for i in range(duration):
            if not self.is_running:
                return
            self.status_var.set(f"延迟中... {duration - i}秒")
            time.sleep(1)
    
    def auto_click(self, var_avg):
        """
        输入一个元组，自动点击
        :param var_avg: 坐标元组
        :return: None
        """
        pyautogui.click(var_avg[0], var_avg[1], button='left')
        time.sleep(1)

    def get_xy(self, img_model_path, threshold=0.1):
        """
        用来判定游戏画面的点击坐标
        :param img_model_path:用来检测的图片
        :param threshold: 匹配阈值
        :return:以元组形式返回检测到的区域中心的坐标, 未找到则返回None
        """
        # 将图片截图并且保存
        pyautogui.screenshot().save("./code/pic/screenshot.png")
        # 待读取图像
        img = cv2.imread("./code/pic/screenshot.png")
        # 图像模板
        img_terminal = cv2.imread(img_model_path)
        if img_terminal is None:
            print(f"错误: 模板图片未找到于 {img_model_path}")
            return None
        # 读取模板的高度宽度和通道数
        height, width, channel = img_terminal.shape
        # 使用matchTemplate进行模板匹配（标准平方差匹配）
        result = cv2.matchTemplate(img, img_terminal, cv2.TM_SQDIFF_NORMED)
        # 解析出匹配区域的左上角图标
        min_val, _, min_loc, _ = cv2.minMaxLoc(result)

        if min_val < threshold:
            upper_left = min_loc
            # 计算出匹配区域右下角图标（左上角坐标加上模板的长宽即可得到）
            lower_right = (upper_left[0] + width, upper_left[1] + height)
            # 计算坐标的平均值并将其返回
            avg = (int((upper_left[0] + lower_right[0]) / 2), int((upper_left[1] + lower_right[1]) / 2))
            return avg
        else:
            return None

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
                # 使用安全中心点进行拖动
                drag_start_x, drag_start_y = self.get_safe_screen_center()
                self.safe_move_to(drag_start_x, drag_start_y)
                # 使用安全拖动函数
                self.safe_drag_rel(-swipe_distance, 0, duration=0.5)
                time.sleep(1)
        
        self.status_var.set(f"失败: 滑动 {max_swipes} 次后仍然未找到 {operation['name']}")
    
    def execute_drag(self, operation):
        """执行鼠标拖动"""
        direction = operation['direction']
        distance = operation['distance']
        drag_duration = operation['duration']
        start_position = operation.get('start_position', 'screen_center')
        
        self.status_var.set(f"执行拖动: {operation['name']}")
        
        # 根据起始位置类型确定拖动起点
        if start_position == 'screen_center':
            # 屏幕中心
            screen_width, screen_height = pyautogui.size()
            drag_start_x = screen_width / 2
            drag_start_y = screen_height / 2
            position_info = "屏幕中心"
        elif start_position == 'current_mouse':
            # 当前鼠标位置
            drag_start_x, drag_start_y = pyautogui.position()
            position_info = f"当前位置({drag_start_x}, {drag_start_y})"
        elif start_position == 'custom':
            # 自定义位置
            drag_start_x = operation.get('custom_x', 0)
            drag_start_y = operation.get('custom_y', 0)
            position_info = f"自定义位置({drag_start_x}, {drag_start_y})"
        else:
            self.status_var.set(f"错误: 未知起始位置类型 {start_position}")
            return
        
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
        
        self.status_var.set(f"完成拖动: {operation['name']} - {position_info}")
        time.sleep(1)  # 拖动后等待1秒
    
    
    def execute_click(self, operation):
        """执行点击操作"""
        x = operation['x']
        y = operation['y']
        button = operation['button']
        
        self.status_var.set(f"点击: {operation['name']} - ({x}, {y}) {button}键")
        pyautogui.click(x, y, button=button)
        
        time.sleep(1)  # 点击后等待1秒
    
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
        #ttk.Scale(self.top, from_=0.01, to=0.5, variable=self.threshold, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        #ttk.Label(self.top, textvariable=self.threshold).grid(row=2, column=2, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=0.01, to=0.5, textvariable=self.threshold).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

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
        self.top.geometry("500x350")
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
        #ttk.Scale(self.top, from_=0.01, to=0.5, variable=self.threshold, orient=tk.HORIZONTAL).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        #ttk.Label(self.top, textvariable=self.threshold).grid(row=2, column=2, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=1, to=50, textvariable=self.threshold).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

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
        self.top.geometry("500x400")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.name = tk.StringVar(value="拖动操作")
        self.direction = tk.StringVar(value="left")
        self.distance = tk.IntVar(value=400)
        self.duration = tk.DoubleVar(value=0.5)
        self.start_position = tk.StringVar(value="screen_center")
        self.custom_x = tk.IntVar(value=0)
        self.custom_y = tk.IntVar(value=0)
        
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
        ttk.Spinbox(self.top, from_=0.1, to=5.0, increment=0.1, textvariable=self.duration).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="起始位置:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        position_frame = ttk.Frame(self.top)
        position_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Radiobutton(position_frame, text="屏幕中心", variable=self.start_position, 
                       value="screen_center", command=self.toggle_custom_position).pack(anchor=tk.W)
        ttk.Radiobutton(position_frame, text="当前鼠标位置", variable=self.start_position, 
                       value="current_mouse", command=self.toggle_custom_position).pack(anchor=tk.W)
        ttk.Radiobutton(position_frame, text="自定义位置", variable=self.start_position, 
                       value="custom", command=self.toggle_custom_position).pack(anchor=tk.W)
        
        # 自定义位置输入框
        custom_frame = ttk.Frame(self.top)
        custom_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(custom_frame, text="X:").grid(row=0, column=0, padx=5)
        self.x_entry = ttk.Entry(custom_frame, textvariable=self.custom_x, width=8)
        self.x_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(custom_frame, text="Y:").grid(row=0, column=2, padx=5)
        self.y_entry = ttk.Entry(custom_frame, textvariable=self.custom_y, width=8)
        self.y_entry.grid(row=0, column=3, padx=5)
        
        ttk.Button(custom_frame, text="获取当前位置", command=self.get_current_position).grid(row=0, column=4, padx=5)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
        self.toggle_custom_position()
    
    def toggle_custom_position(self):
        """切换自定义位置输入状态"""
        if self.start_position.get() == "custom":
            self.x_entry.config(state=tk.NORMAL)
            self.y_entry.config(state=tk.NORMAL)
        else:
            self.x_entry.config(state=tk.DISABLED)
            self.y_entry.config(state=tk.DISABLED)
    
    def get_current_position(self):
        """获取当前鼠标位置"""
        x, y = pyautogui.position()
        self.custom_x.set(x)
        self.custom_y.set(y)
        messagebox.showinfo("成功", f"已获取鼠标位置: ({x}, {y})")
    
    def ok(self):
        operation = {
            'type': 'drag',
            'name': self.name.get(),
            'direction': self.direction.get(),
            'distance': self.distance.get(),
            'duration': self.duration.get(),
            'start_position': self.start_position.get(),
            'custom_x': self.custom_x.get(),
            'custom_y': self.custom_y.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


class ClickDialog:
    """点击对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加点击操作")
        self.top.geometry("400x250")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.name = tk.StringVar(value="点击操作")
        self.position_x = tk.IntVar(value=0)
        self.position_y = tk.IntVar(value=0)
        self.button = tk.StringVar(value="left")
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Button(self.top, text="获取当前鼠标位置", command=self.get_current_position).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(self.top, text="操作名称:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="X坐标:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.position_x).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="Y坐标:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.position_y).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        
        
        ttk.Label(self.top, text="点击按钮:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Radiobutton(button_frame, text="左键", variable=self.button, value="left").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(button_frame, text="右键", variable=self.button, value="right").pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def get_current_position(self):
        """获取当前鼠标位置"""
        x, y = pyautogui.position()
        self.position_x.set(x)
        self.position_y.set(y)
        messagebox.showinfo("成功", f"已获取鼠标位置: ({x}, {y})")
    
    def ok(self):
        operation = {
            'type': 'click',
            'name': self.name.get(),
            'x': self.position_x.get(),
            'y': self.position_y.get(),
            'button': self.button.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


class IfDialog:
    """条件判断对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加条件判断")
        self.top.geometry("520x350")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.name = tk.StringVar(value="条件判断")
        self.target_node = tk.StringVar()
        self.condition_type = tk.StringVar(value="==")
        self.condition_value = tk.StringVar(value="1")
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self.top, text="操作名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="目标节点名称:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.target_node).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="条件类型:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        condition_frame = ttk.Frame(self.top)
        condition_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.condition_type).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="比较值:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.condition_value).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # 示例说明
        example_frame = ttk.LabelFrame(self.top, text="示例说明", padding="5")
        example_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        examples = [
            "== True  - 判断节点返回值是否为真",
            "!= 0     - 判断节点返回值是否不等于0",
            "> 1      - 判断节点返回值是否大于1",
            "其他支持的语法: <5 <=5 >=5 "
        ]
        for i, example in enumerate(examples):
            ttk.Label(example_frame, text=example).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def ok(self):
        if not self.target_node.get():
            messagebox.showwarning("警告", "请输入目标节点名称")
            return
        
        operation = {
            'type': 'if',
            'name': self.name.get(),
            'target_node': self.target_node.get(),
            'condition_type': self.condition_type.get(),
            'condition_value': self.condition_value.get()
        }
        self.gui.add_operation(operation)
        self.top.destroy()
    
    def cancel(self):
        self.top.destroy()


class LoopStartDialog:
    """循环开始对话框"""
    def __init__(self, parent, gui):
        self.gui = gui
        self.top = tk.Toplevel(parent)
        self.top.title("添加循环开始")
        self.top.geometry("400x200")
        self.top.transient(parent)
        self.top.grab_set()
        
        self.name = tk.StringVar(value="循环开始")
        self.iterations = tk.IntVar(value=1)
        
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self.top, text="操作名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.top, textvariable=self.name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(self.top, text="循环次数:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Spinbox(self.top, from_=1, to=1000, textvariable=self.iterations).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.top.columnconfigure(1, weight=1)
    
    def ok(self):
        operation = {
            'type': 'loop_start',
            'name': self.name.get(),
            'iterations': self.iterations.get()
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
