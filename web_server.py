#!/usr/bin/env python3
"""
Web服务器 - 为数据面板提供API服务
支持数据刷新和实时更新功能
"""

import os
import json
import subprocess
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from datetime import datetime
import threading
import time
from config_loader import get_config

app = Flask(__name__)
CORS(app)  # 允许跨域请求

class DataManager:
    """数据管理器"""
    
    def __init__(self):
        self.last_refresh = None
        self.is_refreshing = False
        self.data_file = "web_data.json"
        self.analysis_script = "data_analyzer.py"
    
    def get_current_data(self):
        """获取当前数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "brands_count": 0,
                    "projects_count": 0,
                    "total_files": 0,
                    "last_updated": "数据未初始化"
                }
        except Exception as e:
            print(f"读取数据文件失败: {e}")
            return {
                "brands_count": 0,
                "projects_count": 0,
                "total_files": 0,
                "last_updated": "数据读取失败"
            }
    
    def refresh_data(self):
        """刷新数据（在后台线程中运行）"""
        if self.is_refreshing:
            return False
        
        self.is_refreshing = True
        try:
            print("开始刷新数据...")
            # 运行数据分析脚本
            result = subprocess.run(['python', self.analysis_script], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("数据刷新成功")
                self.last_refresh = datetime.now()
                return True
            else:
                print(f"数据分析脚本执行失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("数据刷新超时")
            return False
        except Exception as e:
            print(f"数据刷新异常: {e}")
            return False
        finally:
            self.is_refreshing = False

class ChatManager:
    """聊天管理器"""
    
    def __init__(self):
        self.assistant = None
        self.initialize_assistant()
    
    def initialize_assistant(self):
        """初始化智能助手"""
        try:
            from project_assistant import ProjectAssistant
            self.assistant = ProjectAssistant()
            print("智能助手初始化成功")
        except Exception as e:
            print(f"智能助手初始化失败: {e}")
            self.assistant = None
    
    def chat(self, message):
        """处理聊天消息"""
        if not self.assistant:
            return {
                "success": False,
                "response": "智能助手未初始化，请检查Gemini API配置。"
            }
        
        try:
            response = self.assistant.ask(message)
            return {
                "success": True,
                "response": response
            }
        except Exception as e:
            print(f"聊天处理错误: {e}")
            return {
                "success": False,
                "response": f"处理您的问题时出现错误: {str(e)}"
            }

# 创建管理器实例
data_manager = DataManager()
chat_manager = ChatManager()

@app.route('/')
def index():
    """主页 - 返回数据面板"""
    return send_from_directory('.', 'simple_dashboard.html')

@app.route('/web_data.json')
def get_data():
    """API接口 - 获取数据"""
    return jsonify(data_manager.get_current_data())

@app.route('/api/status')
def get_status():
    """API接口 - 获取系统状态"""
    return jsonify({
        "is_refreshing": data_manager.is_refreshing,
        "last_refresh": data_manager.last_refresh.isoformat() if data_manager.last_refresh else None,
        "data_file_exists": os.path.exists(data_manager.data_file),
        "chat_available": chat_manager.assistant is not None,
        "server_time": datetime.now().isoformat()
    })

@app.route('/refresh', methods=['POST'])
def refresh_data():
    """API接口 - 刷新数据"""
    def background_refresh():
        data_manager.refresh_data()
    
    if data_manager.is_refreshing:
        return jsonify({
            "status": "already_refreshing",
            "message": "数据刷新正在进行中"
        }), 202
    
    # 在后台线程中执行刷新
    refresh_thread = threading.Thread(target=background_refresh)
    refresh_thread.daemon = True
    refresh_thread.start()
    
    return jsonify({
        "status": "refresh_started",
        "message": "数据刷新已开始"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """API接口 - 聊天对话"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "response": "请提供有效的消息内容"
            }), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({
                "success": False,
                "response": "消息内容不能为空"
            }), 400
        
        # 处理聊天消息
        result = chat_manager.chat(message)
        return jsonify(result)
        
    except Exception as e:
        print(f"聊天API错误: {e}")
        return jsonify({
            "success": False,
            "response": "服务器处理请求时出现错误"
        }), 500

@app.route('/api/data/detailed')
def get_detailed_data():
    """API接口 - 获取详细数据"""
    try:
        if os.path.exists("data_analysis_result.json"):
            with open("data_analysis_result.json", 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({"error": "详细数据文件不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "API接口不存在"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

def main():
    """主函数"""
    print("=" * 60)
    print("数英网项目数据面板 Web 服务器")
    print("=" * 60)
    
    # 检查必要文件
    if not os.path.exists(data_manager.analysis_script):
        print(f"警告: 数据分析脚本 {data_manager.analysis_script} 不存在")
    
    if not os.path.exists("data"):
        print("警告: data 文件夹不存在")
    
    # 如果数据文件不存在，先运行一次数据分析
    if not os.path.exists(data_manager.data_file):
        print("数据文件不存在，正在初始化数据...")
        data_manager.refresh_data()
    
    print(f"\n服务器启动信息:")
    print(f"  - 访问地址: http://localhost:5000")
    print(f"  - 数据面板: http://localhost:5000")
    print(f"  - API状态: http://localhost:5000/api/status")
    print(f"  - 聊天API: http://localhost:5000/api/chat")
    print(f"  - 当前数据: {data_manager.get_current_data()}")
    print(f"  - 聊天状态: {'可用' if chat_manager.assistant else '不可用'}")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    # 获取配置
    config = get_config()
    server_host = config.get('SERVER_HOST', '0.0.0.0')
    server_port = config.get_int('SERVER_PORT', 5000)
    debug_mode = config.get_bool('DEBUG_MODE', False)
    
    # 启动Flask服务器
    app.run(
        host=server_host,  # 允许外部访问
        port=server_port,
        debug=debug_mode,  # 根据配置决定调试模式
        use_reloader=False  # 避免重启问题
    )

if __name__ == "__main__":
    main()