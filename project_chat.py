#!/usr/bin/env python3
"""
项目智能问答系统 - 交互界面
基于Gemini API的数英网项目数据智能问答
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional
import signal

from project_assistant import ProjectAssistant


class ProjectChatInterface:
    """项目问答系统交互界面"""
    
    def __init__(self):
        """初始化交互界面"""
        self.assistant: Optional[ProjectAssistant] = None
        self.running = True
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器（处理Ctrl+C）"""
        print("\n\n👋 感谢使用项目智能问答系统！")
        self.running = False
        if self.assistant:
            self._show_session_summary()
        sys.exit(0)
    
    def display_welcome(self):
        """显示欢迎信息"""
        print("=" * 80)
        print("🤖 数英网项目智能问答系统")
        print("=" * 80)
        print("✨ 功能特性:")
        print("  • 🔍 智能项目搜索 - 用自然语言查找项目")
        print("  • 📊 数据统计分析 - 获取项目统计信息")
        print("  • 🆚 项目对比分析 - 对比不同项目特点")
        print("  • 💡 深度洞察分析 - 分析行业趋势和特点")
        print("  • 🗣️ 连续对话 - 支持上下文理解")
        print("=" * 80)
        print("💡 示例问题:")
        print("  • '有多少个营销项目？'")
        print("  • '找一些可口可乐的创意案例'")
        print("  • '最近有哪些汽车广告？'")
        print("  • '对比宝马和奔驰的营销策略'")
        print("  • '统计各个品牌的项目数量'")
        print("=" * 80)
    
    def check_prerequisites(self) -> bool:
        """检查运行前提条件"""
        print("🔧 正在检查系统环境...")
        
        # 检查数据文件
        data_file = "output/projects_summary.json"
        if not os.path.exists(data_file):
            print(f"❌ 未找到项目数据文件: {data_file}")
            print("💡 解决方案:")
            print("   1. 运行爬虫程序获取数据: python run_scraper.py")
            print("   2. 确保爬虫已成功抓取项目数据")
            return False
        
        # 检查API密钥
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ 未设置Gemini API密钥")
            print("💡 解决方案:")
            print("   1. 获取Gemini API密钥: https://ai.google.dev/")
            print("   2. 设置环境变量: set GEMINI_API_KEY=your_api_key")
            print("   3. 或在当前会话中输入API密钥")
            
            # 允许用户手动输入API密钥
            manual_key = input("\n🔑 请输入Gemini API密钥 (或按Enter跳过): ").strip()
            if manual_key:
                os.environ['GEMINI_API_KEY'] = manual_key
                print("✅ API密钥已设置")
            else:
                return False
        
        # 检查依赖包
        try:
            import google.generativeai
            import jieba
        except ImportError as e:
            print(f"❌ 缺少必要依赖包: {e}")
            print("💡 解决方案:")
            print("   pip install google-generativeai jieba")
            return False
        
        print("✅ 环境检查通过")
        return True
    
    def initialize_assistant(self) -> bool:
        """初始化智能助手"""
        print("🤖 正在初始化智能助手...")
        
        try:
            self.assistant = ProjectAssistant()
            
            # 获取系统状态
            status = self.assistant.get_system_status()
            
            print("✅ 智能助手初始化成功")
            print(f"📊 已加载 {status['data_manager']['projects_count']} 个项目")
            print(f"🏢 涉及 {status['data_manager']['brands_count']} 个品牌")
            print(f"🎯 合作 {status['data_manager']['agencies_count']} 个代理商")
            
            if status['data_manager']['last_updated']:
                print(f"📅 数据最后更新: {status['data_manager']['last_updated']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 智能助手初始化失败: {e}")
            return False
    
    def show_help(self):
        """显示帮助信息"""
        print("\n📖 帮助信息:")
        print("=" * 50)
        print("🎯 查询类型:")
        print("  • 搜索查询: '找一些XX的项目'")
        print("  • 统计查询: '有多少个项目？'")
        print("  • 对比查询: '对比XX和YY'")
        print("  • 分析查询: '分析XX的特点'")
        print()
        print("💬 系统命令:")
        print("  • /help - 显示帮助信息")
        print("  • /status - 查看系统状态")
        print("  • /stats - 查看数据统计")
        print("  • /history - 查看对话历史")
        print("  • /export - 导出对话记录")
        print("  • /clear - 清空对话历史")
        print("  • /refresh - 刷新项目数据")
        print("  • /quit - 退出系统")
        print("=" * 50)
    
    def handle_system_command(self, command: str) -> bool:
        """
        处理系统命令
        
        Args:
            command: 系统命令
            
        Returns:
            是否继续运行
        """
        command = command.lower().strip()
        
        if command == '/help':
            self.show_help()
            
        elif command == '/status':
            self._show_system_status()
            
        elif command == '/stats':
            self._show_data_statistics()
            
        elif command == '/history':
            self._show_conversation_history()
            
        elif command == '/export':
            self._export_conversation()
            
        elif command == '/clear':
            self._clear_conversation()
            
        elif command == '/refresh':
            self._refresh_data()
            
        elif command == '/quit':
            print("👋 感谢使用项目智能问答系统！")
            self._show_session_summary()
            return False
            
        else:
            print(f"❌ 未知命令: {command}")
            print("💡 输入 /help 查看可用命令")
        
        return True
    
    def _show_system_status(self):
        """显示系统状态"""
        print("\n🔧 系统状态:")
        status = self.assistant.get_system_status()
        print(f"  • 系统状态: {'✅ 正常' if status['ready'] else '❌ 异常'}")
        print(f"  • 项目数据: {status['data_manager']['projects_count']} 个项目")
        print(f"  • 对话轮次: {status['conversation']['total_turns']} 轮")
        print(f"  • 最后更新: {status['data_manager']['last_updated'] or '未知'}")
    
    def _show_data_statistics(self):
        """显示数据统计"""
        print("\n📊 数据统计:")
        stats = self.assistant.data_manager.get_statistics()
        
        print(f"  • 总项目数: {stats['total_projects']} 个")
        print(f"  • 涉及品牌: {stats['total_brands']} 个")
        print(f"  • 合作代理商: {stats['total_agencies']} 个")
        
        if stats['date_range']['earliest'] and stats['date_range']['latest']:
            print(f"  • 时间跨度: {stats['date_range']['earliest']} ~ {stats['date_range']['latest']}")
        
        print("\n🏆 热门品牌 TOP5:")
        for i, (brand, count) in enumerate(stats['top_brands'][:5], 1):
            print(f"    {i}. {brand}: {count} 个项目")
    
    def _show_conversation_history(self):
        """显示对话历史"""
        if not self.assistant.conversation_history:
            print("\n💬 还没有对话记录")
            return
        
        print(f"\n💬 对话历史 (最近10轮):")
        recent_turns = self.assistant.conversation_history[-10:]
        
        for i, turn in enumerate(recent_turns, 1):
            print(f"\n--- 第 {len(self.assistant.conversation_history) - len(recent_turns) + i} 轮 ---")
            print(f"🗣️ 用户: {turn.query}")
            print(f"🤖 助手: {turn.answer[:100]}{'...' if len(turn.answer) > 100 else ''}")
            print(f"📊 结果: {turn.search_result.total_count} 个项目, 耗时 {turn.processing_time:.2f}秒")
    
    def _export_conversation(self):
        """导出对话记录"""
        if not self.assistant.conversation_history:
            print("\n💬 没有对话记录可导出")
            return
        
        filename = self.assistant.export_conversation()
        if filename:
            print(f"✅ 对话记录已导出到: {filename}")
        else:
            print("❌ 导出失败")
    
    def _clear_conversation(self):
        """清空对话历史"""
        confirm = input("确认清空对话历史吗? (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            self.assistant.clear_conversation()
        else:
            print("操作已取消")
    
    def _refresh_data(self):
        """刷新项目数据"""
        print("🔄 正在刷新项目数据...")
        if self.assistant.refresh_data():
            print("✅ 数据刷新成功")
            self._show_data_statistics()
        else:
            print("❌ 数据刷新失败")
    
    def _show_session_summary(self):
        """显示会话摘要"""
        if not self.assistant or not self.assistant.conversation_history:
            return
        
        summary = self.assistant.get_conversation_summary()
        print("\n📋 本次会话摘要:")
        print(f"  • 对话轮次: {summary['total_turns']} 轮")
        print(f"  • 查找项目: {summary['total_projects_found']} 个")
        print(f"  • 平均响应时间: {summary['avg_processing_time']} 秒")
        print(f"  • 会话时长: {summary['first_query_time']} ~ {summary['last_query_time']}")
    
    def chat_loop(self):
        """主要聊天循环"""
        print("\n💬 开始对话 (输入 /help 查看帮助, /quit 退出)")
        print("=" * 80)
        
        while self.running:
            try:
                # 获取用户输入
                user_input = input("\n🗣️ 您: ").strip()
                
                if not user_input:
                    continue
                
                # 处理系统命令
                if user_input.startswith('/'):
                    if not self.handle_system_command(user_input):
                        break
                    continue
                
                # 处理普通查询
                print("🤖 正在思考...")
                answer = self.assistant.ask(user_input)
                
                print(f"\n🤖 助手: {answer}")
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                print(f"\n❌ 处理过程中出现错误: {e}")
                print("💡 请重试或输入 /help 查看帮助")
    
    def run(self):
        """运行交互界面"""
        try:
            # 显示欢迎信息
            self.display_welcome()
            
            # 检查前提条件
            if not self.check_prerequisites():
                return
            
            # 初始化智能助手
            if not self.initialize_assistant():
                return
            
            # 开始聊天循环
            self.chat_loop()
            
        except Exception as e:
            print(f"❌ 系统运行出错: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理资源
            if self.assistant:
                self._show_session_summary()


def main():
    """主函数"""
    interface = ProjectChatInterface()
    interface.run()


if __name__ == "__main__":
    main()