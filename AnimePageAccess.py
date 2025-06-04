from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from BilibiliTripleAction import BilibiliTripleAction
import time
import logging

class AnimePageAccess:
    def __init__(self, driver):
        """
        初始化番剧页面访问类
        :param driver: WebDriver实例
        """
        self.driver = driver
        self.logger = logging.getLogger('anime_access')
        self.episode_urls = []
    
    def navigate_and_verify_page(self, url, container_class="mediainfo_mediaInfoWrap__nCwhA", timeout=30):
        """
        跳转页面并验证页面是否存在
        :param url: 要导航的URL
        :param container_class: 验证页面存在的容器类名
        :param timeout: 超时时间（秒）
        :return: 如果页面存在返回True，否则False
        """
        try:
            # 导航到指定URL
            self.driver.get(url)
            self.logger.info(f"已导航至: {url}")
            
            # 等待容器出现（使用类选择器）
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, container_class))
            )
            self.logger.info(f"检测到容器 {container_class}，页面验证成功")
            return True
        except TimeoutException:
            self.logger.error(f"页面加载超时，未找到容器 {container_class}")
            return False
        except NoSuchElementException:
            self.logger.error(f"页面元素定位失败: NoSuchElementException")
            return False
        except Exception as e:
            self.logger.error(f"导航并验证页面时出错: {str(e)}")
            return False
    
    def get_all_episodes_urls(self, parent_class="numberList_wrapper___SI4W", 
                         child_class="numberListItem_number_list_item__T2VKO", 
                         timeout=15):
        """
        获取所有剧集URL
        :param parent_class: 父容器类名
        :param child_class: 子容器类名
        :param timeout: 超时时间（秒）
        :return: 所有剧集URL列表，如果失败则返回空列表
        """
        try:
            self.logger.info(f"在容器 {parent_class} 中查找所有剧集URL...")
            
            # 1. 等待父容器出现
            parent_container = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, parent_class))
            )
            self.logger.info(f"成功找到父容器: {parent_class}")
            
            # 2. 滚动到父容器（确保可见）
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_container)
            self.logger.info("已滚动到父容器")
            time.sleep(0.5)  # 等待滚动完成
            
            # 3. 查找所有子容器（使用更健壮的等待）
            child_containers = WebDriverWait(parent_container, timeout).until(
                lambda container: container.find_elements(By.CLASS_NAME, child_class)
            )
            
            if not child_containers:
                # 特殊情况：再次尝试查找（有时需要额外等待）
                self.logger.warning("首次查找无结果，尝试再次查找...")
                time.sleep(1)  # 额外等待1秒
                child_containers = parent_container.find_elements(By.CLASS_NAME, child_class)
            
            if not child_containers:
                self.logger.error(f"父容器中没有找到任何'{child_class}'子项")
                return False
            
            # 4. 记录找到的子容器数量
            total_episodes = len(child_containers)
            self.logger.info(f"找到 {total_episodes} 个剧集")

            # 6. 遍历所有子容器，获取每个URL
            for idx, child_container in enumerate(child_containers):
                try:
                    # 7. 确保子容器可见（重点！）
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                        child_container
                    )
                    time.sleep(0.1)  # 短暂等待滚动完成
                    
                    # 8. 查找<a>标签获取URL
                    a_tag = child_container.find_element(By.TAG_NAME, "a")
                    episode_url = a_tag.get_attribute("href")
                    
                    # 9. 记录详细信息
                    #title = child_container.get_attribute("title")
                    #self.logger.info(f"获取剧集 {idx+1}/{total_episodes} URL (标题: {title}): {episode_url}")

                    self.episode_urls.append(episode_url)

                except Exception as e:
                    self.logger.error(f"获取第 {idx+1} 个剧集URL时出错: {str(e)}")
                    continue  # 继续处理下一个
            
            # 10. 返回所有URL列表
            self.logger.info(f"成功获取 {len(self.episode_urls)}/{total_episodes} 个剧集URL")
            return True

        except TimeoutException:
            self.logger.error(f"查找容器超时: {parent_class} 或 {child_class}")
            # 尝试截图辅助调试
            try:
                self.driver.save_screenshot("error_find_containers.png")
                self.logger.info("已保存页面截图: error_find_containers.png")
            except:
                pass
            return False
        except Exception as e:
            self.logger.error(f"获取所有URL时出错: {str(e)}")
            return False

    def navigate_to_episode_page(self, episode_url, timeout=30):
        """
        跳转至剧集页面并覆盖当前页
        :param episode_url: 剧集URL
        :param container_class: 验证页面存在的容器类名
        :param timeout: 超时时间（秒）
        :return: 如果导航并验证成功返回True，否则False
        """
        try:
            self.driver.get(episode_url)
            self.logger.info(f"已跳转至剧集页面: {episode_url}")
            
            # 等待基础DOM加载
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # 等待播放器核心组件就绪（避免等待整个播放器）
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".bpx-player-video-wrap"))
            )
            
            # 关键：等待播放器API可用
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return typeof window.__playinfo__ !== 'undefined'")
            )
            
            self.logger.info("播放器核心组件已加载")
            # 新增：等待三连按钮区域加载
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".toolbar-left"))
            )
            return True
        except TimeoutException:
            self.logger.warning("播放器加载超时，但继续操作")
            return True  # 即使超时也继续
        except Exception as e:
            self.logger.error(f"导航至剧集页面时出错: {str(e)}")
            return False
    def process_specific_episode(self, episode_index, delay=1.0, triple_action=False):
        """
        处理指定剧集 (跳转 + 执行操作)
        :param episode_index: 剧集索引 (0-based)
        :param delay: 操作后延迟 (秒)
        :param like_function: 点赞函数 (可选)
        :return: 是否成功处理
        """
        try:
            self.logger.info(f"开始处理第 {episode_index+1} 集...")
            
            # 检查剧集URL是否存在
            if not hasattr(self, 'episode_urls') or not self.episode_urls:
                self.logger.error("未找到剧集URL列表，请先调用get_all_episodes_urls")
                return False
            
            # 检查索引是否有效
            if episode_index < 0 or episode_index >= len(self.episode_urls):
                self.logger.error(f"无效剧集索引: {episode_index}，有效范围: 0-{len(self.episode_urls)-1}")
                return False
            
            # 获取目标URL
            target_url = self.episode_urls[episode_index]
            self.logger.info(f"目标URL: {target_url}")
            
            # 导航到剧集页面
            if not self.navigate_to_episode_page(target_url):
                self.logger.error(f"跳转到第 {episode_index+1} 集失败")
                return False
            
            self.logger.info(f"成功进入第 {episode_index+1} 集页面")
            
            # 添加短暂等待确保页面加载
            time.sleep(0.5)
            
            # 执行一键三连操作
            if triple_action:
                # 创建操作实例
                triple_operator = BilibiliTripleAction(self.driver)
                
                # 使用长按方式
                triple_result = triple_operator.check_and_operate()
                if triple_result == 1:
                    self.logger.info("成功执行一键三连操作")
                elif triple_result == 0:
                    self.logger.info("该剧集已三连，无需操作")
                else:
                    self.logger.warning("一键三连操作失败")
            
            # 添加操作后延迟
            if delay > 0:
                self.logger.info(f"等待 {delay} 秒...")
                time.sleep(delay)
            
            self.logger.info(f"第 {episode_index+1} 集处理完成")
            return True
            
        except Exception as e:
            self.logger.error(f"处理剧集时出错: {str(e)}")
            return False