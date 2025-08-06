#!/usr/bin/env python3
"""
启动脚本 - 启动数英网数据面板Web服务器
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
from config_loader import get_config

def check_dependencies():
    """检查依赖"""
    print("🔧 检查系统依赖...")
    
    required_packages = [
        'flask',
        'flask-cors',
        'pandas',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖包: {', '.join(missing_packages)}")
        print("💡 请运行以下命令安装:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依赖检查通过")
    return True

def check_data_files():
    """检查数据文件"""
    print("\n📁 检查数据文件...")
    
    # 检查data文件夹
    if not os.path.exists("data"):
        print("❌ data文件夹不存在")
        return False
    
    # 检查Excel文件
    excel_files = list(Path("data").glob("*.xlsx"))
    if not excel_files:
        print("❌ data文件夹中没有Excel文件")
        return False
    
    print(f"✅ 找到 {len(excel_files)} 个Excel文件")
    return True

def generate_web_data():
    """生成Web数据文件"""
    print("\n📊 生成Web数据文件...")
    
    try:
        # 运行数据分析脚本
        result = subprocess.run([sys.executable, 'data_analyzer.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Web数据文件生成成功")
            return True
        else:
            print(f"❌ 数据分析脚本执行失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 数据分析超时")
        return False
    except Exception as e:
        print(f"❌ 生成数据文件时出错: {e}")
        return False

def check_gemini_config():
    """检查Gemini配置"""
    print("\n🤖 检查Gemini配置...")
    
    config = get_config()
    api_key = config.get('GEMINI_API_KEY')
    
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("⚠️ 未设置GEMINI_API_KEY")
        print("💡 聊天功能可能不可用")
        print("   请编辑 config.env 文件，设置您的 Gemini API 密钥")
        return False
    
    print("✅ Gemini API密钥已配置")
    return True

def start_server():
    """启动Web服务器"""
    print("\n🚀 启动Web服务器...")
    
    config = get_config()
    server_port = config.get_int('SERVER_PORT', 5000)
    auto_open_browser = config.get_bool('AUTO_OPEN_BROWSER', True)
    browser_url = config.get('BROWSER_URL', f'http://localhost:{server_port}')
    
    try:
        # 确保环境变量被正确传递，包括配置文件中的设置
        env = os.environ.copy()
        
        # 确保将配置文件中的环境变量添加到子进程环境中
        for key, value in config.get_all().items():
            env[key] = str(value)
        
        # 启动Flask服务器
        server_process = subprocess.Popen([
            sys.executable, 'web_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        
        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        time.sleep(3)
        
        # 检查服务器是否正常启动
        if server_process.poll() is None:
            print("✅ Web服务器启动成功")
            print(f"📱 访问地址: {browser_url}")
            
            # 自动打开浏览器
            if auto_open_browser:
                try:
                    webbrowser.open(browser_url)
                    print("🌐 已自动打开浏览器")
                except:
                    print("⚠️ 无法自动打开浏览器，请手动访问")
            else:
                print("💡 请手动打开浏览器访问")
            
            return server_process
        else:
            stdout, stderr = server_process.communicate()
            print(f"❌ 服务器启动失败:")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("数英网数据面板启动器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺少的包后重试")
        return
    
    # 检查数据文件
    if not check_data_files():
        print("\n❌ 数据文件检查失败")
        print("💡 请确保data文件夹中有Excel文件")
        return
    
    # 生成Web数据文件
    if not generate_web_data():
        print("\n❌ 数据文件生成失败")
        return
    
    # 检查Gemini配置
    check_gemini_config()
    
    # 启动服务器
    server_process = start_server()
    
    if server_process:
        print("\n" + "=" * 60)
        print("🎉 系统启动完成！")
        print("=" * 60)
        print("📋 功能说明:")
        print("  • 左侧: 品牌和项目统计数据")
        print("  • 右侧: AI智能对话功能")
        print("  • 右上角: 刷新数据按钮")
        print("\n💡 使用提示:")
        print("  • 可以询问项目统计、品牌分析等问题")
        print("  • 支持自然语言查询")
        print("  • 数据会自动更新")
        print("\n按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        try:
            # 等待用户中断
            server_process.wait()
        except KeyboardInterrupt:
            print("\n\n🛑 正在停止服务器...")
            server_process.terminate()
            server_process.wait()
            print("✅ 服务器已停止")
    else:
        print("\n❌ 服务器启动失败")

if __name__ == "__main__":
    main()