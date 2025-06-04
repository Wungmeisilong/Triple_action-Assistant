from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import pickle
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bilibili_bot')

class BiliLoginBot:
    def __init__(self, driver_path):
        """初始化浏览器驱动"""
        self.service = ChromeService(executable_path=driver_path)
        self.coin = 0  # 初始化硬币数量为0
        # 配置浏览器选项
        self.options = webdriver.ChromeOptions()
        self._setup_options()
        
        # 初始化浏览器驱动
        self.driver = webdriver.Chrome(service=self.service, options=self.options)
        #self.driver.implicitly_wait(15)
        logger.info("浏览器驱动初始化成功")
        
        # 添加防检测配置
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {'source': '''Object.defineProperty(navigator, 'webdriver', { get: () => undefined })'''}
        )
    
    def _setup_options(self):
        """配置浏览器选项 - 强化稳定性"""
        # 防止被检测为自动化工具
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # SSL相关的修复选项
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument('--disable-web-security')
        
        # 其他优化选项
        self.options.add_argument("--window-size=1200,800")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-notifications")
        
        # 保持窗口不自动关闭
        self.options.add_experimental_option("detach", True)
        
        # 使用最新的用户代理
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        # 禁用日志输出
        self.options.add_argument("--log-level=3")
        self.options.add_argument("--disable-logging")
    
    def open_login_page(self):
        """打开登录页面并确保显示二维码区域"""
        logger.info("打开B站登录页面...")
        try:
            # 使用指定登录页面URL
            self.driver.get("https://passport.bilibili.com/login")
            logger.info("登录页面已加载")
            
            # 确保二维码区域存在
            WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".login-scan__qrcode"))
            )
            logger.info("检测到二维码区域")
            return True
        except TimeoutException:
            logger.error("未找到二维码区域")
            return False
    
    def wait_for_qrcode_scan(self, timeout=120):
        """等待用户扫码"""
        logger.info("等待用户手机扫码...")
        try:
            # 等待扫码成功提示出现
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".qrcode__tip"))
            )
            logger.info("检测到扫码成功提示，请在手机上确认")
            return True
        except TimeoutException:
            logger.error("用户未在手机上扫码")
            return False
    
    def wait_for_login_confirmation(self, timeout=180):
        """等待用户在手机上确认后登录成功"""
        logger.info("等待用户在手机上确认...")
        try:
            # 等待登录成功（检测用户头像）
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".v-img"))
            )
            logger.info("登录成功！检测到用户头像")
            
            # 确认是否进入主站
            try:
                self.driver.get("https://www.bilibili.com")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".v-img"))
                )
                logger.info("确认已进入B站主站")
            except:
                logger.warning("直接进入主站失败，尝试通过当前页面确认")
            
            return True
        except TimeoutException:
            logger.error("用户未在手机上完成确认操作")
            return False
    
    def is_logged_in(self):
        """检查是否已登录"""
        try:
            # 检查用户头像是否存在
            avatar = self.driver.find_element(By.CSS_SELECTOR, ".v-img")
            logger.info(f"已登录用户：{avatar.get_attribute('alt')}")
            return True
        except NoSuchElementException:
            return False
    
    def get_user_coin(self, coin_record_url="https://account.bilibili.com/account/coin", timeout=10):
        """
        获取用户硬币余额
        :param coin_record_url: 硬币记录页面URL
        :param timeout: 超时时间（秒）
        :return: 操作是否成功 (硬币值存储在self.coin属性中)
        """
        try:
            logger.info(f"正在访问硬币记录页面: {coin_record_url}")
            
            # 1. 导航到硬币记录页面
            self.driver.get(coin_record_url)
            logger.info("页面已加载")
            
            # 2. 等待硬币数据容器出现
            coin_container = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".coin-index-title"))
            )
            logger.info("已找到硬币余额容器")

            # 3. 找到硬币数值元素
            coin_element = coin_container.find_element(By.CSS_SELECTOR, "i.coin-num")
            
            # 4. 获取硬币数值
            coin_value = coin_element.text
            logger.info(f"获取到硬币余额文本: '{coin_value}'")

            # 5. 解析硬币值 (去除可能的空格和特殊字符)
            try:
                cleaned_value = coin_value.strip()  # 去除空白字符
                
                # 处理可能的货币符号或单位
                if cleaned_value.endswith('硬币'):
                    cleaned_value = cleaned_value.replace('硬币', '').strip()
                
                # 转换为浮点数
                self.coin = float(cleaned_value)
                logger.info(f"硬币余额解析成功: {self.coin}")
            except ValueError:
                logger.error(f"硬币值解析失败: '{coin_value}'")
                return False
            
            # 6. 返回上一页面
            logger.info("返回上一页面...")
            self.driver.back()
            
            # 7. 等待返回完成 (给页面足够时间加载)
            time.sleep(1)

            logger.info("硬币余额获取完成")
            return True
            
        except TimeoutException:
            logger.error("查找硬币元素超时")
            return False
        except NoSuchElementException:
            logger.error("未找到硬币元素")
            return False
        except Exception as e:
            logger.error(f"获取硬币余额时出错: {str(e)}")
            return False

    def save_cookies(self, filename="bili_cookies.pkl"):
        """保存登录后的cookies"""
        try:
            cookies = self.driver.get_cookies()
            with open(filename, 'wb') as file:
                pickle.dump(cookies, file)
            logger.info(f"登录状态已保存至: {filename}")
            return True
        except Exception as e:
            logger.error(f"保存cookies失败: {str(e)}")
            return False
    
    def load_cookies(self, filename="bili_cookies.pkl"):
        """加载保存的cookies"""
        try:
            # 1. 打开网站首页（设置域名）
            self.driver.get("https://www.bilibili.com")
            
            # 2. 加载保存的cookies
            with open(filename, 'rb') as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    # 3. 添加每个cookie到浏览器
                    self.driver.add_cookie(cookie)
            
            logger.info(f"已加载登录状态: {filename}")
            return True
        except Exception as e:
            logger.error(f"加载cookies失败: {str(e)}")
            return False
    
    def close_browser(self):
        """关闭浏览器（用户确认后关闭）"""
        logger.info("浏览器将在用户确认后关闭")
        input("按Enter键关闭浏览器...")
        try:
            self.driver.quit()
            logger.info("浏览器已关闭")
            return True
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {str(e)}")
            return False
