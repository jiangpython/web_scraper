"""
Gemini API 客户端
处理自然语言查询解析和回答生成
"""

import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import google.generativeai as genai
from dataclasses import dataclass


@dataclass
class QueryIntent:
    """查询意图数据结构"""
    query_type: str  # search, compare, analyze, statistics
    entities: Dict[str, Any]  # 提取的实体信息
    filters: Dict[str, Any]  # 查询条件
    confidence: float  # 置信度
    raw_query: str  # 原始查询


class GeminiClient:
    """Gemini API 客户端"""
    
    def __init__(self, api_key: str = None):
        """
        初始化Gemini客户端
        
        Args:
            api_key: Gemini API密钥
        """
        # 从环境变量或参数获取API密钥
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("需要提供Gemini API密钥。请设置GEMINI_API_KEY环境变量或传入api_key参数")
        
        # 配置Gemini
        genai.configure(api_key=self.api_key)
        
        # 初始化模型
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 对话历史
        self.conversation_history = []
        
        print("✅ Gemini客户端初始化成功")
    
    def analyze_query(self, user_query: str, context: str = "") -> QueryIntent:
        """
        分析用户查询意图
        
        Args:
            user_query: 用户查询
            context: 上下文信息
            
        Returns:
            QueryIntent对象
        """
        # 构建分析提示词
        prompt = self._build_analysis_prompt(user_query, context)
        
        try:
            # 调用Gemini API
            response = self.model.generate_content(prompt)
            
            # 解析响应
            result = self._parse_analysis_result(response.text, user_query)
            
            return result
            
        except Exception as e:
            print(f"⚠️ 查询分析失败: {e}")
            
            # 返回默认意图
            return QueryIntent(
                query_type="search",
                entities={},
                filters={},
                confidence=0.5,
                raw_query=user_query
            )
    
    def generate_answer(self, query: str, search_results: List[Dict], 
                       query_info: Dict = None) -> str:
        """
        基于搜索结果生成自然语言回答
        
        Args:
            query: 用户查询
            search_results: 搜索结果
            query_info: 查询信息
            
        Returns:
            自然语言回答
        """
        # 构建回答提示词
        prompt = self._build_answer_prompt(query, search_results, query_info)
        
        try:
            # 调用Gemini API
            response = self.model.generate_content(prompt)
            
            # 添加到对话历史
            self.conversation_history.append({
                "query": query,
                "response": response.text,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "result_count": len(search_results)
            })
            
            return response.text
            
        except Exception as e:
            print(f"⚠️ 回答生成失败: {e}")
            
            # 返回默认回答
            if search_results:
                return f"找到了 {len(search_results)} 个相关项目。由于技术原因，无法提供详细分析，请查看具体项目信息。"
            else:
                return "很抱歉，没有找到相关的项目信息。请尝试使用其他关键词。"
    
    def _build_analysis_prompt(self, user_query: str, context: str = "") -> str:
        """构建查询分析提示词"""
        prompt = f"""
你是一个专业的项目数据查询分析助手。请分析用户的查询意图，并以JSON格式返回结构化结果。

用户查询: "{user_query}"
上下文: {context}

请分析并返回以下信息（JSON格式）：
{{
    "query_type": "查询类型 (search/compare/analyze/statistics)",
    "entities": {{
        "brand": "品牌名称（如果提到）",
        "agency": "代理商名称（如果提到）",
        "project_name": "项目名称（如果提到）",
        "industry": "行业（如果提到）",
        "keywords": ["关键词1", "关键词2"]
    }},
    "filters": {{
        "date_range": "时间范围（如果提到，格式：recent/2023-01/2023-01~2023-12）",
        "limit": "结果数量限制（如果提到，数字）"
    }},
    "confidence": "置信度 (0.0-1.0)"
}}

分析规则：
1. search: 寻找特定项目、品牌或关键词
2. compare: 对比两个或多个项目/品牌
3. analyze: 深度分析项目特点、趋势等
4. statistics: 统计分析，如数量、排行等

5. 提取所有可能的实体（品牌、代理商、关键词等）
6. 识别时间相关词汇："最近"=recent，"今年"=2024，"去年"=2023等
7. 数字词汇转换：一个=1，几个=5，很多=20等

只返回JSON，不要其他文字。
"""
        return prompt
    
    def _build_answer_prompt(self, query: str, search_results: List[Dict], 
                           query_info: Dict = None) -> str:
        """构建回答生成提示词"""
        
        # 限制搜索结果数量以避免prompt过长
        limited_results = search_results[:10] if len(search_results) > 10 else search_results
        
        # 构建项目信息摘要
        projects_summary = []
        for i, project in enumerate(limited_results, 1):
            summary = f"""
项目{i}:
- 标题: {project.get('title', '未知')}
- 品牌: {project.get('brand', '未知')}
- 代理商: {project.get('agency', '未知')}
- 发布时间: {project.get('publish_date', '未知')}
- 分类: {project.get('category', '未知')}
- URL: {project.get('url', '')}
"""
            projects_summary.append(summary)
        
        projects_text = "\n".join(projects_summary)
        
        prompt = f"""
你是一个专业的营销项目分析师。请基于搜索结果回答用户的问题。

用户问题: "{query}"
搜索结果数量: {len(search_results)}
查询信息: {json.dumps(query_info, ensure_ascii=False) if query_info else "无"}

项目详情:
{projects_text}

回答要求：
1. 用自然、专业的中文回答
2. 根据查询类型调整回答风格：
   - 搜索类: 列出相关项目，突出关键信息
   - 对比类: 对比分析项目特点和差异
   - 分析类: 深入分析趋势、特点、洞察
   - 统计类: 提供数据统计和排名
3. 如果结果很多，重点介绍前几个，并说明总数
4. 如果没有结果，提供搜索建议
5. 适当引用具体项目信息支撑观点
6. 保持回答简洁但信息丰富

请开始回答：
"""
        return prompt
    
    def _parse_analysis_result(self, response_text: str, user_query: str) -> QueryIntent:
        """解析Gemini的分析结果"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("无法找到JSON格式的回答")
            
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            return QueryIntent(
                query_type=result.get('query_type', 'search'),
                entities=result.get('entities', {}),
                filters=result.get('filters', {}),
                confidence=float(result.get('confidence', 0.5)),
                raw_query=user_query
            )
            
        except Exception as e:
            print(f"⚠️ 解析分析结果失败: {e}")
            print(f"原始回答: {response_text}")
            
            # 简单的关键词匹配作为备选
            return self._fallback_analysis(user_query)
    
    def _fallback_analysis(self, user_query: str) -> QueryIntent:
        """备选的查询分析方法（基于关键词匹配）"""
        query_lower = user_query.lower()
        
        # 查询类型判断
        if any(word in query_lower for word in ['对比', '比较', 'vs', '和', '与']):
            query_type = 'compare'
        elif any(word in query_lower for word in ['统计', '数量', '排行', '多少', '几个']):
            query_type = 'statistics'
        elif any(word in query_lower for word in ['分析', '趋势', '特点', '怎么样']):
            query_type = 'analyze'
        else:
            query_type = 'search'
        
        # 简单的实体提取
        entities = {}
        keywords = []
        
        # 品牌关键词
        brand_keywords = re.findall(r'品牌[\s：:]*([^，,。.！!？?]*)', query_lower)
        if brand_keywords:
            entities['brand'] = brand_keywords[0].strip()
        
        # 代理商关键词
        agency_keywords = re.findall(r'代理商[\s：:]*([^，,。.！!？?]*)', query_lower)
        if agency_keywords:
            entities['agency'] = agency_keywords[0].strip()
        
        # 通用关键词提取
        for word in query_lower.split():
            if len(word) > 1 and word not in ['的', '了', '在', '有', '是', '和', '与']:
                keywords.append(word)
        
        entities['keywords'] = keywords[:5]  # 限制关键词数量
        
        # 时间过滤
        filters = {}
        if any(word in query_lower for word in ['最近', '近期']):
            filters['date_range'] = 'recent'
        elif '今年' in query_lower:
            filters['date_range'] = '2024'
        elif '去年' in query_lower:
            filters['date_range'] = '2023'
        
        return QueryIntent(
            query_type=query_type,
            entities=entities,
            filters=filters,
            confidence=0.6,
            raw_query=user_query
        )
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history[-limit:] if limit else self.conversation_history
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("✅ 对话历史已清空")
    
    def test_connection(self) -> bool:
        """测试Gemini API连接"""
        try:
            response = self.model.generate_content("你好，请回复'连接成功'")
            return "连接" in response.text or "成功" in response.text
        except Exception as e:
            print(f"❌ Gemini API连接测试失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试Gemini客户端...")
    
    # 注意：需要设置GEMINI_API_KEY环境变量
    try:
        client = GeminiClient()
        
        # 测试连接
        if client.test_connection():
            print("✅ API连接测试通过")
        else:
            print("❌ API连接测试失败")
            exit(1)
        
        # 测试查询分析
        test_queries = [
            "帮我找一些可口可乐的营销项目",
            "最近有哪些创意广告？",
            "对比一下宝马和奔驰的营销策略",
            "统计一下各个品牌的项目数量"
        ]
        
        for query in test_queries:
            print(f"\n🔍 测试查询: '{query}'")
            intent = client.analyze_query(query)
            print(f"查询类型: {intent.query_type}")
            print(f"实体: {intent.entities}")
            print(f"过滤条件: {intent.filters}")
            print(f"置信度: {intent.confidence}")
        
        print("\n✅ Gemini客户端测试完成")
        
    except ValueError as e:
        print(f"❌ 初始化失败: {e}")
        print("💡 请设置GEMINI_API_KEY环境变量或传入API密钥")
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")