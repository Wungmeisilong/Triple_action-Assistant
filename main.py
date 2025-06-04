from BiliLoginBot import BiliLoginBot
from AnimePageAccess import AnimePageAccess
import os
import logging

# 配置日志
logger = logging.getLogger('bilibili_bot')

# 定义cookie文件路径
COOKIE_FILE = "bili_cookies.pkl"

# 定义番剧页面
ANIME_URL = "https://www.bilibili.com/bangumi/play/ss45734?from_spmid=666.25.series.0"  # 示例番剧页面
PARENT_CONTAINER = "numberList_wrapper___SI4W"  # 图片中的类名
CHILD_CONTAINER = "numberListItem_number_list_item__T2VKO"  # 图片中的类名
COIN_RECORD_URL = "https://account.bilibili.com/account/coin"

if __name__ == "__main__":
    # 替换为你的ChromeDriver实际路径
    DRIVER_PATH = "C:/Program Files/Google/Chrome/Application/chromeDriver/chromedriver-win64/chromedriver.exe"
    
    # 创建登录机器人实例
    login_bot = BiliLoginBot(DRIVER_PATH)
    
    try:
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
                                login_bot.get_user_coin(COIN_RECORD_URL)
                                login_bot.save_cookies(COOKIE_FILE)
                            else:
                                logger.error("用户未完成确认操作")
                                login_bot.close_browser()
                                exit()
            else:
                logger.error("加载cookie失败，需要重新扫码登录")
                # 执行正常扫码流程
                if login_bot.open_login_page():
                    logger.info("请使用手机B站APP扫描二维码")
                    if login_bot.wait_for_qrcode_scan():
                        logger.info("扫码成功！请在手机上选择登录选项并确认")
                        if login_bot.wait_for_login_confirmation():
                            login_bot.get_user_coin(COIN_RECORD_URL)
                            login_bot.save_cookies(COOKIE_FILE)
                        else:
                            logger.error("用户未完成确认操作")
                            login_bot.close_browser()
                            exit()
        else:
            logger.info("未找到cookie文件，需要扫码登录")
            # 执行正常扫码流程
            if login_bot.open_login_page():
                logger.info("请使用手机B站APP扫描二维码")
                if login_bot.wait_for_qrcode_scan():
                    logger.info("扫码成功！请在手机上选择登录选项并确认")
                    if login_bot.wait_for_login_confirmation():
                        login_bot.get_user_coin(COIN_RECORD_URL)
                        login_bot.save_cookies(COOKIE_FILE)
                    else:
                        logger.error("用户未完成确认操作")
                        login_bot.close_browser()
                        exit()
        
        # 步骤3: 获取用户硬币信息
        if login_bot.get_user_coin(COIN_RECORD_URL, timeout=3):
           testCoin = login_bot.coin
           logger.info(f"用户硬币值： {login_bot.coin }")
        else:
            logger.error("获取用户硬币信息失败")
            login_bot.close_browser()
            exit()
        # 步骤5: 访问番剧页面
        anime_access = AnimePageAccess(login_bot.driver)
        if anime_access.navigate_and_verify_page(ANIME_URL):
            logger.info("成功进入番剧页面")
            episode_bool = anime_access.get_all_episodes_urls(
                parent_class=PARENT_CONTAINER,  # 图片中的父容器类名
                child_class=CHILD_CONTAINER       # 图片中的子容器类名
                )
            # 循环执行操作
            for episode_index in range(5, 20): #意思是从第6集到第20集

                if testCoin <= 4:
                    logger.info("硬币不足，停止操作")
                    break
                if episode_bool:
                    anime_access.process_specific_episode(episode_index, delay=1.0, triple_action=True)
                testCoin -= 2  # 假设每次操作消耗2个硬币

    except Exception as e:
        logger.exception(f"程序运行出错: {str(e)}")
    finally:
        # 确保浏览器被关闭
        login_bot.close_browser()