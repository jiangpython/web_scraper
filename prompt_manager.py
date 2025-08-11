#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理器 - 加载和管理AI提示词模板
支持模板变量替换和动态提示词生成
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

class PromptManager:
    """提示词管理器"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self.prompts_file = os.path.join(prompts_dir, "simple_prompts.json")
        self.prompts_data = {}
        
        # 确保目录存在
        os.makedirs(prompts_dir, exist_ok=True)
        
        # 加载提示词模板
        self._load_prompts()
    
    def _load_prompts(self):
        """加载提示词模板文件"""
        if not os.path.exists(self.prompts_file):
            print(f"警告: 提示词文件不存在: {self.prompts_file}")
            return
        
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                self.prompts_data = json.load(f)
            
            version = self.prompts_data.get("version", "未知")
            print(f"成功加载提示词模板 v{version}")
            
        except Exception as e:
            print(f"加载提示词文件失败: {e}")
            self.prompts_data = {}
    
    def get_query_analysis_prompt(self, user_query: str, chat_history: str = "") -> str:
        """获取查询分析提示词"""
        template = self.prompts_data.get("data_schema_prompt", "")
        
        if not template:
            # 备用简化版本
            return f"你是数据查询助手。用户问题: {user_query}\n请返回JSON格式的查询指令。"
        
        return template.format(user_query=user_query, chat_history=chat_history or "无")
    
    def get_answer_generation_prompt(self, original_question: str, query_results: Any, chat_history: str = "") -> str:
        """获取答案生成提示词"""
        template = self.prompts_data.get("answer_generation_prompt", "")
        
        if not template:
            # 备用简化版本
            return f"用户问题: {original_question}\n查询结果: {query_results}\n请基于查询结果回答用户问题。"
        
        # 将查询结果转换为字符串
        results_str = self._format_query_results(query_results)
        
        return template.format(
            original_question=original_question,
            query_results=results_str,
            chat_history=chat_history or "无"
        )
    
    def get_pagination_response(self, total_count: int, returned_count: int, 
                              project_details: str, remaining_count: int) -> str:
        """获取分页响应模板"""
        template = self.prompts_data.get("pagination_prompt", "")
        
        if not template:
            return f"找到{total_count}个项目，显示前{returned_count}个，还有{remaining_count}个可查看。"
        
        # 生成分页建议
        if remaining_count <= 5:
            suggestion = "您可以要求查看剩余的所有项目。"
        elif remaining_count <= 20:
            suggestion = "您可以要求查看接下来的10个项目，或按特定条件筛选。"
        else:
            suggestion = "建议您提供更具体的筛选条件，以便找到最相关的项目。"
        
        return template.format(
            total_count=total_count,
            returned_count=returned_count,
            project_details=project_details,
            remaining_count=remaining_count,
            pagination_suggestion=suggestion
        )
    
    def get_error_message(self, error_type: str, **kwargs) -> str:
        """获取错误提示消息"""
        template = self.prompts_data.get(error_type, "")
        
        if template:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                print(f"错误模板变量缺失: {e}")
                return template
        else:
            return "系统遇到未知错误，请稍后重试。"
    
    def get_conversation_starters(self) -> List[str]:
        """获取对话开场建议"""
        return self.prompts_data.get("conversation_starters", [
            "您可以问我关于营销项目的问题",
            "比如：品牌分析、项目统计、代理商查询等"
        ])
    
    def get_query_examples(self) -> Dict[str, Any]:
        """获取查询示例"""
        return self.prompts_data.get("query_examples", {})
    
    def _format_query_results(self, results: Any) -> str:
        """格式化查询结果为字符串"""
        if isinstance(results, dict):
            return json.dumps(results, ensure_ascii=False, indent=2)
        elif isinstance(results, list):
            if len(results) > 10:
                # 如果结果太多，只显示前10个
                truncated = results[:10]
                return json.dumps(truncated, ensure_ascii=False, indent=2) + f"\n... 还有 {len(results)-10} 个结果未显示"
            else:
                return json.dumps(results, ensure_ascii=False, indent=2)
        else:
            return str(results)
    
    def validate_prompts(self) -> Dict[str, bool]:
        """验证提示词模板的完整性"""
        required_prompts = [
            "data_schema_prompt",
            "answer_generation_prompt", 
            "pagination_prompt",
            "error_handling_prompts"
        ]
        
        validation_results = {}
        
        for prompt_key in required_prompts:
            validation_results[prompt_key] = prompt_key in self.prompts_data
        
        return validation_results
    
    def reload_prompts(self):
        """重新加载提示词（用于热更新）"""
        print("重新加载提示词模板...")
        self._load_prompts()
    
    def get_prompt_info(self) -> Dict[str, Any]:
        """获取提示词信息"""
        return {
            "version": self.prompts_data.get("version", "未知"),
            "last_updated": self.prompts_data.get("last_updated", "未知"),
            "total_prompts": len(self.prompts_data),
            "available_prompts": list(self.prompts_data.keys()),
            "validation": self.validate_prompts()
        }

def main():
    """测试提示词管理器"""
    manager = PromptManager()
    
    # 显示提示词信息
    info = manager.get_prompt_info()
    print("提示词管理器信息:")
    print(f"  版本: {info['version']}")
    print(f"  更新时间: {info['last_updated']}")
    print(f"  可用模板: {len(info['available_prompts'])} 个")
    
    # 验证模板
    validation = info['validation']
    print(f"  模板验证:")
    for key, valid in validation.items():
        status = "OK" if valid else "FAIL"
        print(f"    {status} {key}")
    
    # 测试模板生成
    print(f"\n测试模板生成:")
    test_query = "华为有多少个营销项目？"
    prompt = manager.get_query_analysis_prompt(test_query)
    print(f"  查询分析提示词长度: {len(prompt)} 字符")
    
    # 测试错误消息
    error_msg = manager.get_error_message("no_results")
    print(f"  错误消息示例: {error_msg[:50]}...")

if __name__ == "__main__":
    main()