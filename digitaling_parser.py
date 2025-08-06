"""
数英网页面解析器
针对数英网页面结构优化的解析器
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
                    driver.find_elements(By.CSS_SELECTOR, 'h1'),
                    driver.find_elements(By.CSS_SELECTOR, '.project-title'),
                    driver.find_elements(By.CSS_SELECTOR, '[class*="content"]'),
                    driver.find_elements(By.CSS_SELECTOR, '.work-detail')
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


class DigitalingParser:
    """数英网页面解析器"""
    
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
            time.sleep(random.uniform(2, 4))
            
            # 验证页面有效性
            if not self.validator.is_valid_project_page(self.driver):
                print(f"✗ 无效页面: {url}")
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
                'description': self._extract_description(),
                'images': self._extract_images(),
                'stats': self._extract_stats(),
                'creators': self._extract_creators(),
                'tags': self._extract_tags(),
                'category': self._extract_category()
            }
            
            # 验证必要字段
            if not project_data['title']:
                print(f"✗ 无法提取标题: {url}")
                return None
            
            print(f"✓ 解析成功: {project_data['title'][:50]}...")
            return project_data
            
        except Exception as e:
            print(f"✗ 解析失败 {url}: {e}")
            return None
    
    def _extract_project_id(self, url: str) -> str:
        """提取项目ID"""
        match = re.search(r'/projects/(\d+)\.html', url)
        return match.group(1) if match else "unknown"
    
    def _extract_title(self) -> str:
        """提取项目标题"""
        # 数英网标题选择器（按优先级排序）
        selectors = [
            'h1.work-title',          # 主要标题选择器
            'h1[class*="title"]',     # 包含title的h1
            '.work-detail h1',        # 作品详情区域的标题
            '.project-title',         # 项目标题类
            'h1',                     # 通用h1标签
            '.work-header h1',        # 作品头部标题
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
        # 数英网品牌信息选择器
        selectors = [
            '.work-client-name',      # 客户名称
            '.work-info .client',     # 作品信息中的客户
            '[class*="brand"] a',     # 品牌链接
            '.work-brand',            # 作品品牌
            'span:contains("品牌：") + span',  # 品牌标签后的内容
            'span:contains("客户：") + span',  # 客户标签后的内容
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # 处理包含文本的选择器
                    elements = self.driver.find_elements(By.XPATH, 
                        f"//span[contains(text(),'品牌：')]/following-sibling::span | "
                        f"//span[contains(text(),'客户：')]/following-sibling::span"
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
                r'品牌[：:]\s*([^<>\n\r]{2,50})',
                r'客户[：:]\s*([^<>\n\r]{2,50})',
                r'Brand[：:]\s*([^<>\n\r]{2,50})',
                r'Client[：:]\s*([^<>\n\r]{2,50})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source, re.I)
                if match:
                    brand = match.group(1).strip()
                    if brand and not self._is_noise_text(brand):
                        return brand
        except:
            pass
        
        return ""
    
    def _extract_agency(self) -> str:
        """提取代理商信息"""
        # 数英网代理商选择器
        selectors = [
            '.work-agency-name',      # 代理商名称
            '.work-info .agency',     # 作品信息中的代理商
            'a[href*="/company/"]',   # 公司链接
            '.work-company',          # 作品公司
            'span:contains("代理商：") + span',
            'span:contains("制作公司：") + span',
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        f"//span[contains(text(),'代理商：')]/following-sibling::span | "
                        f"//span[contains(text(),'制作公司：')]/following-sibling::span"
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
                r'代理商[：:]\s*([^<>\n\r]{2,50})',
                r'制作公司[：:]\s*([^<>\n\r]{2,50})',
                r'Agency[：:]\s*([^<>\n\r]{2,50})',
                r'Production[：:]\s*([^<>\n\r]{2,50})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source, re.I)
                if match:
                    agency = match.group(1).strip()
                    if agency and not self._is_noise_text(agency):
                        return agency
        except:
            pass
        
        return ""
    
    def _extract_publish_date(self) -> str:
        """提取发布日期"""
        # 数英网日期选择器
        selectors = [
            '.work-time',             # 作品时间
            '.work-date',             # 作品日期
            '.publish-time',          # 发布时间
            'time[datetime]',         # HTML5时间标签
            '[class*="date"]',        # 包含date的类
            'span:contains("发布时间：") + span',
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        "//span[contains(text(),'发布时间：')]/following-sibling::span"
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
                            return date_str
            except:
                continue
        
        # 从页面源码中提取日期
        try:
            page_source = self.driver.page_source
            date_patterns = [
                r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
                r'datetime="([^"]+)"',
                r'发布时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)'
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
    
    def _extract_description(self) -> str:
        """提取项目描述"""
        # 数英网描述选择器（按优先级排序）
        selectors = [
            '.work-content',          # 作品内容
            '.work-description',      # 作品描述
            '.project-content',       # 项目内容
            '.work-detail .content',  # 详情内容
            '.work-text',             # 作品文本
            '[class*="content"] p',   # 内容区域的段落
        ]
        
        description_parts = []
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    
                    # 过滤条件
                    if (text and 
                        len(text) > 20 and 
                        len(text) < 3000 and 
                        not self._is_noise_text(text)):
                        
                        # 检查是否包含项目相关关键词
                        content_keywords = [
                            '项目', '品牌', '营销', '创意', '活动', '广告',
                            '设计', '传播', '推广', '策略', '概念', '理念'
                        ]
                        
                        if any(keyword in text for keyword in content_keywords):
                            description_parts.append(text)
                            break  # 找到第一个匹配的就停止
            except:
                continue
        
        # 合并和清理描述
        if description_parts:
            full_description = ' '.join(description_parts)
            # 清理HTML标签和多余空白
            full_description = re.sub(r'<[^>]+>', '', full_description)
            full_description = re.sub(r'\s+', ' ', full_description).strip()
            
            # 限制长度
            if len(full_description) > 2000:
                full_description = full_description[:2000] + "..."
            
            return full_description
        
        return ""
    
    def _extract_images(self) -> List[str]:
        """提取项目图片"""
        images = []
        
        # 数英网图片选择器
        selectors = [
            '.work-content img',      # 作品内容中的图片
            '.work-images img',       # 作品图片区域
            '.project-images img',    # 项目图片
            '.work-gallery img',      # 作品画廊
            'img[src*="digitaling"]', # 数英网域名图片
        ]
        
        for selector in selectors:
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
        
        # 去重并限制数量
        unique_images = list(dict.fromkeys(images))  # 保持顺序的去重
        return unique_images[:15]  # 限制最多15张图片
    
    def _extract_stats(self) -> Dict:
        """提取统计信息"""
        stats = {}
        
        # 点赞数选择器
        like_selectors = [
            '.like-count',
            '.vote-count',
            '[class*="like"] .count',
            '[class*="vote"] .count',
            'span:contains("赞") + span'
        ]
        
        for selector in like_selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        "//span[contains(text(),'赞')]/following-sibling::span"
                    )
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    if text and text.replace(',', '').isdigit():
                        stats['likes'] = int(text.replace(',', ''))
                        break
            except:
                continue
        
        # 评论数选择器
        comment_selectors = [
            '.comment-count',
            '[class*="comment"] .count',
            'span:contains("评论") + span'
        ]
        
        for selector in comment_selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        "//span[contains(text(),'评论')]/following-sibling::span"
                    )
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    if text and text.replace(',', '').isdigit():
                        stats['comments'] = int(text.replace(',', ''))
                        break
            except:
                continue
        
        return stats
    
    def _extract_creators(self) -> List[str]:
        """提取创作人员"""
        creators = []
        
        # 创作人员选择器
        selectors = [
            '.work-creators',         # 作品创作者
            '.work-team',            # 作品团队
            '.creators-list',        # 创作者列表
            'span:contains("创作人员：") + span',
            'span:contains("制作团队：") + span',
        ]
        
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    elements = self.driver.find_elements(By.XPATH, 
                        f"//span[contains(text(),'创作人员：')]/following-sibling::span | "
                        f"//span[contains(text(),'制作团队：')]/following-sibling::span"
                    )
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) < 200:
                        # 分割多个创作者
                        names = re.split(r'[,，、\n]', text)
                        for name in names:
                            name = name.strip()
                            if name and len(name) < 30 and not self._is_noise_text(name):
                                creators.append(name)
            except:
                continue
        
        # 去重
        return list(dict.fromkeys(creators))  # 保持顺序的去重
    
    def _extract_tags(self) -> List[str]:
        """提取标签"""
        tags = []
        
        # 标签选择器
        selectors = [
            '.work-tags a',          # 作品标签链接
            '.project-tags a',       # 项目标签链接
            'a[href*="/tag/"]',      # 标签链接
            '.tags .tag',            # 标签区域
            '[class*="label"]',      # 标签类
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) < 30 and not self._is_noise_text(text):
                        tags.append(text)
            except:
                continue
        
        # 去重
        return list(dict.fromkeys(tags))
    
    def _extract_category(self) -> str:
        """提取项目类别"""
        # 类别选择器
        selectors = [
            '.work-category',        # 作品类别
            '.project-category',     # 项目类别
            '.category-name',        # 类别名称
            'a[href*="/category/"]', # 类别链接
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) < 50 and not self._is_noise_text(text):
                    return text
            except NoSuchElementException:
                continue
        
        return ""
    
    def _is_noise_text(self, text: str) -> bool:
        """检查是否为噪音文本"""
        noise_patterns = [
            r'^\s*$',                # 空白
            r'^[\d\s,，.。]+$',       # 纯数字和标点
            r'^(登录|注册|首页|返回|更多|查看|点击)$',  # 导航词汇
            r'^(Copyright|版权|©)',   # 版权信息
            r'javascript:',          # JS代码
            r'^https?://',           # URL
            r'^\d{4}-\d{2}-\d{2}$',  # 纯日期
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text, re.I):
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
                   'upload' in url_lower)
        
        # 检查域名（优先数英网图片）
        trusted_domains = ['digitaling.com', 'oss.digitaling.com']
        is_trusted = any(domain in url for domain in trusted_domains)
        
        return is_image and is_trusted