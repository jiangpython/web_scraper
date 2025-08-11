#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能AI助手 - 简化版
基于CSV数据 + 智能内容长度控制 + 独立提示词模板
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

from prompt_manager import PromptManager
from gemini_client import GeminiClient
from deepseek_client import DeepSeekClient
from config_optimized import get_config

class ContentLengthManager:
    """内容长度智能管理器"""
    
    def __init__(self):
        self.max_chars = 4500  # 单次响应最大字符数
        self.project_avg_chars = 1500  # 单个项目详情平均字符数
        self.max_projects_per_response = 3  # 单次最多返回项目数
    
    def calculate_response_limit(self, query_type: str, total_found: int) -> int:
        """计算合理的返回数量限制"""
        if query_type in ["search", "filter"] and total_found > 0:
            # 详细项目查询，根据内容长度动态调整
            estimated_limit = self.max_chars // self.project_avg_chars
            return min(estimated_limit, self.max_projects_per_response, total_found)
        elif query_type in ["statistics", "count", "list_brands"]:
            # 统计类查询不受严格限制
            return min(100, total_found)
        else:
            return min(5, total_found)
    
    def check_content_length(self, content: str) -> Dict[str, Any]:
        """检查内容长度并给出建议"""
        char_count = len(content)
        
        return {
            "char_count": char_count,
            "exceeds_limit": char_count > self.max_chars,
            "truncate_suggestion": f"内容较长({char_count}字符)，建议分批显示" if char_count > self.max_chars else None
        }

