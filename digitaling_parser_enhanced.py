"""
增强版数英网页面解析器
完整提取项目信息，包括图文内容和项目信息区域
"""

import re
import time
import random
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class DigitalingPageValidator:
    """数英网页面验证器"""
    
    @staticmethod
    def is_valid_project_page(driver: webdriver.Chrome) -> bool:
        """验证是否为有效的项目详情页"""
        try:
            current_url = driver.current_url
            
            # 检查URL格式
            if not re.match(r'https?://www\.digitaling\.com/projects/\d+\.html', current_url):
                return False
            
            # 检查是否重定向到错误页面
            error_indicators = [
                '404' in current_url,
                'error' in current_url.lower(),
                'not-found' in current_url.lower()
            ]
            
            if any(error_indicators):
                return False
            
            # 检查页面标题
            page_title = driver.title.lower()
            title_error_indicators = [
                '404', 'not found', '页面不存在', '未找到页面',
                'error', '错误', '访问错误'
            ]
            
            if any(indicator in page_title for indicator in title_error_indicators):
                return False
            
            # 检查页面内容中的错误信息
            try:
                # 等待页面基本加载
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                
                # 检查是否存在项目标题或内容区域
                project_indicators = [
                    driver.find_elements(By.CSS_SELECTOR, '.article-title'),
                    driver.find_elements(By.CSS_SELECTOR, '.content'),
                    driver.find_elements(By.CSS_SELECTOR, 'h1'),
                    driver.find_elements(By.CSS_SELECTOR, '.project-info')
                ]
                
                # 如果找到任何项目相关元素，认为是有效页面
                if any(elements for elements in project_indicators):
                    return True
                
                # 检查页面源码中的明确错误信息
                page_source = driver.page_source
                explicit_errors = [
                    '您访问的页面不存在',
                    '页面未找到',
                    '404错误',
                    '页面不存在或已被删除',
                    'Page Not Found'
                ]
                
                if any(error in page_source for error in explicit_errors):
                    return False
                
            except TimeoutException:
                return False
            
            return True
            
        except Exception as e:
            print(f"页面验证出错: {e}")
            return False


