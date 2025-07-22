from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import pandas as pd
from datetime import datetime
import re
import os


class DigitalingSeleniumScraper:
    def __init__(self, headless=False, driver_path=None):
        """
        初始化Selenium WebDriver

        Args:
            headless: 是否使用无头模式
            driver_path: ChromeDriver的路径，如果为None则自动查找
        """
        # Chrome选项
        self.options = webdriver.ChromeOptions()
        if headless:
            self.options.add_argument('--headless')

        # 反反爬虫设置
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 其他有用的选项
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')

        self.driver_path = driver_path
        self.driver = None
        self.wait = None

    def find_chrome_driver(self):
        """查找ChromeDriver的路径"""
        # 可能的ChromeDriver文件名
        possible_names = ['chromedriver.exe', 'chromedriver']

        # 1. 首先检查是否指定了路径
        if self.driver_path and os.path.exists(self.driver_path):
            return self.driver_path

        # 2. 在当前目录查找
        for name in possible_names:
            if os.path.exists(name):
                print(f"✓ 在当前目录找到ChromeDriver: {name}")
                return os.path.abspath(name)

        # 3. 在项目根目录的各个可能位置查找
        possible_dirs = [
            '.',  # 当前目录
            './drivers',  # drivers子目录
            './chromedriver',  # chromedriver子目录
            '../',  # 上级目录
        ]

        for dir_path in possible_dirs:
            for name in possible_names:
                full_path = os.path.join(dir_path, name)
                if os.path.exists(full_path):
                    print(f"✓ 找到ChromeDriver: {full_path}")
                    return os.path.abspath(full_path)

        # 4. 如果都没找到，返回None（将尝试使用系统PATH中的）
        return None

    def start_driver(self):
        """启动驱动"""
        try:
            # 查找ChromeDriver
            driver_path = self.find_chrome_driver()

            if driver_path:
                # 使用找到的ChromeDriver路径
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=self.options)
                print(f"✓ 使用ChromeDriver: {driver_path}")
            else:
                # 尝试使用系统PATH中的ChromeDriver
                print("⚠ 未在项目目录找到ChromeDriver，尝试使用系统PATH中的...")
                self.driver = webdriver.Chrome(options=self.options)

            self.wait = WebDriverWait(self.driver, 10)

            # 执行一些JavaScript来隐藏webdriver特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("✓ Chrome驱动启动成功")

        except Exception as e:
            print(f"✗ 启动Chrome驱动失败: {e}")
            print("\n请确保：")
            print("1. 已下载正确版本的ChromeDriver")
            print("2. ChromeDriver文件名为 'chromedriver.exe'（Windows）或 'chromedriver'（Mac/Linux）")
            print("3. ChromeDriver放在以下位置之一：")
            print("   - 当前项目目录")
            print("   - ./drivers/ 子目录")
            print("   - ./chromedriver/ 子目录")
            raise

    def close_driver(self):
        """关闭驱动"""
        if self.driver:
            self.driver.quit()
            print("✓ Chrome驱动已关闭")

    def extract_project_info(self, element):
        """从元素中提取项目信息"""
        project = {}

        try:
            # 查找项目链接
            link_elem = element.find_element(By.CSS_SELECTOR, 'a[href*="/projects/"][href$=".html"]')
            project['link'] = link_elem.get_attribute('href')

            # 获取标题
            project['title'] = link_elem.text.strip() or link_elem.get_attribute('title') or ''

            # 如果标题为空，尝试其他方式
            if not project['title']:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, 'h3, h4, h5')
                    project['title'] = title_elem.text.strip()
                except:
                    pass

            # 获取元素的所有文本
            element_text = element.text

            # 提取品牌信息
            brand_match = re.search(r'Brand[:\s]*([^\n]+?)(?:\s*By[:\s]*([^\n]+?))?(?:\n|$)', element_text, re.I)
            if brand_match:
                project['brand'] = brand_match.group(1).strip()
                if brand_match.group(2):
                    project['agency'] = brand_match.group(2).strip().split()[0]  # 取第一个词作为代理商

            # 提取日期
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', element_text)
            if date_match:
                project['publish_date'] = date_match.group(1).replace('/', '-')

            # 提取图片
            try:
                img_elem = element.find_element(By.TAG_NAME, 'img')
                img_url = img_elem.get_attribute('src')
                if img_url and not img_url.startswith('data:'):
                    project['image_url'] = img_url
            except:
                pass

            # 提取点赞数或其他互动数据
            try:
                like_elem = element.find_element(By.CSS_SELECTOR, '[class*="like"], [class*="vote"], [class*="count"]')
                project['likes'] = like_elem.text.strip()
            except:
                pass

        except Exception as e:
            print(f"提取项目信息时出错: {e}")
            return None

        return project if project.get('title') and project.get('link') else None

    def wait_for_projects_load(self):
        """等待项目列表加载"""
        try:
            # 等待页面加载完成
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(2)  # 额外等待，确保动态内容加载

            # 尝试多种可能的选择器
            selectors = [
                'a[href*="/projects/"][href$=".html"]',
                'li.work-item',
                'div.project-item',
                'article.project',
                '[class*="project"]',
                '[class*="work"]'
            ]

            for selector in selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✓ 找到项目元素，使用选择器: {selector}")
                    return True

            return False
        except:
            return False

    def scrape_current_page(self):
        """抓取当前页面的项目"""
        projects = []

        # 等待项目加载
        if not self.wait_for_projects_load():
            print("✗ 未找到项目元素")
            return projects

        # 查找所有包含项目链接的元素
        project_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/projects/"][href$=".html"]')

        # 获取每个链接的父容器作为项目元素
        processed_containers = set()

        for link in project_links:
            try:
                # 向上查找合适的容器元素
                container = link
                for _ in range(5):  # 最多向上查找5层
                    parent = container.find_element(By.XPATH, '..')
                    if parent.tag_name in ['li', 'article', 'div']:
                        # 检查是否已处理过这个容器
                        container_id = id(parent)
                        if container_id not in processed_containers:
                            processed_containers.add(container_id)
                            project = self.extract_project_info(parent)
                            if project and self.is_valid_project(project):
                                projects.append(project)
                            break
                    container = parent
            except:
                continue

        return projects

    def is_valid_project(self, project):
        """验证项目是否有效"""
        # 检查必要字段
        if not project.get('title') or not project.get('link'):
            return False

        # 过滤无效标题
        invalid_titles = ['全部', '每周项目精选', '查看更多', '加载更多', '项目']
        if project['title'] in invalid_titles:
            return False

        # 确保链接格式正确
        if not re.search(r'/projects/\d+\.html', project['link']):
            return False

        return True

    def click_next_page(self):
        """点击下一页"""
        try:
            # 尝试多种下一页按钮的选择器
            next_selectors = [
                'a:contains("下一页")',
                'a.next',
                '[class*="next"]',
                'a[rel="next"]'
            ]

            # 使用JavaScript查找包含"下一页"文本的链接
            next_link = self.driver.execute_script("""
                var links = document.getElementsByTagName('a');
                for (var i = 0; i < links.length; i++) {
                    if (links[i].textContent.includes('下一页')) {
                        return links[i];
                    }
                }
                return null;
            """)

            if next_link:
                # 滚动到元素
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_link)
                time.sleep(0.5)

                # 检查是否可点击
                if next_link.get_attribute('class') and 'disabled' in next_link.get_attribute('class'):
                    return False

                # 点击
                self.driver.execute_script("arguments[0].click();", next_link)
                time.sleep(2)  # 等待页面加载
                return True

        except Exception as e:
            print(f"点击下一页时出错: {e}")

        return False

    def get_company_name_from_url(self, url):
        """从URL中提取公司名称"""
        # 尝试从页面获取公司名称
        try:
            # 访问页面
            self.driver.get(url)
            time.sleep(2)

            # 尝试多种选择器查找公司名
            selectors = [
                'h1.company-name',
                '.company-title',
                '[class*="company"] h1',
                'title'
            ]

            for selector in selectors:
                try:
                    if selector == 'title':
                        title = self.driver.title
                        # 从标题中提取公司名
                        if '|' in title:
                            company_name = title.split('|')[0].strip()
                        elif '-' in title:
                            company_name = title.split('-')[0].strip()
                        else:
                            company_name = title.strip()

                        if company_name and len(company_name) < 50:
                            return company_name
                    else:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        company_name = elem.text.strip()
                        if company_name:
                            return company_name
                except:
                    continue

        except:
            pass

        # 如果无法从页面获取，从URL提取
        match = re.search(r'/company/projects/(\d+)', url)
        if match:
            return f"公司_{match.group(1)}"

        return "未知公司"

    def scrape_all_projects(self, start_url, max_pages=16):
        """抓取所有项目"""
        all_projects = []

        try:
            # 获取公司名称
            company_name = self.get_company_name_from_url(start_url)
            print(f"\n正在抓取: {company_name}")

            # 访问起始页面
            print(f"访问页面: {start_url}")
            self.driver.get(start_url)
            time.sleep(3)  # 等待页面完全加载

            # 检查是否被重定向
            current_url = self.driver.current_url
            if 'dindex' in current_url:
                print("✗ 被重定向到首页，尝试重新导航...")
                self.driver.get(start_url)
                time.sleep(3)

            # 抓取多页数据
            empty_page_count = 0
            for page in range(1, max_pages + 1):
                print(f"\n========== 第 {page} 页 ==========")

                # 抓取当前页
                projects = self.scrape_current_page()
                if projects:
                    all_projects.extend(projects)
                    print(f"✓ 获取到 {len(projects)} 个项目")
                    empty_page_count = 0  # 重置空页计数

                    # 显示部分项目
                    for p in projects[:3]:
                        print(f"  - {p['title'][:40]}...")
                else:
                    print("✗ 当前页未找到项目")
                    empty_page_count += 1

                    # 如果连续2页没有数据，可能已经到达最后
                    if empty_page_count >= 2:
                        print("连续2页无数据，停止抓取")
                        break

                # 尝试进入下一页
                if page < max_pages:
                    if not self.click_next_page():
                        print("✗ 无法进入下一页，停止抓取")
                        break

        except Exception as e:
            print(f"\n抓取过程中出错: {e}")

        return all_projects, company_name

    def read_urls_from_file(self, filename='urls.txt'):
        """从文件读取URL列表"""
        urls = []

        if not os.path.exists(filename):
            print(f"✗ 未找到文件: {filename}")
            return urls

        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if line and not line.startswith('#'):
                    # 支持带页数的格式：URL,页数
                    if ',' in line:
                        url, pages = line.split(',', 1)
                        try:
                            pages = int(pages.strip())
                        except:
                            pages = 16
                        urls.append((url.strip(), pages))
                    else:
                        urls.append((line, 16))  # 默认16页

        print(f"✓ 从 {filename} 读取到 {len(urls)} 个URL")
        return urls

    def scrape_multiple_companies(self, urls_file='urls.txt'):
        """批量抓取多个公司的项目"""
        # 读取URL列表
        url_list = self.read_urls_from_file(urls_file)

        if not url_list:
            print("没有找到要抓取的URL")
            return

        # 启动驱动
        self.start_driver()

        all_company_data = {}

        try:
            # 抓取每个公司
            for i, (url, max_pages) in enumerate(url_list, 1):
                print(f"\n{'=' * 60}")
                print(f"正在处理第 {i}/{len(url_list)} 个公司")
                print(f"URL: {url}")
                print(f"最大页数: {max_pages}")
                print('=' * 60)

                # 抓取项目
                projects, company_name = self.scrape_all_projects(url, max_pages)

                # 去重
                unique_projects = []
                seen_links = set()
                for project in projects:
                    if project['link'] not in seen_links:
                        seen_links.add(project['link'])
                        unique_projects.append(project)

                # 保存数据
                if unique_projects:
                    all_company_data[company_name] = unique_projects
                    print(f"\n✓ {company_name}: 获取到 {len(unique_projects)} 个唯一项目")
                else:
                    print(f"\n✗ {company_name}: 未获取到项目")

                # 休息一下，避免请求过快
                if i < len(url_list):
                    print("\n等待5秒后继续...")
                    time.sleep(5)

        finally:
            self.close_driver()

        return all_company_data

    def save_to_excel_multiple_sheets(self, all_company_data, filename='digitaling_all_projects.xlsx'):
        """保存多个公司的数据到Excel的不同sheet"""
        if not all_company_data:
            print("没有数据可保存")
            return

        # 创建Excel写入器
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 创建汇总sheet
            summary_data = []

            for company_name, projects in all_company_data.items():
                # 创建DataFrame
                df = pd.DataFrame(projects)

                # 重新排列列的顺序
                column_order = ['title', 'link', 'brand', 'agency', 'publish_date', 'description', 'image_url', 'likes']
                existing_columns = [col for col in column_order if col in df.columns]
                other_columns = [col for col in df.columns if col not in column_order]
                df = df[existing_columns + other_columns]

                # 清理sheet名称（Excel sheet名称有限制）
                sheet_name = re.sub(r'[^\w\s-]', '', company_name)[:31]  # Excel sheet名最多31字符

                # 写入各公司的sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # 调整列宽
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass

                    adjusted_width = min(max(max_length + 2, 10), 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                # 收集汇总信息
                summary_data.append({
                    '公司名称': company_name,
                    '项目数量': len(df),
                    '品牌数量': df['brand'].nunique() if 'brand' in df.columns else 0,
                    '代理商数量': df['agency'].nunique() if 'agency' in df.columns else 0,
                    '最早发布时间': self.safe_date_min(df['publish_date']) if 'publish_date' in df.columns else '',
                    '最晚发布时间': self.safe_date_max(df['publish_date']) if 'publish_date' in df.columns else ''
                })

            # 创建汇总sheet
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='汇总', index=False)

            # 调整汇总sheet的列宽
            summary_sheet = writer.sheets['汇总']
            for column in summary_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                adjusted_width = min(max(max_length + 2, 10), 30)
                summary_sheet.column_dimensions[column_letter].width = adjusted_width

        print(f"\n✓ 已保存数据到 {filename}")
        print(f"  - 包含 {len(all_company_data)} 个公司的数据")
        print(f"  - 每个公司一个sheet，外加一个汇总sheet")

        # 保存JSON备份
        json_filename = filename.replace('.xlsx', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(all_company_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 已保存JSON备份到 {json_filename}")

    def safe_date_min(self, date_series):
        """安全地获取日期最小值"""
        try:
            # 过滤掉空值和无效日期
            valid_dates = pd.to_datetime(date_series, errors='coerce').dropna()
            if len(valid_dates) > 0:
                return valid_dates.min().strftime('%Y-%m-%d')
        except:
            pass
        return ''

    def safe_date_max(self, date_series):
        """安全地获取日期最大值"""
        try:
            # 过滤掉空值和无效日期
            valid_dates = pd.to_datetime(date_series, errors='coerce').dropna()
            if len(valid_dates) > 0:
                return valid_dates.max().strftime('%Y-%m-%d')
        except:
            pass
        return ''


# 使用示例
if __name__ == "__main__":
    # 创建示例URL文件
    example_urls = """# 数英网公司项目页面列表
# 格式：URL,最大页数（可选，默认16页）
# 以#开头的行会被忽略

https://www.digitaling.com/company/projects/11001,16
https://www.digitaling.com/company/projects/10788,10
https://www.digitaling.com/company/projects/10234
"""

    # 如果urls.txt不存在，创建一个示例文件
    if not os.path.exists('urls.txt'):
        with open('urls.txt', 'w', encoding='utf-8') as f:
            f.write(example_urls)
        print("✓ 已创建示例 urls.txt 文件，请编辑后重新运行")
        print("\n文件格式说明：")
        print("- 每行一个URL")
        print("- 可选：URL后面加逗号和页数，如：URL,10")
        print("- 以#开头的行会被忽略")
        exit()

    # 创建爬虫实例
    scraper = DigitalingSeleniumScraper(headless=False)

    print("数英网批量项目爬虫")
    print("=" * 60)

    # 批量抓取
    all_data = scraper.scrape_multiple_companies('urls.txt')

    # 保存结果
    if all_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f'digitaling_all_projects_{timestamp}.xlsx'
        scraper.save_to_excel_multiple_sheets(all_data, excel_filename)

        # 打印总体统计
        print("\n" + "=" * 60)
        print("抓取完成！总体统计：")
        total_projects = sum(len(projects) for projects in all_data.values())
        print(f"- 成功抓取 {len(all_data)} 个公司")
        print(f"- 共计 {total_projects} 个项目")
    else:
        print("\n未获取到任何数据")