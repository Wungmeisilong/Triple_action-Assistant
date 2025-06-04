import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BilibiliTripleAction:
    def __init__(self, driver):
        self.driver = driver
        self.logger = logging.getLogger('bili_triple_action')
    
        
    def is_triple_active(self):
        """使用组合选择器一次性检查三连状态"""
        try:
            combined_selector = (
                ".toolbar-left > span#like_info.on, "
                ".toolbar-left > span#ogv_weslie_tool_coin_info.on, "
                ".toolbar-left > span#ogv_weslie_tool_favorite_info.on"
            )
            
            # 单次等待替代多次等待
            elements = WebDriverWait(self.driver, 3.5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, combined_selector))
            )
            return len(elements) == 3
        except TimeoutException:
            return False
        except Exception as e:
            self.logger.error(f"检查三连状态出错: {str(e)}")
            return False
    
    def is_active(self, element_name):
        """
        检查按钮是否处于激活状态（有'on'类）
        :param element_name: 按钮名称 (like/coin/favorite)
        """
        selectors = {
            'like': "#like_info.on",
            'coin': "#ogv_weslie_tool_coin_info.on",
            'favorite': "#ogv_weslie_tool_favorite_info.on"
        }
        
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selectors[element_name])
            self.logger.info(f"{element_name}按钮已处于激活状态")
            return True
        except:
            self.logger.info(f"{element_name}按钮未激活，需要操作")
            return False
        
    def is_button_active(self, element_id):
        """
        检查按钮是否处于激活状态（是否包含'on'类）
        :param element_id: 按钮ID
        :return: 是否激活
        """
        try:
            element = self.driver.find_element(By.ID, element_id)
            return 'on' in element.get_attribute('class')
        except:
            return False
            
    def safe_js_click(self, css_selector):
        """
        安全的JavaScript点击（规避点击问题）
        :param css_selector: CSS选择器
        :return: 是否成功
        """
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
            self.driver.execute_script("arguments[0].click();", element)
            time.sleep(0.5)  # 等待操作生效
            return True
        except Exception as e:
            self.logger.error(f"点击元素失败: {css_selector} - {str(e)}")
            return False

    def handle_like(self):
        """处理点赞操作（无弹窗）"""
        if self.is_button_active("like_info"):
            self.logger.info("点赞已激活，无需操作")
            return True
            
        return self.safe_js_click("#like_info")
    
    def handle_coin(self):
        """处理投币操作（带弹窗）"""
        if self.is_button_active("ogv_weslie_tool_coin_info"):
            self.logger.info("投币已激活，无需操作")
            return True
            
        # 1. 点击投币按钮
        if not self.safe_js_click("#ogv_weslie_tool_coin_info"):
            return False
        
        # 2. 等待投币弹窗出现（图1）
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".dialogcoin_coin_operated__KhIb2"))
            )
            self.logger.info("投币弹窗已显示")
        except:
            self.logger.error("投币弹窗未显示，操作失败")
            return False
        
        # 4. 点击确定按钮
        return self.safe_js_click(".dialogcoin_coin_btn__be9sU")
    
    def handle_favorite(self):
        """处理收藏操作（带弹窗，需要选择默认收藏夹）"""
        if self.is_button_active("ogv_weslie_tool_favorite_info"):
            self.logger.info("收藏已激活，无需操作")
            return True
            
        # 1. 点击收藏按钮
        if not self.safe_js_click("#ogv_weslie_tool_favorite_info"):
            return False
        
        # 2. 等待收藏弹窗出现（图2）
        try:
            WebDriverWait(self.driver, 4).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".DialogCollect_content__lBPfq"))
            )
            self.logger.info("收藏弹窗已显示")
        except:
            self.logger.error("收藏弹窗未显示，操作失败")
            return False
        
        # 3. 选择默认收藏夹（图2）
        # 使用更精确的选择器定位第一个收藏夹
        # 图片中显示的结构是第一个li内的label和checkbox
        try:
            self.safe_js_click(".DialogCollect_groupList__msAqc li:first-child label")
        except:
            self.logger.error("选择默认收藏夹失败")
            return False

        return self.safe_js_click(".DialogCollect_btn__VErcg")

    def perform_triple_action(self):
        """执行完整的一键三连操作"""
        results = []
        
        # 点赞
        like_result = self.handle_like()
        results.append(like_result)
        if not like_result:
            self.logger.error("点赞操作失败")
        
        # 投币（等待点赞操作完成）
        time.sleep(1)
        coin_result = self.handle_coin()
        results.append(coin_result)
        if not coin_result:
            self.logger.error("投币操作失败")
        
        # 收藏（等待投币操作完成）
        time.sleep(1)
        favorite_result = self.handle_favorite()
        results.append(favorite_result)
        if not favorite_result:
            self.logger.error("收藏操作失败")
        
        # 完成确认
        if all(results):
            self.logger.info("三连操作成功完成!")
            return True
        
        self.logger.error("三连操作存在失败步骤")
        return False
    
    #*************************************************************************************************************************
    
    def smart_triple_action(self):
        """
        智能三连操作：尝试多种方式
        """
        max_attempts = 1
        methods = [
            self.perform_triple_action # 使用组合方法执行三连
            #self.try_long_press #长按实现一键三连
        ]

        for attempt in range(max_attempts):
            for method in methods:
                self.logger.info(f"尝试方法 {method.__name__} (尝试 #{attempt+1})")
                
                try:
                    if method():
                        if self.is_triple_active():
                            self.logger.info("三连操作成功")
                            return True
                        else:
                            self.logger.warning("方法成功但状态未更新")
                    else:
                        self.logger.warning("方法执行失败")
                except Exception as e:
                    self.logger.error(f"执行方法时出错: {str(e)}")
                
                # 尝试间短暂等待
                time.sleep(0.7)

        return False
    
    def try_long_press(self):
        """
        尝试长按操作 (含错误处理)
        """
        from selenium.webdriver.common.action_chains import ActionChains
        
        try:
            self.logger.info("尝试长按点赞按钮")
            
            # 定位点赞按钮 (使用图片中的ID)
            like_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'like_info'))
            )
            
            # 确保按钮在视口中
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                like_button
            )
            time.sleep(0.5)
            
            # 创建动作链
            actions = ActionChains(self.driver)
            
            # 尝试模拟长按 (2.5秒)
            actions.move_to_element(like_button)
            actions.click_and_hold()
            actions.pause(2.5)
            actions.release()
            
            # 执行整个动作链
            actions.perform()
            
            self.logger.info("长按操作完成")
            time.sleep(2)  # 等待可能的响应
            
            return True
            
        except WebDriverException as wde:
            self.logger.error(f"底层驱动错误: {str(wde)}")
            return False
        except Exception as e:
            self.logger.error(f"长按操作失败: {str(e)}")
            return False
    
    def check_and_operate(self,end_time=0):
        """
        主操作逻辑
        """
        try:
            # 首先检查是否已经三连
            start_time = time.time()
            if self.is_triple_active():
                self.logger.info(f"三连检查耗时: {time.time()-start_time:.2f}秒")
                return 0
                
            # 执行三连操作
            if self.smart_triple_action():
                time.sleep(2)  # 等待状态更新
                
                # 验证结果
                if self.is_triple_active():
                    self.logger.info("成功完成三连操作")
                    return 1
                else:
                    self.logger.warning("操作成功但三连状态未激活")
                    return -1
            else:
                self.logger.error("所有三连方法均失败")
                return -1
                
        except Exception as e:
            self.logger.error(f"三连操作过程中出错: {str(e)}")
            return -1