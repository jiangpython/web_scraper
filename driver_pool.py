"""
WebDriver连接池管理
优化WebDriver资源使用，避免频繁创建销毁
"""

import threading
import time
import random
import os
from queue import Queue, Empty
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


class DriverPool:
    """WebDriver连接池"""
    
    def __init__(self, pool_size=3, max_idle_time=300, headless=True):
        """
        初始化连接池
        
        Args:
            pool_size: 连接池大小
            max_idle_time: 最大空闲时间（秒）
            headless: 是否无头模式
        """
        self.pool_size = pool_size
        self.max_idle_time = max_idle_time
        self.headless = headless
        
        # 连接池队列
        self.available_drivers = Queue(maxsize=pool_size)
        self.busy_drivers = set()
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 驱动配置
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # 启动时预创建驱动
        self._initialize_pool()
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self._cleanup_idle_drivers, daemon=True)
        self.cleanup_thread.start()
    
    def find_chrome_driver(self):
        """查找ChromeDriver路径"""
        possible_names = ['chromedriver.exe', 'chromedriver']
        possible_dirs = ['.', './drivers', './chromedriver', '../']
        
        for dir_path in possible_dirs:
            for name in possible_names:
                full_path = os.path.join(dir_path, name)
                if os.path.exists(full_path):
                    return os.path.abspath(full_path)
        return None
    
    def _create_driver(self):
        """创建新的WebDriver实例"""
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # 反反爬虫设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-webgl2')
        options.add_argument('--window-size=1920,1080')
        
        # 随机User-Agent
        options.add_argument(f'user-agent={random.choice(self.user_agents)}')
        
        # 创建WebDriver
        driver_path = self.find_chrome_driver()
        try:
            if driver_path:
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)
            
            # 隐藏webdriver特征
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 添加元数据
            driver.last_used = time.time()
            driver.created_at = time.time()
            
            return driver
            
        except Exception as e:
            print(f"创建WebDriver失败: {e}")
            try:
                # 尝试使用webdriver-manager
                from webdriver_manager.chrome import ChromeDriverManager
                from selenium.webdriver.chrome.service import Service as ChromeService
                driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
                
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                driver.last_used = time.time()
                driver.created_at = time.time()
                
                return driver
            except ImportError:
                print("webdriver-manager未安装，请运行: pip install webdriver-manager")
                raise e
            except Exception as e2:
                print(f"webdriver-manager也失败了: {e2}")
                raise e
    
    def _initialize_pool(self):
        """初始化连接池"""
        print(f"正在初始化WebDriver连接池（大小：{self.pool_size}）...")
        
        for i in range(self.pool_size):
            try:
                driver = self._create_driver()
                self.available_drivers.put(driver)
                print(f"WebDriver {i+1}/{self.pool_size} 创建成功")
            except Exception as e:
                print(f"WebDriver {i+1}/{self.pool_size} 创建失败: {e}")
        
        print(f"WebDriver连接池初始化完成，可用连接数: {self.available_drivers.qsize()}")
    
    def get_driver(self, timeout=30):
        """
        获取WebDriver
        
        Args:
            timeout: 获取超时时间（秒）
            
        Returns:
            WebDriver实例
        """
        # 尝试从池中获取可用驱动
        try:
            driver = self.available_drivers.get(timeout=timeout)
        except Empty:
            # 如果池为空，创建新驱动
            print("⚠ 连接池为空，创建新的WebDriver...")
            driver = self._create_driver()
        
        # 标记为忙碌状态
        with self.lock:
            self.busy_drivers.add(driver)
        
        # 更新使用时间
        driver.last_used = time.time()
        
        return driver
    
    @contextmanager
    def get_driver_context(self, timeout=30):
        """
        获取WebDriver（上下文管理器）
        
        Args:
            timeout: 获取超时时间（秒）
            
        Usage:
            with pool.get_driver_context() as driver:
                driver.get("https://example.com")
        """
        driver = None
        try:
            driver = self.get_driver(timeout)
            yield driver
        finally:
            if driver:
                # 归还驱动到池中
                self._return_driver(driver)
    
    def return_driver(self, driver):
        """公共方法：归还WebDriver到池中"""
        self._return_driver(driver)
    
    def _return_driver(self, driver):
        """归还WebDriver到池中"""
        try:
            # 检查驱动是否还可用
            if self._is_driver_alive(driver):
                # 更新使用时间
                driver.last_used = time.time()
                
                # 从忙碌集合中移除
                with self.lock:
                    self.busy_drivers.discard(driver)
                
                # 如果池未满，归还到池中
                if not self.available_drivers.full():
                    self.available_drivers.put(driver)
                else:
                    # 池已满，关闭多余的驱动
                    self._close_driver(driver)
            else:
                # 驱动不可用，关闭并从忙碌集合中移除
                with self.lock:
                    self.busy_drivers.discard(driver)
                self._close_driver(driver)
                
        except Exception as e:
            print(f"⚠ 归还WebDriver时出错: {e}")
            with self.lock:
                self.busy_drivers.discard(driver)
            self._close_driver(driver)
    
    def _is_driver_alive(self, driver):
        """检查WebDriver是否还可用"""
        try:
            driver.current_url
            return True
        except:
            return False
    
    def _close_driver(self, driver):
        """安全关闭WebDriver"""
        try:
            driver.quit()
        except:
            pass
    
    def _cleanup_idle_drivers(self):
        """清理空闲的WebDriver"""
        while True:
            try:
                time.sleep(60)  # 每分钟检查一次
                
                current_time = time.time()
                drivers_to_remove = []
                
                # 检查可用池中的空闲驱动
                temp_drivers = []
                while not self.available_drivers.empty():
                    try:
                        driver = self.available_drivers.get_nowait()
                        if (current_time - driver.last_used) > self.max_idle_time:
                            drivers_to_remove.append(driver)
                        else:
                            temp_drivers.append(driver)
                    except Empty:
                        break
                
                # 重新放回非空闲的驱动
                for driver in temp_drivers:
                    self.available_drivers.put(driver)
                
                # 关闭空闲的驱动
                for driver in drivers_to_remove:
                    self._close_driver(driver)
                    print(f"清理空闲WebDriver（空闲时间：{current_time - driver.last_used:.1f}秒）")
                
                # 确保池中至少有一个驱动
                if self.available_drivers.empty() and len(self.busy_drivers) == 0:
                    try:
                        new_driver = self._create_driver()
                        self.available_drivers.put(new_driver)
                        print("创建新的WebDriver以维持连接池")
                    except Exception as e:
                        print(f"维护连接池时创建WebDriver失败: {e}")
                
            except Exception as e:
                print(f"⚠ 清理空闲WebDriver时出错: {e}")
    
    def get_pool_status(self):
        """获取连接池状态"""
        return {
            "available": self.available_drivers.qsize(),
            "busy": len(self.busy_drivers),
            "total": self.available_drivers.qsize() + len(self.busy_drivers),
            "max_size": self.pool_size
        }
    
    def close_all(self):
        """关闭所有WebDriver"""
        print("正在关闭WebDriver连接池...")
        
        # 关闭可用池中的驱动
        while not self.available_drivers.empty():
            try:
                driver = self.available_drivers.get_nowait()
                self._close_driver(driver)
            except Empty:
                break
        
        # 关闭忙碌的驱动
        busy_drivers_copy = list(self.busy_drivers)
        for driver in busy_drivers_copy:
            self._close_driver(driver)
        
        self.busy_drivers.clear()
        print("WebDriver连接池已关闭")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.close_all()
        except:
            pass


# 全局连接池实例
_global_driver_pool = None
_pool_lock = threading.Lock()


def get_global_pool(pool_size=3, headless=True):
    """获取全局WebDriver连接池"""
    global _global_driver_pool
    
    with _pool_lock:
        if _global_driver_pool is None:
            _global_driver_pool = DriverPool(pool_size=pool_size, headless=headless)
    
    return _global_driver_pool


def close_global_pool():
    """关闭全局WebDriver连接池"""
    global _global_driver_pool
    
    with _pool_lock:
        if _global_driver_pool is not None:
            _global_driver_pool.close_all()
            _global_driver_pool = None