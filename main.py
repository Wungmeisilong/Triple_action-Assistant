from BiliLoginBot import BiliLoginBot
from AnimePageAccess import AnimePageAccess
import os
import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time

# 配置日志
logger = logging.getLogger('bilibili_bot')

# 定义cookie文件路径
COOKIE_FILE = "bili_cookies.pkl"

# 定义番剧页面
ANIME_URL = "https://www.bilibili.com/bangumi/play/ss28747?from_spmid=666.5.hotlist.0"  # 示例番剧页面
PARENT_CONTAINER = "numberList_wrapper___SI4W"  # 图片中的类名
CHILD_CONTAINER = "numberListItem_number_list_item__T2VKO"  # 图片中的类名
COIN_RECORD_URL = "https://account.bilibili.com/account/coin"

class BiliBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("B站硬币自动投币工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置日志队列
        self.log_queue = []
        self.running = False
        
        # 创建UI
        self.create_widgets()
        
        # 配置日志处理器
        self.setup_logging()
        
        # 启动日志更新线程
        self.update_logs()
    
    def create_widgets(self):
        # 标题
        title_frame = tk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(title_frame, text="B站硬币自动投币工具", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 状态信息
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(status_frame, text="当前状态:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(status_frame, textvariable=self.status_var, fg="blue", font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W)
        
        tk.Label(status_frame, text="硬币数量:", font=("Arial", 10)).grid(row=0, column=2, padx=(20, 0), sticky=tk.W)
        self.coin_var = tk.StringVar(value="0")
        tk.Label(status_frame, textvariable=self.coin_var, fg="green", font=("Arial", 10, "bold")).grid(row=0, column=3, sticky=tk.W)
        
        # 日志区域
        log_frame = tk.LabelFrame(self.root, text="操作日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)
        
        # 控制按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = tk.Button(button_frame, text="开始执行", command=self.start_bot, width=15, height=2)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(button_frame, text="停止", command=self.stop_bot, state=tk.DISABLED, width=15, height=2)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="退出", command=self.root.destroy, width=15, height=2).pack(side=tk.RIGHT, padx=5)
    
    def setup_logging(self):
        # 创建自定义日志处理器
        class QueueHandler(logging.Handler):
            def __init__(self, log_queue):
                super().__init__()
                self.log_queue = log_queue
            
            def emit(self, record):
                msg = self.format(record)
                self.log_queue.append(msg)
        
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 添加GUI处理器
        gui_handler = QueueHandler(self.log_queue)
        gui_handler.setFormatter(formatter)
        logger.addHandler(gui_handler)
        
        logger.setLevel(logging.INFO)
    
    def update_logs(self):
        if self.log_queue:
            self.log_area.config(state=tk.NORMAL)
            while self.log_queue:
                msg = self.log_queue.pop(0)
                self.log_area.insert(tk.END, msg + "\n")
            self.log_area.config(state=tk.DISABLED)
            self.log_area.yview(tk.END)
        
        self.root.after(100, self.update_logs)
    
    def start_bot(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set("运行中...")
            
            # 在新线程中运行bot
            bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            bot_thread.start()
    
    def stop_bot(self):
        if self.running:
            self.running = False
            self.status_var.set("已停止")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            logger.info("用户手动停止程序")
    
    def run_bot(self):
        try:
            # 替换为你的ChromeDriver实际路径
            DRIVER_PATH = "C:/Program Files/Google/Chrome/Application/chromeDriver/chromedriver-win64/chromedriver.exe"
            
            # 创建登录机器人实例
            login_bot = BiliLoginBot(DRIVER_PATH)
            
            # 检查cookie文件是否存在
            if os.path.exists(COOKIE_FILE):
                logger.info("检测到cookie文件，尝试加载登录状态...")
                
                # 步骤1: 加载保存的cookies
                if login_bot.load_cookies(COOKIE_FILE):
                    # 步骤2: 验证登录状态
                    if login_bot.is_logged_in():
                        logger.info("Cookie登录成功！跳过扫码流程")
                    else:
                        logger.warning("Cookie登录失败，需要重新扫码登录")
                        # 执行正常扫码流程
                        if login_bot.open_login_page():
                            logger.info("请使用手机B站APP扫描二维码")
                            if login_bot.wait_for_qrcode_scan():
                                logger.info("扫码成功！请在手机上选择登录选项并确认")
                                if login_bot.wait_for_login_confirmation():
                                    login_bot.save_cookies(COOKIE_FILE)
                                else:
                                    logger.error("用户未完成确认操作")
                                    login_bot.close_browser()
                                    return
                else:
                    logger.error("加载cookie失败，需要重新扫码登录")
                    # 执行正常扫码流程
                    if login_bot.open_login_page():
                        logger.info("请使用手机B站APP扫描二维码")
                        if login_bot.wait_for_qrcode_scan():
                            logger.info("扫码成功！请在手机上选择登录选项并确认")
                            if login_bot.wait_for_login_confirmation():
                                login_bot.save_cookies(COOKIE_FILE)
                            else:
                                logger.error("用户未完成确认操作")
                                login_bot.close_browser()
                                return
            else:
                logger.info("未找到cookie文件，需要扫码登录")
                # 执行正常扫码流程
                if login_bot.open_login_page():
                    logger.info("请使用手机B站APP扫描二维码")
                    if login_bot.wait_for_qrcode_scan():
                        logger.info("扫码成功！请在手机上选择登录选项并确认")
                        if login_bot.wait_for_login_confirmation():
                            login_bot.save_cookies(COOKIE_FILE)
                        else:
                            logger.error("用户未完成确认操作")
                            login_bot.close_browser()
                            return
            
            # 步骤3: 获取用户硬币信息
            if login_bot.get_user_coin(COIN_RECORD_URL, timeout=15,retries=2):
                testCoin = login_bot.coin
                self.coin_var.set(str(login_bot.coin))
                logger.info(f"用户硬币值： {login_bot.coin}")
            else:
                logger.error("获取用户硬币信息失败")
                login_bot.close_browser()
                return
            
            # 步骤5: 访问番剧页面
            anime_access = AnimePageAccess(login_bot.driver)
            if anime_access.navigate_and_verify_page(ANIME_URL):
                logger.info("成功进入番剧页面")
                episode_bool = anime_access.get_all_episodes_urls(
                    parent_class=PARENT_CONTAINER,  # 图片中的父容器类名
                    child_class=CHILD_CONTAINER       # 图片中的子容器类名
                )
                
                # 循环执行操作
                for episode_index in range(20, 35):  # 意思是从第21集到第29集
                    if not self.running:
                        logger.info("用户停止操作")
                        break
                    
                    if testCoin <= 4:
                        logger.info("硬币不足，停止操作")
                        break
                    
                    if episode_bool:
                        anime_access.process_specific_episode(episode_index, delay=1.0, triple_action=True)
                    
                    testCoin -= 2  # 假设每次操作消耗2个硬币
                    self.coin_var.set(str(testCoin))
                    time.sleep(1)  # 添加短暂延迟
            
            logger.info("程序执行完成")
            self.status_var.set("执行完成")
            
        except Exception as e:
            logger.exception(f"程序运行出错: {str(e)}")
            self.status_var.set(f"错误: {str(e)}")
        finally:
            self.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            # 确保浏览器被关闭
            if 'login_bot' in locals():
                login_bot.close_browser()

if __name__ == "__main__":
    root = tk.Tk()
    app = BiliBotGUI(root)
    root.mainloop()