import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import os
import time
import random
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

class DouyinCommentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("抖音直播评论助手")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 变量
        self.live_url = tk.StringVar()
        self.min_interval = tk.IntVar(value=1)
        self.max_interval = tk.IntVar(value=2)
        self.comments = []
        self.is_running = False
        self.browser = None
        self.page = None
        self.start_date = tk.StringVar(value=time.strftime("%Y-%m-%d"))
        self.start_time = tk.StringVar(value="14:00")
        self.end_time = tk.StringVar(value="16:00")
        self.last_comment = None  # 新增最后发送的评论记录
        
        # 创建界面
        self.create_widgets()
        
        # 默认评论
        default_comments = [
            "我孩子周成去年没参加，说了全额退定金没给退，招生老师一直不理人，大家不要相信！"
        ]
        for comment in default_comments:
            self.add_comment_to_list(comment)
    
    def create_widgets(self):
        # 创建标签页
        tab_control = ttk.Notebook(self.root)
        
        # 主设置标签页
        main_tab = ttk.Frame(tab_control)
        tab_control.add(main_tab, text="主设置")
        
        # 评论管理标签页
        comment_tab = ttk.Frame(tab_control)
        tab_control.add(comment_tab, text="评论管理")
        
        # 日志标签页
        log_tab = ttk.Frame(tab_control)
        tab_control.add(log_tab, text="运行日志")
        
        tab_control.pack(expand=1, fill="both")
        
        # === 主设置标签页 ===
        main_frame = ttk.LabelFrame(main_tab, text="基本设置")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 直播间链接
        ttk.Label(main_frame, text="直播间链接:").grid(column=0, row=0, padx=10, pady=10, sticky=tk.W)
        ttk.Entry(main_frame, width=50, textvariable=self.live_url).grid(column=1, row=0, padx=10, pady=10, sticky=tk.W)
        
        # 发送间隔
        ttk.Label(main_frame, text="发送间隔(秒):").grid(column=0, row=1, padx=10, pady=10, sticky=tk.W)
        interval_frame = ttk.Frame(main_frame)
        interval_frame.grid(column=1, row=1, padx=10, pady=10, sticky=tk.W)
        
        ttk.Label(interval_frame, text="最小:").pack(side=tk.LEFT)
        ttk.Spinbox(interval_frame, from_=5, to=60, width=5, textvariable=self.min_interval).pack(side=tk.LEFT, padx=5)
        ttk.Label(interval_frame, text="最大:").pack(side=tk.LEFT, padx=10)
        ttk.Spinbox(interval_frame, from_=10, to=120, width=5, textvariable=self.max_interval).pack(side=tk.LEFT, padx=5)
        
        # 时间设置
        time_frame = ttk.LabelFrame(main_frame, text="运行时间设置")
        time_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=10, sticky="ew")
        
        # 日期选择
        ttk.Label(time_frame, text="运行日期:").pack(side=tk.LEFT, padx=5)
        self.date_entry = ttk.Entry(time_frame, textvariable=self.start_date, width=10)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        
        # 时间选择
        ttk.Label(time_frame, text="开始时间:").pack(side=tk.LEFT, padx=5)
        self.start_cb = ttk.Combobox(time_frame, textvariable=self.start_time, 
                                   values=[f"{h:02d}:{m:02d}" for h in range(24) for m in range(0,60,5)], 
                                   width=5)
        self.start_cb.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(time_frame, text="结束时间:").pack(side=tk.LEFT, padx=5)
        self.end_cb = ttk.Combobox(time_frame, textvariable=self.end_time, 
                                 values=[f"{h:02d}:{m:02d}" for h in range(24) for m in range(0,60,5)], 
                                 width=5)
        self.end_cb.pack(side=tk.LEFT, padx=5)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(column=0, row=3, columnspan=2, pady=20)
        
        self.start_button = ttk.Button(control_frame, text="启动", command=self.start_bot)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # === 评论管理标签页 ===
        comment_frame = ttk.LabelFrame(comment_tab, text="评论列表")
        comment_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 评论输入
        input_frame = ttk.Frame(comment_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.comment_input = ttk.Entry(input_frame, width=50)
        self.comment_input.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(input_frame, text="添加", command=self.add_comment).pack(side=tk.LEFT, padx=5)
        
        # 评论列表
        list_frame = ttk.Frame(comment_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.comment_listbox = tk.Listbox(list_frame, width=70, height=15)
        self.comment_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.comment_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.comment_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 评论操作按钮
        button_frame = ttk.Frame(comment_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="删除选中", command=self.delete_comment).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空所有", command=self.clear_comments).pack(side=tk.LEFT, padx=5)
        
        # 文件导入按钮
        file_frame = ttk.Frame(comment_frame)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(file_frame, text="导入评论文件", command=self.import_comments).pack(side=tk.LEFT)
        
        # === 日志标签页 ===
        log_frame = ttk.LabelFrame(log_tab, text="运行日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
    
    def add_comment(self):
        comment = self.comment_input.get().strip()
        if comment:
            self.add_comment_to_list(comment)
            self.comment_input.delete(0, tk.END)
    
    def add_comment_to_list(self, comment):
        if comment not in self.comments:
            self.comments.append(comment)
            self.comment_listbox.insert(tk.END, comment)
    
    def delete_comment(self):
        selected = self.comment_listbox.curselection()
        if selected:
            index = selected[0]
            self.comment_listbox.delete(index)
            del self.comments[index]
    
    def clear_comments(self):
        self.comment_listbox.delete(0, tk.END)
        self.comments.clear()
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_bot(self):
        if not self.live_url.get():
            messagebox.showerror("错误", "请输入直播间链接")
            return
        
        if not self.comments:
            messagebox.showerror("错误", "请添加至少一条评论")
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 启动机器人线程
        threading.Thread(target=self.run_bot_thread, daemon=True).start()
        self.log("启动评论助手...")
    
    def stop_bot(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("正在停止评论助手...")
    
    def run_bot_thread(self):
        asyncio.run(self.run_bot())
    
    async def run_bot(self):
        # 检查运行时间
        if not self.check_runtime():
            self.log("当前不在设定的运行时间段内，程序退出")
            return
        
        self.log(f"准备进入直播间: {self.live_url.get()}")
        
        # 用户数据目录
        user_data_dir = "./browser_profile"
        os.makedirs(user_data_dir, exist_ok=True)
        
        try:
            async with async_playwright() as p:
                self.log("正在连接系统浏览器...")
                try:
                    # 连接到已存在的Chrome实例
                    browser = await p.chromium.connect_over_cdp(
                        "http://localhost:9222",
                        timeout=30000,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                        }
                    )
                    self.log("✅ 已连接到系统浏览器")
                except Exception as e:
                    self.log(f"连接浏览器失败: {str(e)}")
                    self.log("正在尝试启动新浏览器...")
                    browser = await p.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="chrome",
                        headless=False,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--remote-debugging-port=9222"
                        ],
                        viewport={"width": 1280, "height": 800}
                    )
                
                # 获取或创建页面
                page = browser.pages[0] if browser.pages else await browser.new_page()
                
                # 反检测
                await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
                """)
                
                # 检查Cookie
                cookies = await browser.cookies()
                has_session = any(c['name'] == 'sessionid' for c in cookies)
                
                if has_session:
                    self.log("检测到历史会话Cookie")
                else:
                    self.log("未检测到登录信息，需要登录")
                    await page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=30000)
                    await self.handle_login(page)
                
                # 进入直播间
                self.log(f"正在进入直播间...")
                try:
                    await page.goto(self.live_url.get(), wait_until="domcontentloaded", timeout=30000)
                    self.log("直播间页面已加载")
                    await asyncio.sleep(5)
                except Exception as e:
                    self.log(f"直播间加载异常: {e}")
                
                # 处理弹窗
                await self.handle_popups(page)
                
                # 发送评论
                await self.send_comments(page)
                
                # 完成后关闭浏览器
                if not self.is_running:
                    await browser.close()
                    self.log("浏览器已关闭")
        
        except Exception as e:
            self.log(f"发生错误: {e}")
            self.is_running = False
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
    
    async def handle_login(self, page):
        self.log("等待用户登录...")
        # 登录逻辑与原脚本相同
        # ...
    
    async def handle_popups(self, page):
        try:
            # 关闭礼物弹窗
            gift_close = await page.query_selector('div.webcast-gift-modal button.close')
            if gift_close:
                await gift_close.click()
                self.log("已关闭礼物弹窗")
            
            # 关闭关注提示
            follow_close = await page.query_selector('div.follow-guide-container .close-btn')
            if follow_close:
                await follow_close.click()
                self.log("已关闭关注提示")
        except Exception as e:
            self.log(f"处理弹窗出错: {e}")
    
    async def send_comments(self, page):
        try:
            self.log("正在查找评论框...")
            
            comment_box = await page.wait_for_selector(
                'textarea.webcast-chatroom___textarea[placeholder="与大家互动一下..."]', 
                state="visible", 
                timeout=15000
            )
            self.log("找到评论框")
            
            if not comment_box:
                self.log("未找到评论框")
                return
            
            self.log("开始发送评论...")
            
            while self.is_running:
                # 检查是否被禁言
                is_muted = await self.check_muted_status(page)
                if is_muted:
                    self.log("检测到被禁言，刷新页面...")
                    await page.reload()
                    await asyncio.sleep(5)
                    return await self.send_comments(page)
                
                # 优化评论选择
                if len(self.comments) > 1:
                    candidates = [c for c in self.comments if c != self.last_comment]
                    comment = random.choice(candidates)
                else:
                    comment = random.choice(self.comments)
                
                self.last_comment = comment
                
                # 输入评论
                await comment_box.click()
                await page.fill('textarea.webcast-chatroom___textarea', "")
                await page.type('textarea.webcast-chatroom___textarea', comment, delay=100)
                
                # 点击发送按钮或按回车
                send_btn = await page.query_selector('.webcast-chatroom___send-btn')
                if send_btn:
                    await send_btn.click()
                    self.log(f"已发送评论: {comment} (按钮)")
                else:
                    await page.keyboard.press("Enter")
                    self.log(f"已发送评论: {comment} (回车)")
                
                # 随机等待
                wait_time = random.randint(self.min_interval.get(), self.max_interval.get())
                self.log(f"等待{wait_time}秒后发送下一条...")
                
                # 分段等待，以便能够及时响应停止命令
                for _ in range(wait_time):
                    if not self.is_running:
                        break
                    await asyncio.sleep(1)
            
            self.log("评论发送已停止")
            
        except Exception as e:
            self.log(f"发送评论出错: {e}")
            self.is_running = False
            self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))

    async def check_muted_status(self, page):
        """检查是否被禁言"""
        try:
            # 查找禁言提示元素
            mute_warning = await page.query_selector('div.mute-warning:visible')
            if mute_warning:
                return True
            
            # 检查发送按钮是否被禁用
            send_btn = await page.query_selector('.webcast-chatroom___send-btn:disabled')
            if send_btn:
                return True
            
            # 检查输入框是否被禁用
            comment_box = await page.query_selector('textarea.webcast-chatroom___textarea[disabled]')
            if comment_box:
                return True
            
            return False
        except Exception as e:
            self.log(f"禁言检查出错: {e}")
            return False

    def check_runtime(self):
        try:
            now = datetime.now()
            run_date = datetime.strptime(self.start_date.get(), "%Y-%m-%d").date()
            start_time = datetime.strptime(self.start_time.get(), "%H:%M").time()
            end_time = datetime.strptime(self.end_time.get(), "%H:%M").time()

            # 创建带日期的时间对象
            start_dt = datetime.combine(run_date, start_time)
            end_dt = datetime.combine(run_date, end_time)

            # 处理跨天情况
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            return start_dt <= now <= end_dt
        except Exception as e:
            self.log(f"时间格式错误: {str(e)}")
            return False

    def import_comments(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        comment = line.strip()
                        if comment:
                            self.add_comment_to_list(comment)
                self.log(f"成功导入评论文件: {file_path}")
            except Exception as e:
                self.log(f"文件导入失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DouyinCommentApp(root)
    root.mainloop() 