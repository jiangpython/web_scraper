#!/usr/bin/env python3
"""
数据清理和标准化工具函数
用于清理和标准化爬取的项目数据
"""

import re
import html
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCleaner:
    """数据清理和标准化工具类"""
    
    def __init__(self):
        # 品牌名称标准化映射表
        self.brand_mapping = {
            '中国平安': ['平安', '中国平安', 'PING AN'],
            '蓝莓传媒': ['蓝莓传媒', 'BlueMedia'],
            '腾讯': ['腾讯', 'Tencent'],
            '阿里巴巴': ['阿里巴巴', '阿里', 'Alibaba'],
            '字节跳动': ['字节跳动', 'ByteDance', '抖音'],
            '小米': ['小米', 'Xiaomi', 'MI'],
        }
        
        # 营销类型关键词映射
        self.marketing_keywords = {
            '体育营销': ['体育', '运动', '赛事', '龙舟', '足球', '篮球', '马拉松', '奥运'],
            '节日营销': ['春节', '端午', '中秋', '国庆', '情人节', '母亲节', '父亲节'],
            '明星营销': ['明星', '代言', '明星代言', '名人', '网红', 'KOL'],
            '创意广告': ['创意', '广告', '病毒', '话题', 'TVC', '短片'],
            '数字营销': ['数字', '线上', '互动', 'H5', '小程序', 'APP'],
            '公益营销': ['公益', '慈善', '环保', '责任', '正能量'],
            '跨界合作': ['跨界', '联名', '合作', '联动', 'IP'],
            '品牌升级': ['品牌', '升级', '重塑', '形象', '定位'],
        }
        
        # 行业分类映射
        self.industry_mapping = {
            '金融保险': ['平安', '银行', '保险', '金融', '理财'],
            '互联网科技': ['腾讯', '阿里', '字节', '百度', '华为'],
            '汽车': ['汽车', '车', 'BMW', '奔驰', '奥迪', '丰田'],
            '快消品': ['可口可乐', '百事', '雀巢', '宝洁', '联合利华'],
            '服装时尚': ['耐克', '阿迪', '优衣库', 'ZARA', 'H&M'],
            '食品饮料': ['麦当劳', '肯德基', '星巴克', '茶颜悦色'],
        }

    def extract_brand_from_title(self, title: str) -> str:
        """从标题中提取标准化品牌名"""
        if not title:
            return ""
        
        # 匹配 "品牌名×" 或 "品牌名:" 格式
        patterns = [
            r'^([^×:：]+)×',  # 品牌名×
            r'^([^：:]+)[:：]',  # 品牌名: 或 品牌名：
            r'^([^｜|]+)[｜|]',  # 品牌名| 或 品牌名｜
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title.strip())
            if match:
                brand = match.group(1).strip()
                return self.standardize_brand_name(brand)
        
        # 如果没有匹配到格式，尝试从已知品牌列表中匹配
        title_upper = title.upper()
        for standard_brand, variations in self.brand_mapping.items():
            for variation in variations:
                if variation.upper() in title_upper:
                    return standard_brand
        
        return ""

    def standardize_brand_name(self, brand: str) -> str:
        """标准化品牌名称"""
        if not brand:
            return ""
        
        brand = brand.strip()
        brand_upper = brand.upper()
        
        # 查找标准品牌名
        for standard_brand, variations in self.brand_mapping.items():
            for variation in variations:
                if variation.upper() == brand_upper:
                    return standard_brand
        
        return brand

    def clean_html_tags(self, text: str) -> str:
        """清理HTML标签和特殊字符"""
        if not text:
            return ""
        
        # 解码HTML实体
        text = html.unescape(text)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除常见的HTML实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def standardize_date_format(self, date_str: str) -> str:
        """标准化日期格式为YYYY-MM-DD"""
        if not date_str:
            return ""
        
        date_str = date_str.strip()
        
        # 常见日期格式
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-1-26 或 2024-01-26
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2024年1月26日
            r'(\d{4})\.(\d{1,2})\.(\d{1,2})',  # 2024.1.26
            r'(\d{4})/(\d{1,2})/(\d{1,2})',   # 2024/1/26
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                year, month, day = match.groups()
                try:
                    # 验证日期有效性
                    datetime(int(year), int(month), int(day))
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue
        
        return ""

    def extract_keywords_from_description(self, description: str, title: str = "") -> List[str]:
        """从描述中提取营销类型关键词"""
        if not description and not title:
            return []
        
        # 确保输入是字符串类型
        description = str(description) if description and not isinstance(description, str) else (description or "")
        title = str(title) if title and not isinstance(title, str) else (title or "")
        
        text = (description + " " + title).lower()
        found_keywords = []
        
        for category, keywords in self.marketing_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    found_keywords.append(category)
                    break  # 每个类别只添加一次
        
        return found_keywords

    def classify_industry(self, brand: str, title: str = "", description: str = "") -> str:
        """根据品牌、标题、描述分类行业"""
        # 确保输入是字符串类型
        brand = str(brand) if brand and not isinstance(brand, str) else (brand or "")
        title = str(title) if title and not isinstance(title, str) else (title or "")
        description = str(description) if description and not isinstance(description, str) else (description or "")
        
        text = (brand + " " + title + " " + description).lower()
        
        for industry, keywords in self.industry_mapping.items():
            for keyword in keywords:
                if keyword in text:
                    return industry
        
        return "其他"

    def extract_campaign_type(self, description: str, title: str = "") -> str:
        """提取营销活动类型"""
        # 确保输入是字符串类型
        description = str(description) if description and not isinstance(description, str) else (description or "")
        title = str(title) if title and not isinstance(title, str) else (title or "")
        
        text = (description + " " + title).lower()
        
        # 按优先级检查
        type_patterns = [
            ('TVC广告', ['tvc', '电视广告', '视频广告', '广告片']),
            ('品牌片', ['品牌片', '企业宣传片', '形象片']),
            ('活动营销', ['活动', '事件', '赛事', '发布会']),
            ('社交传播', ['社交', '微博', '微信', '抖音', '小红书']),
            ('数字营销', ['h5', '小程序', 'app', '互动']),
            ('内容营销', ['内容', '软文', '故事', '情感']),
            ('跨界合作', ['跨界', '联名', '合作', 'ip']),
            ('公关传播', ['公关', 'pr', '媒体', '新闻']),
        ]
        
        for campaign_type, keywords in type_patterns:
            for keyword in keywords:
                if keyword in text:
                    return campaign_type
        
        return "品牌传播"

    def validate_data_quality(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据质量并返回质量报告"""
        quality_report = {
            'valid': True,
            'issues': [],
            'score': 100
        }
        
        required_fields = ['id', 'title', 'url']
        important_fields = ['brand', 'agency', 'description']
        
        # 检查必填字段
        for field in required_fields:
            if not project_data.get(field):
                quality_report['issues'].append(f"缺少必填字段: {field}")
                quality_report['score'] -= 30
                quality_report['valid'] = False
        
        # 检查重要字段
        for field in important_fields:
            if not project_data.get(field):
                quality_report['issues'].append(f"缺少重要字段: {field}")
                quality_report['score'] -= 10
        
        # 检查数据格式
        if project_data.get('publish_date'):
            if not re.match(r'\d{4}-\d{2}-\d{2}', project_data['publish_date']):
                quality_report['issues'].append("日期格式不正确")
                quality_report['score'] -= 5
        
        # 检查URL格式
        if project_data.get('url'):
            if not re.match(r'https?://', project_data['url']):
                quality_report['issues'].append("URL格式不正确")
                quality_report['score'] -= 5
        
        quality_report['score'] = max(0, quality_report['score'])
        return quality_report

    def clean_project_data(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理单个项目数据"""
        cleaned_data = project_data.copy()
        
        try:
            # 提取和标准化品牌名
            if 'title' in cleaned_data:
                brand = self.extract_brand_from_title(cleaned_data['title'])
                if brand:
                    cleaned_data['brand'] = brand
            
            # 清理agency字段
            if 'agency' in cleaned_data:
                cleaned_data['agency'] = self.clean_html_tags(cleaned_data['agency'])
            
            # 标准化日期
            if 'publish_date' in cleaned_data:
                cleaned_data['publish_date'] = self.standardize_date_format(cleaned_data['publish_date'])
            
            # 提取关键词
            description = cleaned_data.get('description', '')
            title = cleaned_data.get('title', '')
            keywords = self.extract_keywords_from_description(description, title)
            if keywords:
                cleaned_data['keywords'] = keywords
            
            # 分类行业
            brand = cleaned_data.get('brand', '')
            industry = self.classify_industry(brand, title, description)
            cleaned_data['industry'] = industry
            
            # 提取营销活动类型
            campaign_type = self.extract_campaign_type(description, title)
            cleaned_data['campaign_type'] = campaign_type
            
            # 分类营销类别
            if keywords:
                cleaned_data['category'] = keywords[0]  # 使用第一个关键词作为主分类
            else:
                cleaned_data['category'] = campaign_type
            
            # 数据质量检查
            quality_report = self.validate_data_quality(cleaned_data)
            cleaned_data['_quality_score'] = quality_report['score']
            
            logger.info(f"成功清理项目数据: {cleaned_data.get('id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"清理项目数据时出错: {e}")
            cleaned_data['_cleaning_error'] = str(e)
        
        return cleaned_data

    def clean_batch_data(self, batch_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量清理项目数据"""
        logger.info(f"开始批量清理 {len(batch_data)} 个项目")
        
        cleaned_batch = []
        for project in batch_data:
            cleaned_project = self.clean_project_data(project)
            cleaned_batch.append(cleaned_project)
        
        logger.info(f"批量清理完成，处理了 {len(cleaned_batch)} 个项目")
        return cleaned_batch

# 便捷函数
def clean_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：清理单个项目数据"""
    cleaner = DataCleaner()
    return cleaner.clean_project_data(project_data)

def clean_projects(projects_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数：批量清理项目数据"""
    cleaner = DataCleaner()
    return cleaner.clean_batch_data(projects_data)