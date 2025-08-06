"""
项目智能助手
整合数据管理和Gemini API，提供智能问答服务
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from project_data_manager import ProjectDataManager, SearchResult
from gemini_client import GeminiClient, QueryIntent


@dataclass
class ConversationTurn:
    """对话轮次数据结构"""
    query: str
    intent: QueryIntent
    search_result: SearchResult
    answer: str
    timestamp: str
    processing_time: float


class ProjectAssistant:
    """项目智能助手"""
    
    def __init__(self, 
                 data_path: str = "output/projects_summary.json",
                 gemini_api_key: str = None):
        """
        初始化智能助手
        
        Args:
            data_path: 项目数据文件路径
            gemini_api_key: Gemini API密钥
        """
        print("🤖 正在初始化项目智能助手...")
        
        # 初始化数据管理器
        self.data_manager = ProjectDataManager(data_path)
        
        # 如果没有传入API Key，尝试从配置文件获取
        if not gemini_api_key:
            try:
                from config_loader import get_config
                config = get_config()
                gemini_api_key = config.get('GEMINI_API_KEY')
                print("📡 从配置文件加载Gemini API密钥")
            except Exception as e:
                print(f"⚠️ 无法从配置文件获取API密钥: {e}")
        
        # 初始化Gemini客户端
        self.gemini_client = GeminiClient(gemini_api_key)
        
        # 对话历史
        self.conversation_history: List[ConversationTurn] = []
        
        # 系统状态
        self.ready = True
        
        print("✅ 项目智能助手初始化完成")
        print(f"📊 已加载 {len(self.data_manager.projects)} 个项目")
    
    def ask(self, query: str) -> str:
        """
        处理用户查询并返回回答
        
        Args:
            query: 用户查询
            
        Returns:
            智能回答
        """
        start_time = datetime.now()
        
        try:
            print(f"🔍 处理查询: '{query}'")
            
            # 1. 分析查询意图
            print("  1️⃣ 分析查询意图...")
            context = self._build_context()
            intent = self.gemini_client.analyze_query(query, context)
            print(f"     查询类型: {intent.query_type}")
            print(f"     置信度: {intent.confidence:.2f}")
            
            # 2. 执行数据搜索
            print("  2️⃣ 执行数据搜索...")
            search_result = self._execute_search(intent)
            print(f"     找到 {search_result.total_count} 个相关项目")
            
            # 3. 生成智能回答
            print("  3️⃣ 生成智能回答...")
            answer = self._generate_answer(query, intent, search_result)
            
            # 4. 记录对话
            processing_time = (datetime.now() - start_time).total_seconds()
            conversation_turn = ConversationTurn(
                query=query,
                intent=intent,
                search_result=search_result,
                answer=answer,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                processing_time=processing_time
            )
            
            self.conversation_history.append(conversation_turn)
            
            print(f"✅ 查询处理完成，耗时 {processing_time:.2f}秒")
            
            return answer
            
        except Exception as e:
            error_msg = f"很抱歉，处理您的查询时出现了问题: {str(e)}"
            print(f"❌ 查询处理失败: {e}")
            return error_msg
    
    def _build_context(self) -> str:
        """构建对话上下文"""
        if not self.conversation_history:
            return "这是对话的开始。"
        
        # 取最近3轮对话作为上下文
        recent_turns = self.conversation_history[-3:]
        context_parts = []
        
        for i, turn in enumerate(recent_turns, 1):
            context_parts.append(f"前{len(recent_turns)-i+1}轮:")
            context_parts.append(f"  用户问: {turn.query}")
            context_parts.append(f"  查询类型: {turn.intent.query_type}")
            context_parts.append(f"  结果数: {turn.search_result.total_count}")
        
        return "\n".join(context_parts)
    
    def _execute_search(self, intent: QueryIntent) -> SearchResult:
        """根据查询意图执行搜索"""
        
        # 根据查询类型选择搜索策略
        if intent.query_type == "statistics":
            return self._handle_statistics_query(intent)
        elif intent.query_type == "compare":
            return self._handle_compare_query(intent)
        else:
            return self._handle_search_query(intent)
    
    def _handle_search_query(self, intent: QueryIntent) -> SearchResult:
        """处理搜索类查询"""
        # 提取搜索参数
        brand = intent.entities.get('brand')
        agency = intent.entities.get('agency')
        keywords = intent.entities.get('keywords', [])
        
        # 处理关键词
        keyword = None
        if keywords:
            # 使用第一个关键词，或者合并多个关键词
            keyword = ' '.join(keywords) if len(keywords) > 1 else keywords[0]
        
        # 处理时间范围
        start_date = None
        end_date = None
        date_range = intent.filters.get('date_range')
        
        if date_range == 'recent':
            # 最近30天
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        elif date_range and date_range.isdigit():
            # 特定年份
            year = date_range
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
        elif date_range and '~' in date_range:
            # 日期范围
            try:
                start_date, end_date = date_range.split('~')
            except:
                pass
        
        # 处理数量限制
        limit = intent.filters.get('limit', 20)  # 默认限制20个结果
        if isinstance(limit, str) and limit.isdigit():
            limit = int(limit)
        elif not isinstance(limit, int):
            limit = 20
        
        # 执行高级搜索
        return self.data_manager.advanced_search(
            brand=brand,
            agency=agency,
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def _handle_statistics_query(self, intent: QueryIntent) -> SearchResult:
        """处理统计类查询"""
        # 获取统计信息
        stats = self.data_manager.get_statistics()
        
        # 构建统计结果
        # 这里创建一个特殊的SearchResult来承载统计信息
        return SearchResult(
            projects=[],  # 统计查询不返回具体项目
            total_count=0,
            query_info={
                "type": "statistics",
                "stats": stats,
                "intent": asdict(intent)
            },
            search_time=0.0
        )
    
    def _handle_compare_query(self, intent: QueryIntent) -> SearchResult:
        """处理对比类查询"""
        keywords = intent.entities.get('keywords', [])
        
        if len(keywords) >= 2:
            # 对比两个关键词相关的项目
            results1 = self.data_manager.search_by_keyword(keywords[0])
            results2 = self.data_manager.search_by_keyword(keywords[1])
            
            # 合并结果
            combined_results = results1 + results2
            
            return SearchResult(
                projects=combined_results[:20],  # 限制结果数量
                total_count=len(combined_results),
                query_info={
                    "type": "compare",
                    "keywords": keywords,
                    "results1_count": len(results1),
                    "results2_count": len(results2),
                    "intent": asdict(intent)
                },
                search_time=0.0
            )
        else:
            # 回退到普通搜索
            return self._handle_search_query(intent)
    
    def _generate_answer(self, query: str, intent: QueryIntent, search_result: SearchResult) -> str:
        """生成智能回答"""
        
        # 特殊处理统计类查询
        if intent.query_type == "statistics" and search_result.query_info.get("type") == "statistics":
            return self._generate_statistics_answer(query, search_result.query_info["stats"])
        
        # 使用Gemini生成自然语言回答
        answer = self.gemini_client.generate_answer(
            query=query,
            search_results=search_result.projects,
            query_info=search_result.query_info
        )
        
        # 添加搜索信息摘要
        if search_result.total_count > 0:
            summary = f"\n\n📊 搜索摘要: 找到 {search_result.total_count} 个相关项目，耗时 {search_result.search_time:.3f}秒"
            if search_result.total_count > 10:
                summary += f"（显示前10个）"
            answer += summary
        
        return answer
    
    def _generate_statistics_answer(self, query: str, stats: Dict) -> str:
        """生成统计类回答"""
        answer_parts = []
        
        # 基本统计
        answer_parts.append(f"📊 **项目数据统计概览**")
        answer_parts.append(f"• 总项目数: **{stats['total_projects']}** 个")
        answer_parts.append(f"• 涉及品牌: **{stats['total_brands']}** 个")
        answer_parts.append(f"• 合作代理商: **{stats['total_agencies']}** 个")
        
        # 日期范围
        if stats['date_range']['earliest'] and stats['date_range']['latest']:
            answer_parts.append(f"• 时间跨度: {stats['date_range']['earliest']} 至 {stats['date_range']['latest']}")
        
        # 热门品牌
        if stats['top_brands']:
            answer_parts.append(f"\n🏆 **项目数量最多的品牌 TOP5:**")
            for i, (brand, count) in enumerate(stats['top_brands'][:5], 1):
                answer_parts.append(f"{i}. {brand}: {count} 个项目")
        
        # 热门代理商
        if stats['top_agencies']:
            answer_parts.append(f"\n🏢 **项目数量最多的代理商 TOP5:**")
            for i, (agency, count) in enumerate(stats['top_agencies'][:5], 1):
                answer_parts.append(f"{i}. {agency}: {count} 个项目")
        
        # 月度分布（显示最近6个月）
        if stats['monthly_distribution']:
            answer_parts.append(f"\n📅 **最近月份项目分布:**")
            sorted_months = sorted(stats['monthly_distribution'].items(), reverse=True)[:6]
            for month, count in sorted_months:
                answer_parts.append(f"• {month}: {count} 个项目")
        
        answer_parts.append(f"\n📈 最后更新时间: {stats['last_updated']}")
        
        return "\n".join(answer_parts)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        if not self.conversation_history:
            return {"message": "还没有对话记录"}
        
        total_turns = len(self.conversation_history)
        total_projects_found = sum(turn.search_result.total_count for turn in self.conversation_history)
        avg_processing_time = sum(turn.processing_time for turn in self.conversation_history) / total_turns
        
        query_types = [turn.intent.query_type for turn in self.conversation_history]
        query_type_counts = {}
        for qt in query_types:
            query_type_counts[qt] = query_type_counts.get(qt, 0) + 1
        
        return {
            "total_turns": total_turns,
            "total_projects_found": total_projects_found,
            "avg_processing_time": round(avg_processing_time, 2),
            "query_type_distribution": query_type_counts,
            "first_query_time": self.conversation_history[0].timestamp,
            "last_query_time": self.conversation_history[-1].timestamp,
        }
    
    def export_conversation(self, filename: str = None) -> str:
        """导出对话记录"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"conversation_export_{timestamp}.json"
        
        export_data = {
            "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "summary": self.get_conversation_summary(),
            "conversations": [asdict(turn) for turn in self.conversation_history]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 对话记录已导出到: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 导出对话记录失败: {e}")
            return ""
    
    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_history = []
        self.gemini_client.clear_conversation_history()
        print("✅ 对话历史已清空")
    
    def refresh_data(self) -> bool:
        """刷新项目数据"""
        return self.data_manager.refresh_data()
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        data_stats = self.data_manager.get_statistics()
        
        return {
            "ready": self.ready,
            "data_manager": {
                "projects_count": len(self.data_manager.projects),
                "last_updated": data_stats['last_updated'],
                "brands_count": data_stats['total_brands'],
                "agencies_count": data_stats['total_agencies']
            },
            "gemini_client": {
                "api_available": True,  # 假设可用，实际使用时可以测试
                "conversation_turns": len(self.gemini_client.conversation_history)
            },
            "conversation": {
                "total_turns": len(self.conversation_history),
                "summary": self.get_conversation_summary() if self.conversation_history else None
            }
        }


if __name__ == "__main__":
    # 测试智能助手
    print("🧪 测试项目智能助手...")
    
    try:
        # 初始化助手（需要设置GEMINI_API_KEY环境变量）
        assistant = ProjectAssistant()
        
        # 获取系统状态
        status = assistant.get_system_status()
        print(f"📊 系统状态: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        # 测试查询
        test_queries = [
            "有多少个项目？",
            "最近有哪些营销项目？",
            "找一些关于汽车品牌的创意案例",
        ]
        
        for query in test_queries:
            print(f"\n🤖 用户: {query}")
            answer = assistant.ask(query)
            print(f"💬 助手: {answer}")
        
        # 显示对话摘要
        summary = assistant.get_conversation_summary()
        print(f"\n📋 对话摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        
        print("\n✅ 智能助手测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("💡 请确保:")
        print("1. 设置了GEMINI_API_KEY环境变量")
        print("2. 存在项目数据文件 output/projects_summary.json")
        print("3. 安装了必要的依赖包: google-generativeai jieba")