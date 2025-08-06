import os
import re
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from urllib.parse import urlparse, urljoin
from datetime import datetime
import subprocess


class DigitalingVideoDownloader:
    def __init__(self, headless=False, driver_path=None):
        """初始化视频下载器"""
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

        # 其他选项
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')

        # 启用日志以捕获网络请求
        self.options.add_experimental_option('perfLoggingPrefs', {
            'enableNetwork': True,
            'enablePage': False,
        })
        self.options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})

        self.driver_path = driver_path
        self.driver = None
        self.wait = None

        # 下载设置
        self.download_dir = 'downloaded_videos'
        self.progress_file = 'video_download_progress.json'

        # 创建下载目录
        os.makedirs(self.download_dir, exist_ok=True)

        # Session for downloading
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def find_chrome_driver(self):
        """查找ChromeDriver的路径"""
        possible_names = ['chromedriver.exe', 'chromedriver']

        if self.driver_path and os.path.exists(self.driver_path):
            return self.driver_path

        for name in possible_names:
            if os.path.exists(name):
                print(f"✓ 在当前目录找到ChromeDriver: {name}")
                return os.path.abspath(name)

        possible_dirs = ['.', './drivers', './chromedriver', '../']

        for dir_path in possible_dirs:
            for name in possible_names:
                full_path = os.path.join(dir_path, name)
                if os.path.exists(full_path):
                    print(f"✓ 找到ChromeDriver: {full_path}")
                    return os.path.abspath(full_path)

        return None

    def start_driver(self):
        """启动驱动"""
        try:
            driver_path = self.find_chrome_driver()

            if driver_path:
                service = Service(driver_path)
                self.driver = webdriver.Chrome(service=service, options=self.options)
            else:
                print("⚠ 未在项目目录找到ChromeDriver，尝试使用系统PATH中的...")
                self.driver = webdriver.Chrome(options=self.options)

            self.wait = WebDriverWait(self.driver, 15)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("✓ Chrome驱动启动成功")

        except Exception as e:
            print(f"✗ 启动Chrome驱动失败: {e}")
            raise

    def close_driver(self):
        """关闭驱动"""
        if self.driver:
            self.driver.quit()
            print("✓ Chrome驱动已关闭")

    def get_network_logs(self):
        """获取网络日志，查找视频URL"""
        logs = self.driver.get_log('performance')
        video_urls = []

        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message['message']['method']

                if method == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    url = response['url']
                    mime_type = response.get('mimeType', '')

                    # 检查是否是视频相关的URL
                    if any(ext in url for ext in ['.mp4', '.m3u8', '.flv', '.avi', '.mov', '.webm']):
                        video_urls.append(url)
                    elif 'video' in mime_type:
                        video_urls.append(url)
                    elif any(keyword in url for keyword in ['video', 'vod', 'stream']):
                        if not any(skip in url for skip in ['.js', '.css', '.png', '.jpg', '.gif']):
                            video_urls.append(url)

            except:
                continue

        return list(set(video_urls))  # 去重

    def extract_video_info(self, url):
        """从页面提取视频信息"""
        video_info = {
            'page_url': url,
            'title': '',
            'videos': [],
            'project_id': ''
        }

        try:
            # 提取项目ID
            match = re.search(r'/projects/(\d+)', url)
            if match:
                video_info['project_id'] = match.group(1)

            # 访问页面
            print(f"\n访问页面: {url}")
            self.driver.get(url)
            time.sleep(3)  # 等待页面加载

            # 获取页面标题
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1, .project-title, .title')
                video_info['title'] = title_elem.text.strip()
            except:
                video_info['title'] = self.driver.title.split('|')[0].strip()

            print(f"项目标题: {video_info['title']}")

            # 方法1：查找HTML5 video标签
            video_elements = self.driver.find_elements(By.TAG_NAME, 'video')
            for video in video_elements:
                src = video.get_attribute('src')
                if src:
                    video_info['videos'].append({
                        'type': 'html5_video',
                        'url': urljoin(url, src)
                    })

                # 检查source标签
                sources = video.find_elements(By.TAG_NAME, 'source')
                for source in sources:
                    src = source.get_attribute('src')
                    if src:
                        video_info['videos'].append({
                            'type': 'html5_video',
                            'url': urljoin(url, src)
                        })

            # 方法2：查找iframe（可能包含第三方视频）
            iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                iframe_src = iframe.get_attribute('src')
                if iframe_src and any(
                        platform in iframe_src for platform in ['qq.com', 'youku.com', 'bilibili.com', 'iqiyi.com']):
                    video_info['videos'].append({
                        'type': 'iframe',
                        'url': iframe_src,
                        'platform': self.identify_platform(iframe_src)
                    })

            # 方法3：查找视频链接
            # 滚动页面以加载所有内容
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # 查找可能的视频链接
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and any(ext in href for ext in ['.mp4', '.mov', '.avi', '.flv']):
                    video_info['videos'].append({
                        'type': 'direct_link',
                        'url': href
                    })

            # 方法4：检查网络日志
            network_videos = self.get_network_logs()
            for video_url in network_videos:
                video_info['videos'].append({
                    'type': 'network_capture',
                    'url': video_url
                })

            # 方法5：查找视频播放器的特定class或id
            player_selectors = [
                '.video-player',
                '#video-player',
                '.player-container',
                '[class*="video"]',
                '[id*="video"]',
                '.vjs-tech',  # video.js
                '.plyr',  # plyr
                '.flowplayer'  # flowplayer
            ]

            for selector in player_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    # 获取元素的所有属性
                    attrs = self.driver.execute_script(
                        "var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;",
                        elem
                    )

                    # 查找包含视频URL的属性
                    for attr_name, attr_value in attrs.items():
                        if attr_value and ('mp4' in attr_value or 'video' in attr_value):
                            if attr_value.startswith('http'):
                                video_info['videos'].append({
                                    'type': 'player_attribute',
                                    'url': attr_value
                                })

            # 去重
            unique_videos = []
            seen_urls = set()
            for video in video_info['videos']:
                if video['url'] not in seen_urls:
                    seen_urls.add(video['url'])
                    unique_videos.append(video)

            video_info['videos'] = unique_videos

        except Exception as e:
            print(f"提取视频信息时出错: {e}")

        return video_info

    def identify_platform(self, url):
        """识别视频平台"""
        platforms = {
            'qq.com': '腾讯视频',
            'youku.com': '优酷',
            'bilibili.com': 'B站',
            'iqiyi.com': '爱奇艺',
            'weibo.com': '微博',
            'douyin.com': '抖音'
        }

        for domain, name in platforms.items():
            if domain in url:
                return name

        return '未知平台'

    def download_video(self, video_url, save_path):
        """下载视频"""
        try:
            # 检查是否是m3u8格式
            if '.m3u8' in video_url:
                print(f"检测到m3u8格式，使用ffmpeg下载...")
                return self.download_m3u8(video_url, save_path)

            # 普通视频下载
            print(f"开始下载: {video_url}")
            response = self.session.get(video_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(save_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r下载进度: {progress:.1f}%", end='')

            print(f"\n✓ 下载完成: {save_path}")
            return True

        except Exception as e:
            print(f"\n✗ 下载失败: {e}")
            return False

    def download_m3u8(self, m3u8_url, save_path):
        """使用ffmpeg下载m3u8视频"""
        try:
            # 检查是否安装了ffmpeg
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)

            # 构建ffmpeg命令
            cmd = [
                'ffmpeg',
                '-i', m3u8_url,
                '-c', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                save_path
            ]

            print("使用ffmpeg下载m3u8视频...")
            subprocess.run(cmd, check=True)
            print(f"✓ m3u8视频下载完成: {save_path}")
            return True

        except FileNotFoundError:
            print("✗ 未找到ffmpeg，请先安装ffmpeg")
            print("下载地址: https://ffmpeg.org/download.html")
            return False
        except Exception as e:
            print(f"✗ m3u8下载失败: {e}")
            return False

    def process_links_file(self, links_file='links.txt', resume=True):
        """处理链接文件中的所有链接"""
        if not os.path.exists(links_file):
            print(f"✗ 未找到文件: {links_file}")
            return

        # 读取链接
        links = []
        with open(links_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and 'http' in line:
                    links.append(line)

        print(f"✓ 从 {links_file} 读取到 {len(links)} 个链接")

        if not links:
            return

        # 加载进度
        progress = {}
        if resume and os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                print(f"✓ 找到进度文件，已完成 {len(progress.get('completed', []))} 个链接")
            except:
                progress = {}

        completed = progress.get('completed', [])

        # 启动驱动
        self.start_driver()

        try:
            # 处理每个链接
            for i, link in enumerate(links, 1):
                if link in completed and resume:
                    print(f"\n跳过已完成的链接 {i}/{len(links)}: {link}")
                    continue

                print(f"\n{'=' * 60}")
                print(f"处理第 {i}/{len(links)} 个链接")
                print('=' * 60)

                # 提取视频信息
                video_info = self.extract_video_info(link)

                if video_info['videos']:
                    print(f"\n找到 {len(video_info['videos'])} 个视频")

                    # 创建项目文件夹
                    safe_title = re.sub(r'[^\w\s-]', '', video_info['title'] or f"项目_{video_info['project_id']}")[:50]
                    project_dir = os.path.join(self.download_dir, f"{video_info['project_id']}_{safe_title}")
                    os.makedirs(project_dir, exist_ok=True)

                    # 保存项目信息
                    info_file = os.path.join(project_dir, 'info.json')
                    with open(info_file, 'w', encoding='utf-8') as f:
                        json.dump(video_info, f, ensure_ascii=False, indent=2)

                    # 下载每个视频
                    for j, video in enumerate(video_info['videos'], 1):
                        print(f"\n视频 {j}/{len(video_info['videos'])}")
                        print(f"类型: {video['type']}")
                        print(f"URL: {video['url']}")

                        if video['type'] == 'iframe':
                            print(f"✗ 第三方平台视频 ({video.get('platform', '未知')}), 需要专门工具下载")
                            continue

                        # 确定文件扩展名
                        ext = '.mp4'  # 默认
                        if '.m3u8' in video['url']:
                            ext = '.mp4'  # m3u8转换后为mp4
                        else:
                            # 从URL尝试提取扩展名
                            url_path = urlparse(video['url']).path
                            if '.' in url_path:
                                possible_ext = os.path.splitext(url_path)[1]
                                if possible_ext in ['.mp4', '.flv', '.avi', '.mov', '.webm']:
                                    ext = possible_ext

                        # 下载视频
                        video_filename = f"video_{j}_{video['type']}{ext}"
                        video_path = os.path.join(project_dir, video_filename)

                        if not os.path.exists(video_path):
                            self.download_video(video['url'], video_path)
                        else:
                            print(f"✓ 视频已存在: {video_path}")

                else:
                    print("\n✗ 未找到视频")

                # 更新进度
                completed.append(link)
                progress['completed'] = completed
                progress['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, ensure_ascii=False, indent=2)

                # 休息一下
                if i < len(links):
                    time.sleep(3)

        except KeyboardInterrupt:
            print("\n\n⚠ 用户中断操作")
            print("进度已保存")
        finally:
            self.close_driver()

        # 完成后清理进度文件
        if len(completed) == len(links):
            print("\n✓ 所有链接处理完成！")
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)

    def generate_download_report(self):
        """生成下载报告"""
        report = []

        for project_folder in os.listdir(self.download_dir):
            project_path = os.path.join(self.download_dir, project_folder)
            if os.path.isdir(project_path):
                info_file = os.path.join(project_path, 'info.json')
                if os.path.exists(info_file):
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)

                    video_files = [f for f in os.listdir(project_path) if f.endswith(('.mp4', '.flv', '.avi', '.mov'))]

                    report.append({
                        '项目ID': info['project_id'],
                        '项目标题': info['title'],
                        '页面URL': info['page_url'],
                        '找到视频数': len(info['videos']),
                        '下载视频数': len(video_files),
                        '视频文件': video_files
                    })

        # 保存报告
        report_file = os.path.join(self.download_dir,
                                   f'download_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 下载报告已生成: {report_file}")

        # 打印统计
        total_projects = len(report)
        total_videos = sum(item['下载视频数'] for item in report)
        print(f"\n下载统计:")
        print(f"- 处理项目数: {total_projects}")
        print(f"- 下载视频数: {total_videos}")


# 使用示例
if __name__ == "__main__":
    # 创建示例links.txt文件
    example_links = """# 数英网项目详情页链接
# 每行一个链接
# 以#开头的行会被忽略

https://www.digitaling.com/projects/326465.html
https://www.digitaling.com/projects/326206.html
https://www.digitaling.com/projects/325847.html
"""

    # 如果links.txt不存在，创建示例文件
    if not os.path.exists('links.txt'):
        with open('links.txt', 'w', encoding='utf-8') as f:
            f.write(example_links)
        print("✓ 已创建示例 links.txt 文件")
        print("请在文件中添加要下载视频的项目页面链接")
        exit()

    # 创建下载器
    downloader = DigitalingVideoDownloader(headless=False)  # 设置True可后台运行

    print("数英网视频下载器")
    print("=" * 60)
    print("功能说明:")
    print("- 自动识别并下载页面中的视频")
    print("- 支持HTML5视频、直接链接等")
    print("- 支持断点续传")
    print("- 每个项目创建独立文件夹")
    print("=" * 60)

    # 开始处理
    downloader.process_links_file('links.txt')

    # 生成报告
    downloader.generate_download_report()