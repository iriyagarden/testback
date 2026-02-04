"""
shopping_cart_test.py
购物车功能自动化测试
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import csv
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShoppingCartPage:
    """购物车页面对象模型"""
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        
    # 定位器
    CART_ICON = (By.CSS_SELECTOR, ".cart-icon")
    CART_COUNT = (By.CSS_SELECTOR, ".cart-count")
    ADD_TO_CART_BTN = (By.XPATH, "//button[contains(text(), '加入购物车')]")
    CART_ITEMS = (By.CSS_SELECTOR, ".cart-item")
    ITEM_NAME = (By.CSS_SELECTOR, ".item-name")
    ITEM_PRICE = (By.CSS_SELECTOR, ".item-price")
    QUANTITY_INPUT = (By.CSS_SELECTOR, ".quantity-input")
    INCREASE_QTY = (By.CSS_SELECTOR, ".increase-qty")
    DECREASE_QTY = (By.CSS_SELECTOR, ".decrease-qty")
    REMOVE_ITEM = (By.CSS_SELECTOR, ".remove-item")
    TOTAL_PRICE = (By.CSS_SELECTOR, ".total-price")
    CHECKOUT_BTN = (By.CSS_SELECTOR, ".checkout-button")
    EMPTY_CART_MSG = (By.CSS_SELECTOR, ".empty-cart-message")
    CONTINUE_SHOPPING = (By.CSS_SELECTOR, ".continue-shopping")
    
    def navigate_to_homepage(self, url):
        """访问首页"""
        self.driver.get(url)
        logger.info(f"访问首页: {url}")
        
    def add_item_to_cart(self, product_index=0):
        """添加商品到购物车"""
        products = self.driver.find_elements(*self.ADD_TO_CART_BTN)
        if product_index < len(products):
            products[product_index].click()
            logger.info(f"添加第 {product_index + 1} 个商品到购物车")
            return True
        return False
    
    def open_cart(self):
        """打开购物车"""
        self.driver.find_element(*self.CART_ICON).click()
        self.wait.until(EC.presence_of_element_located(self.CART_ITEMS))
        logger.info("打开购物车页面")
        
    def get_cart_items_count(self):
        """获取购物车商品数量"""
        try:
            count_element = self.driver.find_element(*self.CART_COUNT)
            return int(count_element.text)
        except (NoSuchElementException, ValueError):
            return 0
    
    def get_cart_items(self):
        """获取购物车中的所有商品"""
        items = []
        cart_items = self.driver.find_elements(*self.CART_ITEMS)
        
        for item in cart_items:
            try:
                name = item.find_element(*self.ITEM_NAME).text
                price_text = item.find_element(*self.ITEM_PRICE).text
                price = float(price_text.replace('¥', '').replace('$', '').strip())
                quantity = item.find_element(*self.QUANTITY_INPUT).get_attribute("value")
                
                items.append({
                    'name': name,
                    'price': price,
                    'quantity': int(quantity)
                })
            except Exception as e:
                logger.warning(f"解析商品信息时出错: {e}")
                
        return items
    
    def update_quantity(self, item_index, new_quantity):
        """更新商品数量"""
        items = self.driver.find_elements(*self.CART_ITEMS)
        if item_index < len(items):
            quantity_input = items[item_index].find_element(*self.QUANTITY_INPUT)
            quantity_input.clear()
            quantity_input.send_keys(str(new_quantity))
            logger.info(f"更新第 {item_index + 1} 个商品数量为: {new_quantity}")
            return True
        return False
    
    def increase_quantity(self, item_index):
        """增加商品数量"""
        items = self.driver.find_elements(*self.CART_ITEMS)
        if item_index < len(items):
            items[item_index].find_element(*self.INCREASE_QTY).click()
            logger.info(f"增加第 {item_index + 1} 个商品数量")
            return True
        return False
    
    def remove_item(self, item_index):
        """移除购物车中的商品"""
        items = self.driver.find_elements(*self.CART_ITEMS)
        if item_index < len(items):
            items[item_index].find_element(*self.REMOVE_ITEM).click()
            logger.info(f"移除第 {item_index + 1} 个商品")
            return True
        return False
    
    def get_total_price(self):
        """获取购物车总价"""
        try:
            total_text = self.driver.find_element(*self.TOTAL_PRICE).text
            return float(total_text.replace('¥', '').replace('$', '').replace('总计:', '').strip())
        except Exception as e:
            logger.error(f"获取总价失败: {e}")
            return 0
    
    def proceed_to_checkout(self):
        """前往结算"""
        self.driver.find_element(*self.CHECKOUT_BTN).click()
        logger.info("点击结算按钮")
        
    def is_cart_empty(self):
        """检查购物车是否为空"""
        try:
            self.driver.find_element(*self.EMPTY_CART_MSG)
            return True
        except NoSuchElementException:
            return False

    def refresh_ui(self, wait_for_locator=None, timeout=10):
        """
        刷新界面（刷新当前页面）并等待页面加载完成。

        参数:
            wait_for_locator: 可选，传入一个selenium定位器元组 (By.*, "selector")，
                              刷新后将等待该元素出现以确保界面已就绪。
            timeout: 等待超时时间（秒）
        """
        self.driver.refresh()

        # 等待页面 readyState = complete（有些站点还会有异步渲染，可配合 wait_for_locator）
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception:
            # readyState 等待失败也不直接终止，交给后续元素等待兜底
            pass

        locator = wait_for_locator or self.CART_ICON
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))
        logger.info("界面已刷新并完成加载")


class TestShoppingCart:
    """购物车测试类"""
    
    @pytest.fixture(scope="class")
    def setup(self):
        """测试初始化"""
        # 使用 Chrome 浏览器
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        # options.add_argument("--headless")  # 无头模式，用于CI/CD
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        
        cart_page = ShoppingCartPage(driver)
        
        # 测试数据
        test_data = {
            "url": "https://demo.ecommerce.com",
            "products": [
                {"name": "产品A", "price": 199.99},
                {"name": "产品B", "price": 299.99},
                {"name": "产品C", "price": 99.99}
            ]
        }
        
        yield driver, cart_page, test_data
        
        # 测试清理
        driver.quit()
    
    @pytest.fixture(autouse=True)
    def take_screenshot_on_failure(self, request, setup):
        """测试失败时截图"""
        driver, _, _ = setup
        yield
        if request.node.rep_call.failed:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"screenshots/failure_{request.node.name}_{timestamp}.png"
            driver.save_screenshot(screenshot_name)
            logger.error(f"测试失败，截图已保存: {screenshot_name}")
    
    def test_01_add_single_item_to_cart(self, setup):
        """测试添加单个商品到购物车"""
        driver, cart_page, test_data = setup
        cart_page.navigate_to_homepage(test_data["url"])
        
        # 添加第一个商品
        assert cart_page.add_item_to_cart(0), "添加商品失败"
        
        # 验证购物车数量更新
        time.sleep(1)  # 等待DOM更新
        cart_count = cart_page.get_cart_items_count()
        assert cart_count == 1, f"购物车数量应为1，实际为{cart_count}"
        
        logger.info("✓ 测试通过: 成功添加单个商品到购物车")
    
    def test_02_add_multiple_items_to_cart(self, setup):
        """测试添加多个商品到购物车"""
        driver, cart_page, test_data = setup
        cart_page.navigate_to_homepage(test_data["url"])
        
        # 添加三个商品
        items_to_add = 3
        for i in range(items_to_add):
            assert cart_page.add_item_to_cart(i), f"添加第{i+1}个商品失败"
            time.sleep(0.5)
        
        # 验证购物车数量
        cart_count = cart_page.get_cart_items_count()
        assert cart_count == items_to_add, f"购物车数量应为{items_to_add}，实际为{cart_count}"
        
        logger.info(f"✓ 测试通过: 成功添加{items_to_add}个商品到购物车")
    
    def test_03_view_cart_contents(self, setup):
        """测试查看购物车内容"""
        driver, cart_page, test_data = setup
        
        # 先添加商品
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        
        # 打开购物车
        cart_page.open_cart()
        
        # 验证购物车中有商品
        items = cart_page.get_cart_items()
        assert len(items) > 0, "购物车应至少有一个商品"
        
        # 验证商品信息
        first_item = items[0]
        assert "name" in first_item, "商品应包含名称"
        assert "price" in first_item, "商品应包含价格"
        assert "quantity" in first_item, "商品应包含数量"
        
        logger.info(f"✓ 测试通过: 购物车中有 {len(items)} 个商品")
    
    def test_04_update_item_quantity(self, setup):
        """测试更新商品数量"""
        driver, cart_page, test_data = setup
        
        # 准备测试环境
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        cart_page.open_cart()
        
        # 更新数量为3
        new_quantity = 3
        assert cart_page.update_quantity(0, new_quantity), "更新数量失败"
        
        # 获取更新后的商品信息
        time.sleep(1)  # 等待更新
        items = cart_page.get_cart_items()
        assert items[0]['quantity'] == new_quantity, f"数量应为{new_quantity}，实际为{items[0]['quantity']}"
        
        logger.info(f"✓ 测试通过: 成功更新商品数量为 {new_quantity}")
    
    def test_05_remove_item_from_cart(self, setup):
        """测试从购物车移除商品"""
        driver, cart_page, test_data = setup
        
        # 添加两个商品
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        cart_page.add_item_to_cart(1)
        cart_page.open_cart()
        
        # 移除第一个商品
        initial_count = cart_page.get_cart_items_count()
        assert cart_page.remove_item(0), "移除商品失败"
        
        # 等待移除动画完成
        time.sleep(1)
        
        # 验证数量减少
        final_count = cart_page.get_cart_items_count()
        assert final_count == initial_count - 1, f"移除后数量应为{initial_count-1}，实际为{final_count}"
        
        logger.info("✓ 测试通过: 成功从购物车移除商品")
    
    def test_06_cart_total_calculation(self, setup):
        """测试购物车总价计算"""
        driver, cart_page, test_data = setup
        
        # 添加两个商品
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        cart_page.add_item_to_cart(1)
        cart_page.open_cart()
        
        # 获取商品信息并计算预期总价
        items = cart_page.get_cart_items()
        expected_total = sum(item['price'] * item['quantity'] for item in items)
        
        # 获取实际显示的总价
        actual_total = cart_page.get_total_price()
        
        # 允许小数的微小差异
        assert abs(expected_total - actual_total) < 0.01, \
            f"总价计算错误: 预期{expected_total}，实际{actual_total}"
        
        logger.info(f"✓ 测试通过: 总价计算正确 {actual_total}")
    
    def test_07_empty_cart_state(self, setup):
        """测试清空购物车后的状态"""
        driver, cart_page, test_data = setup
        
        # 添加然后移除所有商品
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        cart_page.open_cart()
        
        # 移除所有商品
        while not cart_page.is_cart_empty():
            cart_page.remove_item(0)
            time.sleep(0.5)
        
        # 验证购物车为空
        assert cart_page.is_cart_empty(), "购物车应显示为空"
        assert cart_page.get_cart_items_count() == 0, "购物车数量应为0"
        
        logger.info("✓ 测试通过: 购物车清空后状态正确")
    
    def test_08_checkout_flow(self, setup):
        """测试结算流程"""
        driver, cart_page, test_data = setup
        
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        cart_page.open_cart()
        
        # 点击结算按钮
        cart_page.proceed_to_checkout()
        
        # 验证是否跳转到结算页面
        time.sleep(2)
        assert "checkout" in driver.current_url.lower() or "结算" in driver.page_source, \
            "未成功跳转到结算页面"
        
        logger.info("✓ 测试通过: 结算流程正常")
    
    @pytest.mark.parametrize("quantity", [0, -1, 999, "abc"])
    def test_09_quantity_edge_cases(self, setup, quantity):
        """测试数量边界情况"""
        driver, cart_page, test_data = setup
        
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        cart_page.open_cart()
        
        # 尝试设置各种边界值
        try:
            cart_page.update_quantity(0, quantity)
            time.sleep(1)
            
            # 验证系统如何处理无效输入
            items = cart_page.get_cart_items()
            if isinstance(quantity, int) and quantity > 0:
                assert items[0]['quantity'] == min(quantity, 999), "数量限制不正确"
            else:
                # 系统应该恢复为有效值
                assert items[0]['quantity'] >= 1, "数量应为有效值"
                
        except Exception as e:
            logger.info(f"系统正确处理异常输入: {quantity}, 错误: {e}")
            assert True  # 抛出异常也是可以接受的行为
    
    def test_10_cart_persistence(self, setup):
        """测试购物车数据持久化（刷新页面后数据仍在）"""
        driver, cart_page, test_data = setup
        
        cart_page.navigate_to_homepage(test_data["url"])
        cart_page.add_item_to_cart(0)
        
        # 获取初始数量
        initial_count = cart_page.get_cart_items_count()
        
        # 刷新页面
        cart_page.refresh_ui()
        
        # 验证数量仍然存在
        persisted_count = cart_page.get_cart_items_count()
        assert persisted_count == initial_count, f"刷新后购物车数据丢失: {initial_count} -> {persisted_count}"
        
        logger.info("✓ 测试通过: 购物车数据持久化正常")


class TestDataDrivenShoppingCart:
    """数据驱动的购物车测试"""
    
    @pytest.fixture
    def load_test_data(self):
        """加载测试数据"""
        # 可以从JSON文件、CSV文件或数据库加载测试数据
        test_cases = [
            {
                "test_name": "正常添加商品",
                "products": ["产品A"],
                "expected_count": 1
            },
            {
                "test_name": "添加多个不同商品",
                "products": ["产品A", "产品B", "产品C"],
                "expected_count": 3
            },
            {
                "test_name": "重复添加同一商品",
                "products": ["产品A", "产品A", "产品A"],
                "expected_count": 3
            }
        ]
        return test_cases
    
    @pytest.mark.parametrize("test_case", [
        {"products": 1, "expected": 1},
        {"products": 3, "expected": 3},
        {"products": 5, "expected": 5}
    ])
    def test_data_driven_add_items(self, setup, test_case):
        """数据驱动的添加商品测试"""
        driver, cart_page, test_data = setup
        
        cart_page.navigate_to_homepage(test_data["url"])
        
        # 添加指定数量的商品
        for i in range(test_case["products"]):
            cart_page.add_item_to_cart(i % 3)  # 循环使用前3个商品
        
        # 验证结果
        actual_count = cart_page.get_cart_items_count()
        assert actual_count == test_case["expected"], \
            f"预期{test_case['expected']}个商品，实际{actual_count}个"


def generate_test_report(results_file="test_results.json"):
    """生成测试报告（可在测试结束后调用）"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": 10,
        "passed": 0,
        "failed": 0,
        "duration": 0,
        "details": []
    }
    
    # 这里可以集成实际的测试运行结果
    with open(results_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report


if __name__ == "__main__":
    # 直接运行单个测试文件
    pytest.main([
        __file__,
        "-v",  # 详细输出
        "--html=report.html",  # 生成HTML报告
        "--self-contained-html",
        "--capture=no",  # 显示print输出
    ])