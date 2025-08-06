#!/usr/bin/env python3
"""
配置管理器 - 提供图形化配置界面
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config_loader import get_config

class ConfigManager:
    """配置管理器GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("数英网系统配置管理器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.config = get_config()
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="数英网数据统计与智能对话系统", 
                               font=("Microsoft YaHei", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 创建配置项
        self.create_config_sections(main_frame)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=10, column=0, columnspan=2, pady=20)
        
        # 按钮
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重置配置", command=self.reset_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="启动系统", command=self.start_system).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
    def create_config_sections(self, parent):
        """创建配置区域"""
        # Gemini API配置
        self.create_section(parent, "Gemini API配置", 1, [
            ("GEMINI_API_KEY", "API密钥", "your_gemini_api_key_here")
        ])
        
        # 服务器配置
        self.create_section(parent, "服务器配置", 3, [
            ("SERVER_HOST", "服务器地址", "0.0.0.0"),
            ("SERVER_PORT", "端口号", "5000"),
            ("DEBUG_MODE", "调试模式", "false")
        ])
        
        # 数据配置
        self.create_section(parent, "数据配置", 6, [
            ("DATA_FOLDER", "数据文件夹", "data"),
            ("OUTPUT_FOLDER", "输出文件夹", "output"),
            ("WEB_DATA_FILE", "Web数据文件", "web_data.json")
        ])
        
        # 浏览器配置
        self.create_section(parent, "浏览器配置", 9, [
            ("AUTO_OPEN_BROWSER", "自动打开浏览器", "true"),
            ("BROWSER_URL", "浏览器地址", "http://localhost:5000")
        ])
        
    def create_section(self, parent, title, start_row, items):
        """创建配置区域"""
        # 区域标题
        section_label = ttk.Label(parent, text=title, font=("Microsoft YaHei", 12, "bold"))
        section_label.grid(row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # 配置项
        for i, (key, label, default) in enumerate(items):
            row = start_row + 1 + i
            
            # 标签
            ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10))
            
            # 输入框
            value = self.config.get(key, default)
            if key == "GEMINI_API_KEY" and value == "your_gemini_api_key_here":
                value = ""
            
            entry = ttk.Entry(parent, width=40)
            entry.insert(0, value)
            entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
            
            # 特殊处理
            if key == "GEMINI_API_KEY":
                ttk.Button(parent, text="获取密钥", 
                          command=lambda: self.open_gemini_help()).grid(row=row, column=2)
            elif key == "DATA_FOLDER":
                ttk.Button(parent, text="浏览", 
                          command=lambda: self.browse_folder(entry)).grid(row=row, column=2)
            elif key == "OUTPUT_FOLDER":
                ttk.Button(parent, text="浏览", 
                          command=lambda: self.browse_folder(entry)).grid(row=row, column=2)
            
            # 保存引用
            setattr(self, f"entry_{key}", entry)
    
    def open_gemini_help(self):
        """打开Gemini API帮助"""
        help_text = """
获取Gemini API密钥的步骤：

1. 访问 Google AI Studio: https://ai.google.dev/
2. 登录您的Google账户
3. 点击"Get API key"
4. 创建新的API密钥
5. 复制密钥并粘贴到配置中

注意：请妥善保管您的API密钥，不要泄露给他人。
        """
        messagebox.showinfo("Gemini API密钥获取帮助", help_text)
    
    def browse_folder(self, entry):
        """浏览文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            entry.delete(0, tk.END)
            entry.insert(0, folder)
    
    def save_config(self):
        """保存配置"""
        try:
            # 收集所有配置值
            for key in self.config.get_all().keys():
                entry_name = f"entry_{key}"
                if hasattr(self, entry_name):
                    entry = getattr(self, entry_name)
                    value = entry.get().strip()
                    
                    # 特殊处理
                    if key == "GEMINI_API_KEY" and not value:
                        value = "your_gemini_api_key_here"
                    
                    self.config.set(key, value)
            
            # 保存到文件
            self.config.save_config()
            messagebox.showinfo("成功", "配置已保存！")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：{str(e)}")
    
    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "确定要重置所有配置吗？"):
            try:
                # 删除配置文件
                if os.path.exists("config.env"):
                    os.remove("config.env")
                
                # 重新加载配置
                self.config = get_config()
                messagebox.showinfo("成功", "配置已重置！")
                
                # 重新加载界面
                self.root.destroy()
                self.__init__()
                self.setup_ui()
                
            except Exception as e:
                messagebox.showerror("错误", f"重置配置失败：{str(e)}")
    
    def start_system(self):
        """启动系统"""
        if messagebox.askyesno("确认", "确定要启动系统吗？"):
            self.root.destroy()
            
            # 启动系统
            try:
                import subprocess
                subprocess.run([sys.executable, "start_dashboard.py"])
            except Exception as e:
                messagebox.showerror("错误", f"启动系统失败：{str(e)}")
    
    def run(self):
        """运行配置管理器"""
        self.root.mainloop()

def main():
    """主函数"""
    app = ConfigManager()
    app.run()

if __name__ == "__main__":
    main() 