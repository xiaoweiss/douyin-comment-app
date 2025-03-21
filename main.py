import asyncio
import os
import time
import random
from playwright.async_api import async_playwright

# 基础配置
DOUYIN_URL = "https://www.douyin.com"
LIVE_URL = "https://live.douyin.com/990739075899"  # 特定的直播间链接
USER_DATA_DIR = "./browser_profile"  # 恢复原来的数据目录路径

# 评论列表
COMMENTS = [
    "广州12岁男孩推荐多少天   ",
    "基地在哪",
    "多少岁合适",
    "孩子多少岁可以参加",
    "填写了 深圳 8岁 女孩",
    "7岁男孩不敢一个人睡觉"
]


async def main():
    """主程序入口"""
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        # 简化浏览器参数，提高兼容性
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800}
        )

        try:
            # 获取或创建页面
            if browser.pages:
                page = browser.pages[0]
            else:
                page = await browser.new_page()

            # 反检测
            await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
            """)

            # 访问抖音前先检查Cookie
            cookies = await browser.cookies()
            has_session = any(c['name'] == 'sessionid' for c in cookies)

            if has_session:
                print("✅ 检测到历史会话Cookie，直接进入直播间")
            else:
                print("🔑 未检测到登录信息，需要登录")
                # 访问抖音主页
                await page.goto(DOUYIN_URL, wait_until="domcontentloaded", timeout=30000)
                await login(page)

            # 直接进入直播间
            print(f"🚀 正在进入直播间: {LIVE_URL}")
            try:
                await page.goto(LIVE_URL, wait_until="domcontentloaded", timeout=30000)
                print("✅ 直播间页面已加载")
                await asyncio.sleep(5)  # 等待直播间加载
            except Exception as e:
                print(f"⚠️ 直播间加载异常，但继续执行: {e}")

            # 处理可能的弹窗
            await handle_popups(page)

            # 发送评论
            await send_comments(page)
            
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            # 保持浏览器打开
            print("程序运行完成，保持浏览器打开")
            input("按Enter键退出...")
            await browser.close()


async def is_logged_in(page):
    """优化登录状态检测"""
    try:
        # 双重验证机制
        # 1. 检查用户信息元素（带重试）
        await page.wait_for_selector('div[data-e2e="user-info"]', state="visible", timeout=5000)
        # 2. 检查登录按钮是否消失
        login_btn = await page.query_selector('div[data-e2e="login-btn"]:visible')
        # 3. 验证Cookie有效性
        cookies = await page.context.cookies()
        session_cookie = next((c for c in cookies if c['name'] == 'sessionid'), None)

        return login_btn is None and session_cookie is not None
    except Exception as e:
        print(f"登录检测异常: {e}")
        return False


async def login(page):
    """处理登录流程（优化版）"""
    try:
        # 确保页面在抖音主站
        if "douyin.com" not in page.url:
            await page.goto(DOUYIN_URL, wait_until="domcontentloaded", timeout=30000)

        # 点击登录按钮
        login_btn = await page.wait_for_selector('div[data-e2e="login-btn"]', timeout=10000)
        await login_btn.click()
        print("✅ 已点击登录按钮")

        # 切换到二维码登录
        try:
            qr_btn = await page.wait_for_selector('div.qrcode-login', timeout=5000)
            await qr_btn.click()
            print("✅ 已切换二维码登录")
        except:
            print("⚠️ 未找到二维码登录选项，继续其他方式")

        # 等待二维码加载
        await page.wait_for_selector('canvas#qrcodeCanvas', timeout=15000)
        print("✅ 请使用抖音APP扫码")

        # 等待登录完成（带超时）
        start_time = time.time()
        while time.time() - start_time < 120:  # 2分钟超时
            if await is_logged_in(page):
                print("✅ 登录成功")
                return True
            await asyncio.sleep(3)
        print("⏰ 登录超时")
        return False
        
    except Exception as e:
        print(f"❌ 登录失败: {str(e)}")
        return False


async def handle_popups(page):
    """处理直播间可能出现的弹窗"""
    try:
        # 关闭礼物弹窗
        gift_close = await page.query_selector('div.webcast-gift-modal button.close')
        if gift_close:
            await gift_close.click()
            print("已关闭礼物弹窗")

        # 关闭关注提示
        follow_close = await page.query_selector('div.follow-guide-container .close-btn')
        if follow_close:
            await follow_close.click()
            print("已关闭关注提示")
    except Exception as e:
        print(f"处理弹窗出错: {e}")


async def send_comments(page):
    """发送评论"""
    try:
        print("🔍 正在查找评论框...")

        # 截图帮助调试
        await page.screenshot(path="live_room.png")
        print("📸 已保存页面截图到live_room.png")

        # 使用正确的选择器
        comment_box = await page.wait_for_selector(
            'textarea.webcast-chatroom___textarea[placeholder="与大家互动一下..."]',
            state="visible",
            timeout=15000)
        print("✅ 找到评论框")

        if not comment_box:
            print("❌ 未找到任何评论框")
            return

        print("🚀 自动开始发送评论...")
        # 无限循环发送评论，直到程序被手动停止
        while True:
            # 随机选择评论
            comment = random.choice(COMMENTS)

            # 点击评论框
            await comment_box.click()

            # 输入评论
            await page.fill('textarea.webcast-chatroom___textarea', "")  # 先清空
            await page.type('textarea.webcast-chatroom___textarea', comment, delay=100)  # 模拟真人输入

            # 点击发送按钮或按回车
            send_btn = await page.query_selector('.webcast-chatroom___send-btn')
            if send_btn:
                await send_btn.click()
                print("✅ 通过按钮发送")
            else:
                await page.keyboard.press("Enter")
                print("✅ 通过回车键发送")

            print(f"📨 已发送评论: {comment}")

            # 随机等待10-100秒
            wait_time = random.randint(10, 100)  # 增加上限，降低风险
            print(f"⏱️ 等待{wait_time}秒后发送下一条...")
            await asyncio.sleep(wait_time)
        
    except Exception as e:
        print(f"发送评论出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())