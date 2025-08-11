"""
DeepSeek API 客户端
"""

import os
import json
import requests
from typing import List, Dict, Any

class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self, api_key: str = None, model_name: str = "DeepSeek-R1-Distill-Llama-70B"):
        """
        初始化DeepSeek客户端

        Args:
            api_key: DeepSeek API密钥
            model_name: 使用的模型名称
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("需要提供DeepSeek API密钥。请设置DEEPSEEK_API_KEY环境变量或传入api_key参数")

        self.api_url = "https://aiapi.999.com.cn/v1/chat/completions"
        self.model_name = model_name
        
        print(f"DeepSeek client initialized successfully (model={self.model_name})")

    def generate_response(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        """
        生成AI响应

        Args:
            prompt: 当前的用户提问
            history: 历史对话记录

        Returns:
            AI响应文本
        """
        headers = {
            'Accept': '*/*',
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        messages = []
        if history:
            for item in history:
                messages.append({"role": item["role"], "content": item["content"]})
        
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model_name,
            "stream": False,
            "messages": messages
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            response_json = response.json()
            
            if "choices" in response_json and len(response_json["choices"]) > 0:
                content = response_json["choices"][0].get("message", {}).get("content", "")
                return content
            else:
                return f"API响应格式不正确: {response.text}"

        except requests.exceptions.RequestException as e:
            print(f"❌ DeepSeek API请求失败: {e}")
            return f"很抱歉，请求DeepSeek服务时发生网络错误: {e}"
        except Exception as e:
            print(f"❌ DeepSeek响应处理失败: {e}")
            return "很抱歉，处理DeepSeek响应时发生未知错误。"

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response_text = self.generate_response("你好，请回复'连接成功'")
            return "连接成功" in response_text
        except Exception as e:
            print(f"❌ DeepSeek API连接测试失败: {e}")
            return False