class DigitalingEnhancedParser:
    """增强版数英网页面解析器"""
    
    def __init__(self, driver: webdriver.Chrome):
        """
        初始化解析器
        
        Args:
            driver: WebDriver实例
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.validator = DigitalingPageValidator()
    
    def parse_project_detail(self, url: str) -> Optional[Dict]:
        """
        解析项目详情页
        
        Args:
            url: 项目详情页URL
            
        Returns:
            项目信息字典或None
        """
        try:
            print(f"正在解析: {url}")
            
            # 访问页面
            self.driver.get(url)
            
            # 随机延时
            time.sleep(random.uniform(3, 5))
            
            # 验证页面有效性
            if not self.validator.is_valid_project_page(self.driver):
                print(f"无效页面: {url}")
                return None
            
            # 滚动页面确保内容加载
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # 提取项目信息
            project_data = {
                'id': self._extract_project_id(url),
                'url': url,
                'title': self._extract_title(),
                'brand': self._extract_brand(),
                'agency': self._extract_agency(),
                'publish_date': self._extract_publish_date(),
                'description': self._extract_complete_description(),
                'images': self._extract_images(),
                'project_info': self._extract_project_info_section()
            }
            
            # 验证必要字段
            if not project_data['title']:
                print(f"无法提取标题: {url}")
                return None
            
            print(f"解析成功: {project_data['title'][:50]}...")
            return project_data
            
        except Exception as e:
            print(f"解析失败 {url}: {e}")
            return None
    
    def _extract_project_id(self, url: str) -> str:
        """提取项目ID"""
        match = re.search(r'/projects/(\d+)\.html', url)
        return match.group(1) if match else "unknown"
    
    def _extract_title(self) -> str:
        """提取项目标题"""
        # 数英网项目标题选择器（按优先级排序）
        selectors = [
            '.article-title',          # 主要标题选择器
            'h1.title',               # 备用标题选择器
            'h1[class*="title"]',     # 包含title的h1
            '.project-title',         # 项目标题类
            'h1',                     # 通用h1标签
            '.content-title',         # 内容标题
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                if title and len(title) > 2:  # 确保标题有意义
                    return title
            except NoSuchElementException:
                continue
        
        # 从页面标题中提取
        try:
            page_title = self.driver.title
            if page_title and '|' in page_title:
                title = page_title.split('|')[0].strip()
                if title and len(title) > 2:
                    return title
        except:
            pass
        
        return ""
    
    def _extract_brand(self) -> str:
        """提取品牌信息"""
        # 优先从项目信息区域提取
        project_info = self._extract_project_info_section()
        if project_info.get('brand'):
            return project_info['brand']
        
        # 数英网品牌信息选择器
        selectors = [
            '.company-logo + span',   # Logo旁边的文字
            '.brand-name',            # 品牌名称
            '.client-name',           # 客户名称
            '.project-brand',         # 项目品牌
            '[class*="brand"] span',  # 包含brand的类
            '.info-item:contains("品牌") + .info-value',
            '.info-item:contains("广告主") + .info-value',
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # 使用XPath处理contains选择器
                    elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class,'info-item') and contains(text(),'品牌')]/following-sibling::div[contains(@class,'info-value')] | "
                        "//div[contains(@class,'info-item') and contains(text(),'广告主')]/following-sibling::div[contains(@class,'info-value')]"
                    )
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) < 100 and not self._is_noise_text(text):
                        return text
            except:
                continue
        
        # 从页面源码中用正则提取
        try:
            page_source = self.driver.page_source
            patterns = [
                r'品牌[：:\s]*<[^>]*>([^<]{2,50})<',
                r'广告主[：:\s]*<[^>]*>([^<]{2,50})<',
                r'客户[：:\s]*<[^>]*>([^<]{2,50})<',
                r'"brand"[：:\s]*"([^"]{2,50})"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.I)
                for match in matches:
                    if match and not self._is_noise_text(match):
                        return match.strip()
        except:
            pass
        
        return ""
    
    def _extract_agency(self) -> str:
        """提取代理商/营销机构信息"""
        # 优先从项目信息区域提取
        project_info = self._extract_project_info_section()
        if project_info.get('agency'):
            return project_info['agency']
        
        # 数英网代理商选择器
        selectors = [
            '.marketing-agency',      # 营销机构
            '.agency-name',           # 代理商名称
            '.production-company',    # 制作公司
            'a[href*="/company/"]',   # 公司链接
            '[class*="agency"] span', # 包含agency的类
            '.info-item:contains("营销机构") + .info-value',
            '.info-item:contains("代理商") + .info-value',
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class,'info-item') and contains(text(),'营销机构')]/following-sibling::div[contains(@class,'info-value')] | "
                        "//div[contains(@class,'info-item') and contains(text(),'代理商')]/following-sibling::div[contains(@class,'info-value')]"
                    )
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) < 100 and not self._is_noise_text(text):
                        # 过滤掉品牌信息（避免混淆）
                        if not any(keyword in text.lower() for keyword in ['品牌', 'brand']):
                            return text
            except:
                continue
        
        # 从页面源码中提取
        try:
            page_source = self.driver.page_source
            patterns = [
                r'营销机构[：:\s]*<[^>]*>([^<]{2,50})<',
                r'代理商[：:\s]*<[^>]*>([^<]{2,50})<',
                r'制作公司[：:\s]*<[^>]*>([^<]{2,50})<',
                r'"agency"[：:\s]*"([^"]{2,50})"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.I)
                for match in matches:
                    if match and not self._is_noise_text(match):
                        return match.strip()
        except:
            pass
        
        return ""
    
    def _extract_publish_date(self) -> str:
        """提取发布日期"""
        # 数英网日期选择器
        selectors = [
            '.publish-time',          # 发布时间
            '.article-time',          # 文章时间
            '.project-date',          # 项目日期
            'time[datetime]',         # HTML5时间标签
            '[class*="time"]',        # 包含time的类
            '.info-item:contains("发布时间") + .info-value',
            '.date-info'
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class,'info-item') and contains(text(),'发布时间')]/following-sibling::div[contains(@class,'info-value')]"
                    )
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    # 先尝试datetime属性
                    if element.tag_name == 'time':
                        datetime_attr = element.get_attribute('datetime')
                        if datetime_attr:
                            return datetime_attr[:10]  # 取日期部分
                    
                    # 从文本中提取日期
                    text = element.text.strip()
                    if text:
                        date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)', text)
                        if date_match:
                            date_str = date_match.group(1)
                            # 标准化日期格式
                            date_str = re.sub(r'[年月]', '-', date_str).replace('日', '')
                            return date_str[:10]  # 确保格式为YYYY-MM-DD
            except:
                continue
        
        # 从页面源码中提取日期
        try:
            page_source = self.driver.page_source
            date_patterns = [
                r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
                r'datetime="([^"]+)"',
                r'发布时间[：:\s]*["\']?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, page_source)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ""
                    if match and re.search(r'\d{4}', match):
                        # 标准化日期格式
                        date_str = re.sub(r'[年月]', '-', match).replace('日', '')
                        return date_str[:10]  # 取前10位
        except:
            pass
        
        return ""
    
    def _extract_complete_description(self) -> str:
        """提取完整的项目描述（图文混合内容）"""
        try:
            description_parts = []
            
            # 查找主要内容区域
            content_selectors = [
                '.article-content',
                '.project-content', 
                '.content',
                '.main-content',
                '.detail-content'
            ]
            
            content_container = None
            for selector in content_selectors:
                try:
                    content_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not content_container:
                # 如果没找到特定容器，使用body
                content_container = self.driver.find_element(By.TAG_NAME, 'body')
            
            # 提取所有段落文本
            paragraphs = content_container.find_elements(By.TAG_NAME, 'p')
            for p in paragraphs:
                text = p.text.strip()
                if text and len(text) > 10:  # 过滤太短的文本
                    # 检查是否是有意义的内容
                    if not self._is_noise_text(text) and self._is_content_text(text):
                        description_parts.append(text)
            
            # 如果段落内容不够，尝试提取其他文本元素
            if len(description_parts) < 2:
                other_selectors = ['div', 'span', 'section']
                for tag in other_selectors:
                    elements = content_container.find_elements(By.TAG_NAME, tag)
                    for elem in elements:
                        text = elem.text.strip()
                        if (text and 
                            len(text) > 20 and 
                            len(text) < 1000 and 
                            not self._is_noise_text(text) and 
                            self._is_content_text(text) and
                            text not in description_parts):
                            description_parts.append(text)
                            if len(description_parts) >= 5:  # 限制数量
                                break
            
            # 合并描述
            if description_parts:
                # 去重并保持顺序
                unique_parts = []
                seen = set()
                for part in description_parts:
                    if part not in seen:
                        unique_parts.append(part)
                        seen.add(part)
                
                full_description = '\n\n'.join(unique_parts)
                
                # 限制长度
                if len(full_description) > 3000:
                    full_description = full_description[:3000] + "..."
                
                return full_description
            
        except Exception as e:
            print(f"提取描述时出错: {e}")
        
        return ""
    
    def _extract_project_info_section(self) -> Dict[str, str]:
        """提取项目信息区域的结构化数据"""
        project_info = {}
        
        try:
            # 查找项目信息区域
            info_selectors = [
                '.project-info',
                '.article-info',
                '.work-info',
                '.info-section',
                '.project-details'
            ]
            
            info_container = None
            for selector in info_selectors:
                try:
                    info_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if info_container:
                # 提取信息项
                info_items = info_container.find_elements(By.CSS_SELECTOR, '.info-item, .info-row, .detail-item')
                
                for item in info_items:
                    try:
                        # 查找标签和值
                        label_elem = item.find_element(By.CSS_SELECTOR, '.info-label, .info-name, .label')
                        value_elem = item.find_element(By.CSS_SELECTOR, '.info-value, .info-content, .value')
                        
                        label = label_elem.text.strip().replace('：', '').replace(':', '')
                        value = value_elem.text.strip()
                        
                        if label and value:
                            # 标准化标签名称
                            if any(keyword in label for keyword in ['品牌', '广告主', '客户']):
                                project_info['brand'] = value
                            elif any(keyword in label for keyword in ['营销机构', '代理商', '制作公司']):
                                project_info['agency'] = value
                            elif any(keyword in label for keyword in ['发布时间', '时间', '日期']):
                                project_info['publish_date'] = value
                            elif any(keyword in label for keyword in ['行业', '分类', '类别']):
                                project_info['category'] = value
                            else:
                                # 其他信息也保存
                                project_info[label] = value
                    except NoSuchElementException:
                        continue
            
            # 如果没有找到结构化信息区域，尝试从页面文本中提取
            if not project_info:
                page_text = self.driver.page_source
                
                # 使用正则表达式提取关键信息
                patterns = {
                    'brand': [
                        r'品牌[：:\s]*([^\n\r<>]{2,50})',
                        r'广告主[：:\s]*([^\n\r<>]{2,50})',
                        r'客户[：:\s]*([^\n\r<>]{2,50})'
                    ],
                    'agency': [
                        r'营销机构[：:\s]*([^\n\r<>]{2,50})',
                        r'代理商[：:\s]*([^\n\r<>]{2,50})',
                        r'制作公司[：:\s]*([^\n\r<>]{2,50})'
                    ],
                    'category': [
                        r'行业[：:\s]*([^\n\r<>]{2,50})',
                        r'分类[：:\s]*([^\n\r<>]{2,50})',
                        r'类别[：:\s]*([^\n\r<>]{2,50})'
                    ]
                }
                
                for field, field_patterns in patterns.items():
                    for pattern in field_patterns:
                        match = re.search(pattern, page_text, re.I)
                        if match:
                            value = match.group(1).strip()
                            # 清理HTML标签
                            value = re.sub(r'<[^>]+>', '', value)
                            if value and not self._is_noise_text(value):
                                project_info[field] = value
                                break
            
        except Exception as e:
            print(f"提取项目信息区域时出错: {e}")
        
        return project_info
    
    def _extract_images(self) -> List[str]:
        """提取项目图片"""
        images = []
        
        try:
            # 查找内容区域中的图片
            content_selectors = [
                '.article-content img',
                '.project-content img', 
                '.content img',
                '.main-content img'
            ]
            
            for selector in content_selectors:
                try:
                    img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for img in img_elements:
                        try:
                            src = img.get_attribute('src')
                            if src and self._is_valid_image_url(src):
                                images.append(src)
                        except:
                            continue
                except:
                    continue
            
            # 如果内容区域没有图片，查找所有图片
            if not images:
                all_images = self.driver.find_elements(By.TAG_NAME, 'img')
                for img in all_images:
                    try:
                        src = img.get_attribute('src')
                        if src and self._is_valid_image_url(src):
                            images.append(src)
                    except:
                        continue
            
            # 去重并限制数量
            unique_images = list(dict.fromkeys(images))  # 保持顺序的去重
            return unique_images[:20]  # 增加图片数量限制
            
        except Exception as e:
            print(f"提取图片时出错: {e}")
        
        return []
    
    def _is_content_text(self, text: str) -> bool:
        """检查是否为有意义的内容文本"""
        # 内容相关的关键词
        content_keywords = [
            '项目', '品牌', '营销', '创意', '活动', '广告', '传播',
            '设计', '推广', '策略', '概念', '理念', '文案', '视觉',
            '用户', '消费者', '市场', '产品', '服务', '体验',
            '社交', '媒体', '平台', '内容', '故事', '情感'
        ]
        
        # 检查是否包含内容关键词
        return any(keyword in text for keyword in content_keywords)
    
    def _is_noise_text(self, text: str) -> bool:
        """检查是否为噪音文本"""
        noise_patterns = [
            r'^\s*$',                # 空白
            r'^[\d\s,，.。]+$',       # 纯数字和标点
            r'^(登录|注册|首页|返回|更多|查看|点击|分享|收藏|关注)$',  # 导航词汇
            r'^(Copyright|版权|©)',   # 版权信息
            r'javascript:',          # JS代码
            r'^https?://',           # URL
            r'^\d{4}-\d{2}-\d{2}$',  # 纯日期
            r'^(上一篇|下一篇|相关推荐|热门文章)$',  # 导航文本
            r'^(评论|点赞|转发|举报)$'  # 交互按钮
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text, re.I):
                return True
        
        # 检查长度
        if len(text.strip()) < 5:
            return True
        
        return False
    
    def _is_valid_image_url(self, url: str) -> bool:
        """验证图片URL是否有效"""
        if not url or url.startswith('data:'):
            return False
        
        # 检查是否为图片文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        url_lower = url.lower()
        
        # 检查文件扩展名或包含图片相关参数
        is_image = (any(ext in url_lower for ext in image_extensions) or 
                   'image' in url_lower or 
                   'img' in url_lower or
                   'upload' in url_lower or
                   'pic' in url_lower)
        
        # 检查域名（优先数英网图片）
        trusted_domains = ['digitaling.com', 'oss.digitaling.com', 'static.digitaling.com']
        is_trusted = any(domain in url for domain in trusted_domains)
        
        # 过滤掉小图标和logo
        is_small_icon = any(keyword in url_lower for keyword in ['icon', 'logo', 'avatar', 'thumb'])
        
        return is_image and is_trusted and not is_small_icon