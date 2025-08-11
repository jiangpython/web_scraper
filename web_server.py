#!/usr/bin/env python3
"""
Web服务器 - 为数据面板提供API服务
支持数据刷新和实时更新功能
"""
print(">>> web_server.py 开始加载 <<<")
import os
import json
import subprocess
from flask import Flask, jsonify, send_from_directory, request
print("Flask导入成功")
from flask_cors import CORS
from datetime import datetime
import threading
import time
from config_optimized import get_config

import logging
logging.basicConfig(level=logging.INFO)



# 强制刷新输出
import sys
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

# 禁用输出缓冲
os.environ['PYTHONUNBUFFERED'] = '1'


print("\n" + "="*60)
print("WEB服务器启动 - 版本：带调试信息 v2")
print("="*60 + "\n")

app = Flask(__name__)
print(f"Flask app创建成功: {app}")
CORS(app)  # 允许跨域请求

app.logger.setLevel(logging.DEBUG)

@app.route('/immediate-test')
def immediate_test():
    return "立即测试成功"

print(f"当前已有路由数: {len(list(app.url_map.iter_rules()))}")



@app.before_request
def log_request():
    app.logger.info(f"收到请求: {request.method} {request.path}")
    if request.method == 'POST':
        app.logger.info(f"请求数据: {request.get_json()}")

@app.after_request
def log_response(response):
    print(f"\n[AFTER_REQUEST] 响应状态: {response.status}")
    sys.stdout.flush()
    return response


@app.route('/')
def index():
    """主页 - 返回数据面板"""
    return send_from_directory('.', 'web_dashboard.html')


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


@app.route('/api/system/status')
def system_status():
    """API接口 - 获取系统状态"""
    try:
        # 检查索引文件状态
        index_file = "output/global_search_index.json"
        index_exists = os.path.exists(index_file)
        index_size = os.path.getsize(index_file) if index_exists else 0

        index_info = {}
        if index_exists:
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                index_info = index_data.get('metadata', {})
            except:
                index_info = {"error": "索引文件读取失败"}

        # 检查项目数据
        projects_file = "output/projects_index.json"
        projects_exists = os.path.exists(projects_file)
        projects_count = 0

        if projects_exists:
            try:
                with open(projects_file, 'r', encoding='utf-8') as f:
                    projects_data = json.load(f)
                projects_count = projects_data.get('total_projects', 0)
            except:
                projects_count = 0

        return jsonify({
            "system_status": "operational",
            "index_status": {
                "exists": index_exists,
                "size_kb": round(index_size / 1024, 2) if index_exists else 0,
                "metadata": index_info
            },
            "projects_status": {
                "exists": projects_exists,
                "count": projects_count
            },
            "chat_available": chat_manager.assistant is not None if chat_manager else False,
            "last_refresh": data_manager.last_refresh.isoformat() if data_manager.last_refresh else None,
            "server_time": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "system_status": "error",
            "error": str(e),
            "server_time": datetime.now().isoformat()
        }), 500


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


from concurrent.futures import ThreadPoolExecutor

# 创建一个全局的线程池
executor = ThreadPoolExecutor(max_workers=2)