class SmartQueryExecutor:
    """智能查询执行器 - 基于CSV数据"""
    
    def __init__(self):
        self.master_df = None
        self.scraped_df = None
        self.content_manager = ContentLengthManager()
        
        # 加载数据
        self._load_data()
    
    def _load_data(self):
        """加载CSV数据文件"""
        try:
            # 加载主数据文件
            if os.path.exists('master_projects.csv'):
                self.master_df = pd.read_csv('master_projects.csv')
                print(f"成功加载主数据: {len(self.master_df)} 个项目")
            else:
                print("警告: master_projects.csv 不存在")
                return
            
            # 加载爬取进度文件（可选）
            if os.path.exists('scraped_projects.csv'):
                self.scraped_df = pd.read_csv('scraped_projects.csv')
                print(f"加载爬取进度: {len(self.scraped_df)} 个项目")
            
        except Exception as e:
            print(f"数据加载失败: {e}")
    
    def execute_query(self, instruction: Dict) -> Dict[str, Any]:
        """执行查询指令"""
        if self.master_df is None:
            raise Exception("数据未加载，无法执行查询")
        
        query_type = instruction.get("query_type", "")
        include_details = instruction.get("include_details", False)
        
        # 执行基础查询
        if query_type == "count":
            return self._execute_count_query(instruction)
        elif query_type == "list_brands":
            return self._execute_list_brands_query(instruction)
        elif query_type == "list_agencies":
            return self._execute_list_agencies_query(instruction)
        elif query_type == "search":
            return self._execute_search_query(instruction)
        elif query_type == "filter":
            return self._execute_filter_query(instruction)
        elif query_type == "statistics":
            return self._execute_statistics_query(instruction)
        elif query_type == "aggregate":
            return self._execute_aggregate_query(instruction)
        else:
            raise Exception(f"不支持的查询类型: {query_type}")
    
    def _execute_count_query(self, instruction: Dict) -> Dict[str, Any]:
        """执行计数查询"""
        df = self.master_df.copy()
        filters = instruction.get("filters", {})
        
        # 应用过滤条件
        df = self._apply_filters(df, filters)
        
        return {
            "query_type": "count",
            "total_count": len(df),
            "filters_applied": filters,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_list_brands_query(self, instruction: Dict) -> Dict[str, Any]:
        """列出所有品牌"""
        df = self.master_df.copy()
        
        # 获取所有唯一品牌
        brands = df['brand'].dropna().unique().tolist()
        brand_counts = df['brand'].value_counts().to_dict()
        
        # 按项目数量排序
        sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "query_type": "list_brands",
            "total_brands": len(brands),
            "top_brands": sorted_brands[:20],  # 显示前20个
            "all_brands": brands,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_list_agencies_query(self, instruction: Dict) -> Dict[str, Any]:
        """列出所有代理商"""
        df = self.master_df.copy()
        
        agencies = df['agency'].dropna().unique().tolist()
        agency_counts = df['agency'].value_counts().to_dict()
        
        sorted_agencies = sorted(agency_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "query_type": "list_agencies",
            "total_agencies": len(agencies),
            "top_agencies": sorted_agencies[:20],
            "all_agencies": agencies,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_search_query(self, instruction: Dict) -> Dict[str, Any]:
        """执行搜索查询"""
        df = self.master_df.copy()
        filters = instruction.get("filters", {})
        limit = instruction.get("limit", 10)
        include_details = instruction.get("include_details", False)
        
        # 应用过滤条件
        df = self._apply_filters(df, filters)
        
        # 获取项目ID列表
        project_ids = df['project_id'].tolist()
        
        # 智能限制返回数量
        actual_limit = self.content_manager.calculate_response_limit("search", len(project_ids))
        limited_df = df.head(actual_limit)
        
        # 构建基础结果
        result = {
            "query_type": "search",
            "total_found": len(df),
            "returned_count": len(limited_df),
            "has_more": len(df) > actual_limit,
            "remaining_count": max(0, len(df) - actual_limit),
            "projects": limited_df.to_dict('records'),
            "execution_time": datetime.now().isoformat()
        }
        
        # 如果需要详细内容，尝试加载
        if include_details:
            # 确保project_id转换为字符串列表
            project_ids = [str(pid) for pid in limited_df['project_id'].tolist()]
            detailed_projects = self._load_project_details(project_ids)
            result["detailed_projects"] = detailed_projects
        
        return result
    
    def _execute_aggregate_query(self, instruction: Dict) -> Dict[str, Any]:
        """执行聚合查询"""
        df = self.master_df.copy()
        filters = instruction.get("filters", {})
        aggregations = instruction.get("aggregations", {})
        
        # 应用过滤条件
        df = self._apply_filters(df, filters)
        
        results = {"query_type": "aggregate"}
        
        # 执行各种聚合操作
        for agg_type, field in aggregations.items():
            if field not in df.columns:
                continue
                
            if agg_type == "distinct_count":
                results[f"{field}_distinct_count"] = df[field].nunique()
            elif agg_type == "count":
                results[f"{field}_count"] = df[field].count()
            elif agg_type == "distinct_list":
                unique_values = df[field].dropna().unique().tolist()
                results[f"{field}_list"] = unique_values
            elif agg_type == "value_counts":
                value_counts = df[field].value_counts().head(20).to_dict()
                results[f"{field}_value_counts"] = value_counts
        
        results["total_records"] = len(df)
        results["execution_time"] = datetime.now().isoformat()
        
        return results

    def _execute_filter_query(self, instruction: Dict) -> Dict[str, Any]:
        """执行过滤查询（与search类似）"""
        return self._execute_search_query(instruction)

    def _execute_statistics_query(self, instruction: Dict) -> Dict[str, Any]:
        """执行统计查询"""
        df = self.master_df.copy()
        filters = instruction.get("filters", {})

        # 应用过滤条件
        df = self._apply_filters(df, filters)

        # 统计信息
        stats = {
            "query_type": "statistics",
            "total_count": len(df),
            "brand_count": df['brand'].nunique(),
            "agency_count": df['agency'].nunique(),
            "date_range": {
                "earliest": df['publish_date'].min(),
                "latest": df['publish_date'].max()
            },
            "top_brands": df['brand'].value_counts().head(10).to_dict(),
            "top_agencies": df['agency'].value_counts().head(10).to_dict(),
            "execution_time": datetime.now().isoformat()
        }

        return stats



    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """应用过滤条件"""
        for field, condition in filters.items():
            if field not in df.columns:
                continue
            
            if isinstance(condition, str):
                # 字符串模糊匹配 - 需要处理不同数据类型
                if field == 'project_id':
                    # project_id是数字类型，转换为字符串或直接数值比较
                    try:
                        # 尝试转换为数字进行精确匹配
                        condition_num = int(condition)
                        df = df[df[field] == condition_num]
                    except ValueError:
                        # 转换失败则跳过该条件
                        continue
                elif df[field].dtype == 'object':
                    # 字符串字段使用模糊匹配
                    df = df[df[field].str.contains(condition, na=False, case=False)]
                else:
                    # 其他类型尝试精确匹配
                    try:
                        df = df[df[field] == condition]
                    except:
                        continue
            elif isinstance(condition, (int, float)):
                # 数值精确匹配
                df = df[df[field] == condition]
            elif isinstance(condition, list):
                # 列表精确匹配
                df = df[df[field].isin(condition)]
            elif isinstance(condition, dict):
                # 复杂条件（如日期范围）
                if "start" in condition and field == "publish_date":
                    df = df[pd.to_datetime(df[field], errors='coerce') >= pd.to_datetime(condition["start"])]
                if "end" in condition and field == "publish_date":
                    df = df[pd.to_datetime(df[field], errors='coerce') <= pd.to_datetime(condition["end"])]
        
        return df
    
    def _load_project_details(self, project_ids: List[str]) -> List[Dict[str, Any]]:
        """从batch文件中加载项目详细内容"""
        detailed_projects = []
        
        try:
            details_dir = "output/details"
            if not os.path.exists(details_dir):
                return detailed_projects
            
            # 搜索所有batch文件
            batch_files = [f for f in os.listdir(details_dir) if f.startswith('batch_') and f.endswith('.json')]
            
            for batch_file in batch_files:
                batch_path = os.path.join(details_dir, batch_file)
                
                try:
                    with open(batch_path, 'r', encoding='utf-8') as f:
                        batch_data = json.load(f)
                    
                    # 查找匹配的项目
                    projects = batch_data.get('projects', [])
                    for project in projects:
                        if str(project.get('id')) in project_ids:
                            detailed_projects.append(project)
                            print(f"✓ 成功加载项目详情: {project.get('title', 'Unknown')[:50]}...")
                            
                except json.JSONDecodeError as e:
                    # JSON文件损坏，跳过但不打印错误（避免日志污染）
                    continue
                except Exception as e:
                    print(f"读取batch文件失败 {batch_file}: {e}")
                    continue
        
        except Exception as e:
            print(f"加载详细内容失败: {e}")
        
        return detailed_projects

class SmartAIAssistant:
    """智能AI助手 - 简化版"""
    
    def __init__(self, model_provider: str = "gemini", gemini_api_key: str = None, deepseek_api_key: str = None):
        self.prompt_manager = PromptManager()
        self.query_executor = SmartQueryExecutor()
        self.config = get_config()
        self.max_history_length = self.config.get_int('MAX_CHAT_HISTORY', 5)
        self.model_provider = model_provider
        self.client = None
        self.ready = False

        try:
            if self.model_provider == "gemini":
                api_key = gemini_api_key or self.config.get('GEMINI_API_KEY')
                self.client = GeminiClient(api_key=api_key)
            elif self.model_provider == "deepseek":
                api_key = deepseek_api_key or self.config.get('DEEPSEEK_API_KEY')
                self.client = DeepSeekClient(api_key=api_key)
            else:
                raise ValueError(f"不支持的模型提供商: {self.model_provider}")

            if self.client:
                # 假设所有客户端都有一个 ready 属性或类似的连接测试
                self.ready = self.client.test_connection() if hasattr(self.client, 'test_connection') else True

            if not self.ready:
                 print(f"{model_provider.capitalize()} 客户端连接测试失败或未准备就绪。")

        except Exception as e:
            print(f"AI客户端 ({self.model_provider}) 初始化失败: {e}")
            self.client = None
            self.ready = False
    
    def process_query(self, user_query: str, history: List[Dict[str, str]] = None) -> str:
        """处理用户查询，可选地包含聊天记录"""
        try:
            if not self.ready:
                return "AI系统未准备就绪，请检查API配置"

            history = history or []
            
            # 限制历史记录长度
            if len(history) > self.max_history_length * 2 : # 每个对话是2条记录
                history = history[-(self.max_history_length * 2):]

            # Deepseek client 需要 history
            if self.model_provider == 'deepseek':
                return self.client.generate_response(user_query, history=history)

            formatted_history = self._format_history(history)

            print(f"\n{'=' * 50}")
            print(f"用户查询: {user_query}")
            if formatted_history:
                print(f"包含历史记录: {len(history)} 条")
            print(f"{'=' * 50}")

            # 1. 生成查询分析提示词
            analysis_prompt = self.prompt_manager.get_query_analysis_prompt(user_query, formatted_history)
            
            # 2. AI分析用户查询，生成查询指令
            ai_response = self.client.generate_response(analysis_prompt)
            
            # 3. 解析AI响应
            query_instruction = self._parse_ai_response(ai_response)
            
            # 4. 执行查询
            query_results = self.query_executor.execute_query(query_instruction)
            
            # 5. 生成最终回答
            final_answer = self._generate_final_answer(user_query, query_results, formatted_history)
            
            return final_answer
            
        except Exception as e:
            error_msg = self.prompt_manager.get_error_message("query_error", error_message=str(e))
            return error_msg

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """将历史记录格式化为字符串"""
        if not history:
            return ""
        
        formatted_lines = []
        for message in history:
            role = "用户" if message.get("role") == "user" else "助手"
            content = message.get("content", "")
            formatted_lines.append(f"{role}: {content}")
        
        return "\n".join(formatted_lines)
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """解析AI响应为查询指令"""
        try:
            # 尝试从响应中提取JSON
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                ai_result = json.loads(json_str)
                
                # 直接使用AI返回的查询类型（现在提示词已经标准化）
                query_type = ai_result.get('query_type', 'search')
                filters = ai_result.get('filters', {})
                explanation = ai_result.get('explanation', '查询指令')
                
                return {
                    "query_type": query_type,
                    "include_details": query_type == 'search',
                    "filters": filters,
                    "explanation": explanation
                }
            else:
                # 如果没有找到JSON，分析用户问题的关键词
                return self._fallback_query_analysis(ai_response)
                
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"AI响应: {ai_response[:200]}")
            # JSON解析失败，分析用户问题
            return self._fallback_query_analysis(ai_response)
    
    def _fallback_query_analysis(self, text: str) -> Dict[str, Any]:
        """备用查询分析 - 基于关键词"""
        text_lower = text.lower()
        
        # 简单的查询类型判断
        if any(word in text_lower for word in ['多少', '数量', '统计', '几个']):
            return {
                "query_type": "count",
                "include_details": False,
                "filters": {},
                "explanation": "统计查询"
            }
        elif any(word in text_lower for word in ['品牌', '列出品牌']):
            return {
                "query_type": "list_brands",
                "include_details": False,
                "filters": {},
                "explanation": "品牌列表查询"
            }
        elif any(word in text_lower for word in ['代理商', '列出代理商']):
            return {
                "query_type": "list_agencies", 
                "include_details": False,
                "filters": {},
                "explanation": "代理商列表查询"
            }
        else:
            return {
                "query_type": "search",
                "include_details": False,
                "filters": {},
                "explanation": "默认搜索查询"
            }
    

    
    def _generate_final_answer(self, original_question: str, query_results: Dict[str, Any], formatted_history: str) -> str:
        """生成最终回答"""
        try:
            # 检查是否有结果
            if self._is_empty_result(query_results):
                return self.prompt_manager.get_error_message("no_results")
            
            # 智能截断，确保上下文不会过长
            simplified_results = self._simplify_results_for_ai(query_results)

            # 生成回答提示词
            answer_prompt = self.prompt_manager.get_answer_generation_prompt(
                original_question, simplified_results, formatted_history
            )
            
            # 打印用于调试的提示词
            print(f"\n[AI Assistant] 最终回答生成提示词 (前400字符):\n{answer_prompt[:400]}...")

            # AI生成最终回答
            final_answer = self.client.generate_response(answer_prompt)
            
            # 如果有分页信息，添加分页提示
            if query_results.get("has_more", False):
                pagination_info = self._generate_pagination_info(query_results)
                final_answer += "\n\n" + pagination_info
            
            return final_answer
            
        except Exception as e:
            # 打印详细错误以供调试
            import traceback
            print("[AI Assistant] 生成最终回答时发生错误:")
            traceback.print_exc()
            return f"生成回答时出错: {str(e)}"

    def _simplify_results_for_ai(self, query_results: Dict[str, Any]) -> Dict[str, Any]:
        """简化查询结果以适应AI提示词长度限制"""
        simplified = query_results.copy()

        # 1. 精简项目列表，但保留更多信息
        if "projects" in simplified and simplified["projects"]:
            simplified_projects = []
            for p in simplified["projects"][:20]: # 最多给AI看20个项目
                project_info = {
                    "title": p.get("title", "N/A"),
                    "brand": p.get("brand", "N/A"),
                    "agency": p.get("agency", "N/A"),
                    "publish_date": p.get("publish_date", "N/A"),
                }
                simplified_projects.append(project_info)
            simplified["projects"] = simplified_projects

        # 2. 关键修复：保留详细项目内容，但智能截断
        if "detailed_projects" in simplified and simplified["detailed_projects"]:
            detailed_projects = []
            for detail in simplified["detailed_projects"][:3]:  # 最多3个详细项目
                # 保留完整的详细信息，但截断过长的描述
                detailed_info = detail.copy()
                if "description" in detailed_info and len(detailed_info["description"]) > 2000:
                    detailed_info["description"] = detailed_info["description"][:2000] + "..."
                detailed_projects.append(detailed_info)
            simplified["detailed_projects"] = detailed_projects

        # 3. 移除大型完整列表
        simplified.pop("all_brands", None)
        simplified.pop("all_agencies", None)

        # 4. 截断排行榜，放宽到20个
        if "top_brands" in simplified and simplified["top_brands"]:
            simplified["top_brands"] = simplified["top_brands"][:20] 
        if "top_agencies" in simplified and simplified["top_agencies"]:
            simplified["top_agencies"] = simplified["top_agencies"][:20]

        return simplified

    def _is_empty_result(self, results: Dict[str, Any]) -> bool:
        """检查查询结果是否为空"""
        query_type = results.get("query_type", "")

        # 根据不同查询类型判断
        if query_type == "count":
            # count类型只看total_count
            return results.get("total_count", 0) == 0

        elif query_type == "list_brands":
            # 品牌列表看total_brands
            return results.get("total_brands", 0) == 0

        elif query_type == "list_agencies":
            # 代理商列表看total_agencies
            return results.get("total_agencies", 0) == 0

        elif query_type in ["search", "filter"]:
            # 搜索类看total_found
            return results.get("total_found", 0) == 0

        elif query_type == "statistics":
            # 统计类看total_count
            return results.get("total_count", 0) == 0

        elif query_type == "aggregate":
            # 聚合类看total_records
            return results.get("total_records", 0) == 0

        # 默认情况：检查是否有任何数据
        has_count = (results.get("total_count", 0) > 0 or
                     results.get("total_found", 0) > 0 or
                     results.get("total_brands", 0) > 0 or
                     results.get("total_agencies", 0) > 0 or
                     results.get("total_records", 0) > 0)

        has_data = (results.get("projects") or
                    results.get("top_brands") or
                    results.get("top_agencies") or
                    results.get("all_brands") or
                    results.get("all_agencies"))

        return not (has_count or has_data)
    
    def _generate_pagination_info(self, results: Dict[str, Any]) -> str:
        """生成分页信息"""
        total_count = results.get("total_found", results.get("total_count", 0))
        returned_count = results.get("returned_count", 0)
        remaining_count = results.get("remaining_count", 0)
        
        if remaining_count > 0:
            return self.prompt_manager.get_pagination_response(
                total_count=total_count,
                returned_count=returned_count,
                project_details="",  # 空字符串，因为详情已在主回答中
                remaining_count=remaining_count
            )
        
        return ""
    
    def get_conversation_starters(self) -> List[str]:
        """获取对话开场建议"""
        return self.prompt_manager.get_conversation_starters()
    
    def reload_prompts(self):
        """重新加载提示词（支持热更新）"""
        self.prompt_manager.reload_prompts()
        print("提示词模板已重新加载")

def main():
    """测试智能AI助手"""
    try:
        assistant = SmartAIAssistant()
        
        if not assistant.ready:
            print("AI助手未准备就绪")
            return
        
        # 测试查询
        test_queries = [
            "数据库中有多少个品牌？",
            "华为做了哪些营销项目？", 
            "列出所有代理商"
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            print("=" * 50)
            
            response = assistant.process_query(query)
            print(response)
            print()
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    main()