class ChatManager:
    """聊天管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print("创建 ChatManager 单例...")
            cls._instance = super(ChatManager, cls).__new__(cls)
            cls._instance.assistant = None
            cls._instance.initialize_assistant()
        return cls._instance

    def initialize_assistant(self):
        """初始化智能助手"""
        try:
            from smart_ai_assistant import SmartAIAssistant
            print("ChatManager: 正在初始化 SmartAIAssistant...")
            # 注意：这里只做默认初始化，实际选择在chat接口中处理
            self.assistant = SmartAIAssistant() # 默认使用Gemini
            if self.assistant.ready:
                print("ChatManager: 默认(Gemini) SmartAIAssistant 初始化成功。")
            else:
                print("ChatManager: 默认(Gemini) SmartAIAssistant 初始化失败。")
        except Exception as e:
            print(f"ChatManager: 初始化失败 - {e}")
            self.assistant = None

    def get_assistant(self, model_provider: str = 'gemini'):
        """根据模型提供商获取或创建助手实例"""
        if model_provider == 'gemini':
            # 复用默认实例
            if self.assistant and self.assistant.model_provider == 'gemini':
                if not self.assistant.ready: # 尝试重新初始化
                    self.initialize_assistant()
                return self.assistant
            else: # 如果默认实例不是gemini，则新建
                from smart_ai_assistant import SmartAIAssistant
                return SmartAIAssistant(model_provider='gemini')

        elif model_provider == 'deepseek':
            # deepseek总是创建一个新的实例，因为它可能依赖不同的API KEY
            # (如果需要，这里可以添加缓存逻辑)
            from smart_ai_assistant import SmartAIAssistant
            print(f"为 deepseek 创建新的助手实例...")
            return SmartAIAssistant(model_provider='deepseek')
        
        else:
            print(f"不支持的模型: {model_provider}，返回默认助手。")
            return self.assistant


    def chat_in_background(self, message: str, history: list, model_provider: str) -> dict:
        """在后台线程中处理聊天消息"""
        try:
            assistant = self.get_assistant(model_provider)

            if not assistant or not assistant.ready:
                return {"success": False, "response": f"AI助手({model_provider})未就绪，请稍后重试。"}
            
            print(f"[BG_THREAD] 使用 {model_provider} 模型开始处理: '{message}'")
            response = assistant.process_query(message, history)
            print(f"[BG_THREAD] 处理完成，返回响应。")
            return {"success": True, "response": response}
        except Exception as e:
            print(f"[BG_THREAD] 发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "response": f"处理请求时发生错误: {e}"}

@app.route('/api/chat', methods=['POST'])
def chat():
    """API接口 - 聊天对话"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        history = data.get('history', []) # 从前端获取历史记录
        model_provider = data.get('model', 'gemini').lower() # 获取模型选择，默认为gemini

        if not message:
            return jsonify({"success": False, "response": "消息内容不能为空"}), 400

        # 将AI调用提交到线程池
        future = executor.submit(chat_manager.chat_in_background, message, history, model_provider)
        
        # 等待结果（设置超时）
        try:
            result = future.result(timeout=60) # 60秒超时
            return jsonify(result)
        except Exception as e:
            print(f"WebAPI: AI任务超时或执行失败: {e}")
            return jsonify({"success": False, "response": "AI服务响应超时或发生内部错误。"}), 504

    except Exception as e:
        print(f"WebAPI: /api/chat 发生未知错误: {e}")
        return jsonify({"success": False, "response": "服务器内部错误"}), 500


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
    print(f"!!! 404错误: {request.path} !!!")
    print(f"!!! 请求方法: {request.method} !!!")
    print(f"!!! 错误详情: {error} !!!")
    sys.stdout.flush()
    return jsonify({
        "error": "API接口不存在",
        "path": request.path,
        "method": request.method
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500


@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """测试端点"""
    print("\n*** TEST ENDPOINT CALLED ***")
    return jsonify({
        "status": "ok",
        "method": request.method,
        "time": datetime.now().isoformat()
    })


@app.route('/ping', methods=['GET', 'POST'])
def ping():
    """超简单的测试路由"""
    print("!!!!! PING被调用 !!!!!")
    sys.stdout.flush()
    return "PONG"  # 简单返回字符串


class DataManager:
    """数据管理器"""
    
    def __init__(self):
        self.last_refresh = None
        self.is_refreshing = False
        self.data_file = "web_data.json"
        self.master_file = "master_projects.csv"
    
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
        """刷新数据（基于master_projects.csv生成统计）"""
        if self.is_refreshing:
            return False
        
        self.is_refreshing = True
        try:
            print("开始刷新数据...")
            
            # 基于master_projects.csv生成统计数据
            if not os.path.exists(self.master_file):
                print(f"主数据文件不存在: {self.master_file}")
                return False
            
            import pandas as pd
            
            # 读取主数据
            print("1. 读取主数据文件...")
            df = pd.read_csv(self.master_file)
            
            # 计算统计信息
            print("2. 计算统计信息...")
            stats = {
                "projects_count": len(df),
                "brands_count": df['brand'].nunique() if 'brand' in df.columns else 0,
                "agencies_count": df['agency'].nunique() if 'agency' in df.columns else 0,
                "total_files": 1,  # master_projects.csv
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "master_projects.csv"
            }
            
            # 保存统计数据
            print("3. 保存统计数据...")
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            print(f"数据刷新成功: {stats['projects_count']}个项目, {stats['brands_count']}个品牌")
            self.last_refresh = datetime.now()
            return True
            
        except Exception as e:
            print(f"刷新数据过程中出错: {e}")
            return False
        finally:
            self.is_refreshing = False





# 创建管理器实例
data_manager = DataManager()
chat_manager = ChatManager() # 在程序启动时初始化一次


def main():
    """主函数"""
    print("=" * 60)
    print("数英网项目数据面板 Web 服务器")
    print("=" * 60)
    # 打印所有注册的路由
    print("\n已注册的路由:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    print()


    # 检查必要文件
    if not os.path.exists(data_manager.master_file):
        print(f"警告: 主数据文件 {data_manager.master_file} 不存在")
    
    if not os.path.exists("data"):
        print("警告: data 文件夹不存在")
    
    # 如果数据文件不存在，先运行一次数据分析
    if not os.path.exists(data_manager.data_file):
        print("数据文件不存在，正在初始化数据...")
        data_manager.refresh_data()
    
    chat_status = "可用" if chat_manager.assistant and chat_manager.assistant.ready else "初始化失败"
    
    print(f"\n服务器启动信息:")
    print(f"  - 访问地址: http://localhost:5000")
    print(f"  - 数据面板: http://localhost:5000")
    print(f"  - API状态: http://localhost:5000/api/status")
    print(f"  - 聊天API: http://localhost:5000/api/chat")
    print(f"  - 当前数据: {data_manager.get_current_data()}")
    print(f"  - 聊天状态: {chat_status}")
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
    print(f"正在运行的文件: {__file__}")
    print(f"文件修改时间: {datetime.fromtimestamp(os.path.getmtime(__file__))}")

    main()