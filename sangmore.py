import discord
from discord.ext import commands
import threading
import time
import re
import requests
import os
import random
import asyncio
import datetime
import json
from typing import Dict, Any, List

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================

os.system("cls" if os.name == "nt" else "clear")

LOGO = """
\033[1;32m
  ██████  ▄▄▄       ███▄    █   ▄████  ███▄ ▄███▓ ▒█████   ██▀███  ▓█████ 
▒██    ▒ ▒████▄     ██ ▀█   █  ██▒ ▀█▒▓██▒▀█▀ ██▒▒██▒  ██▒▓██ ▒ ██▒▓█   ▀ 
░ ▓██▄   ▒██  ▀█▄  ▓██  ▀█ ██▒▒██░▄▄▄░▓██    ▓██░▒██░  ██▒▓██ ░▄█ ▒▒███   
  ▒   ██▒░██▄▄▄▄██ ▓██▒  ▐▌██▒░▓█  ██▓▒██    ▒██ ▒██   ██░▒██▀▀█▄  ▒▓█  ▄ 
▒██████▒▒ ▓█   ▓██▒▒██░   ▓██░░▒▓███▀▒▒██▒   ░██▒░ ████▓▒░░██▓ ▒██▒░▒████▒
▒ ▒▓▒ ▒ ░ ▒▒   ▓▒█░░ ▒░   ▒ ▒  ░▒   ▒ ░ ▒░   ░  ░░ ▒░▒░▒░ ░ ▒▓ ░▒▓░░░ ▒░ ░
░ ░▒  ░ ░  ▒   ▒▒ ░░ ░░   ░ ▒░  ░   ░ ░  ░      ░  ░ ▒ ▒░   ░▒ ░ ▒░ ░ ░  ░
░  ░  ░    ░   ▒      ░   ░ ░ ░ ░   ░ ░      ░   ░ ░ ░ ▒    ░░   ░    ░   
      ░        ░  ░           ░       ░              ░ ░     ░        ░  ░
\033[0m
"""
print(LOGO)
print("\033[1;36m[SYSTEM] KHỞI ĐỘNG HỆ THỐNG SANGMORE BOT...\033[0m")

TOKEN = input("\033[32m [SANGMORE BOT]\033[37m Nhập Token Bot Discord: ")
try:
    SANGMORE_ID_GOC = int(input("\033[32m [SANGMORE BOT]\033[37m Nhập ID Admin Gốc: "))
except ValueError:
    print("ID phải là số! Đang thoát...")
    exit()

# Danh sách admin phụ
sangmore_admins = []
start_time = datetime.datetime.utcnow()

# Màu sắc chủ đạo (Xanh lá Matrix / Hacker)
THEME_COLOR = 0x00FF00 
ERROR_COLOR = 0xFF0000

# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
]

# Khởi tạo Bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)
bot.remove_command('help') # Tắt lệnh help mặc định để tự làm

# ==========================================
# QUẢN LÝ TÁC VỤ (TASK MANAGER)
# ==========================================
class TaskManager:
    def __init__(self):
        # Cấu trúc: { (user_id, target_id): { 'thread': thread_obj, 'stop_event': event, 'start_time': time } }
        self.messenger_tasks = {} 
        # Cấu trúc: { channel_id: asyncio_task }
        self.discord_tasks = {}

    def is_running(self, user_id, target_id):
        return (user_id, target_id) in self.messenger_tasks

    def start_messenger_task(self, user_id, target_id, func, args):
        key = (user_id, target_id)
        if key in self.messenger_tasks:
            return False # Đang chạy rồi
        
        stop_event = threading.Event()
        # Thêm stop_event vào args để hàm worker có thể check
        new_args = list(args) + [stop_event]
        
        t = threading.Thread(target=func, args=new_args)
        t.daemon = True # Thread chết khi chương trình chính chết
        
        self.messenger_tasks[key] = {
            'thread': t,
            'stop_event': stop_event,
            'start_time': time.time(),
            'type': 'messenger'
        }
        t.start()
        return True

    def stop_messenger_task(self, user_id, target_id):
        key = (user_id, target_id)
        if key in self.messenger_tasks:
            # Kích hoạt cờ dừng
            self.messenger_tasks[key]['stop_event'].set()
            # Xóa khỏi danh sách quản lý
            del self.messenger_tasks[key]
            return True
        return False

    def add_discord_task(self, channel_id, task):
        self.discord_tasks[channel_id] = task

    def stop_discord_task(self, channel_id):
        if channel_id in self.discord_tasks:
            self.discord_tasks[channel_id].cancel()
            del self.discord_tasks[channel_id]
            return True
        return False

    def stop_all_discord_tasks(self):
        count = len(self.discord_tasks)
        for task in self.discord_tasks.values():
            task.cancel()
        self.discord_tasks.clear()
        return count

task_manager = TaskManager()

# ==========================================
# XỬ LÝ FACEBOOK (MESSENGER API)
# ==========================================
class MessengerAPI:
    def __init__(self, cookie):
        self.cookie = cookie
        self.headers = {
            "Cookie": self.cookie,
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.fb_dtsg = None
        self.user_id = self._get_uid()
        self._init_token()

    def _get_uid(self):
        try:
            return re.search(r"c_user=(\d+)", self.cookie).group(1)
        except AttributeError:
            raise Exception("Cookie lỗi: Không tìm thấy c_user")

    def _init_token(self):
        try:
            # Thử lấy từ mbasic trước cho nhẹ
            resp = requests.get("https://mbasic.facebook.com", headers=self.headers, timeout=10)
            fb_dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', resp.text)
            
            if not fb_dtsg:
                # Fallback sang www
                resp = requests.get("https://www.facebook.com", headers=self.headers, timeout=10)
                fb_dtsg = re.search(r'"token":"(.*?)"', resp.text)
            
            if fb_dtsg:
                self.fb_dtsg = fb_dtsg.group(1)
            else:
                raise Exception("Không lấy được fb_dtsg (Cookie có thể đã chết)")
        except Exception as e:
            raise Exception(f"Lỗi kết nối khởi tạo: {e}")

    def send_message(self, thread_id, content):
        if not self.fb_dtsg: return False
        
        timestamp = int(time.time() * 1000)
        url = "https://www.facebook.com/messaging/send/"
        
        payload = {
            "thread_fbid": thread_id,
            "body": content,
            "client": "mercury",
            "author": f"fbid:{self.user_id}",
            "timestamp": timestamp,
            "message_id": timestamp,
            "offline_threading_id": timestamp,
            "__user": self.user_id,
            "__a": "1",
            "fb_dtsg": self.fb_dtsg
        }
        
        try:
            r = requests.post(url, data=payload, headers=self.headers, timeout=10)
            if r.status_code == 200 and "error" not in r.text:
                return True
        except:
            pass
        return False

# ==========================================
# CÁC HÀM LOGIC CHẠY NGẦM (WORKERS)
# ==========================================
def worker_spam_mess(cookie, thread_id, message, delay, stop_event):
    try:
        api = MessengerAPI(cookie)
        print(f"[+] Bắt đầu spam {thread_id}")
        while not stop_event.is_set():
            api.send_message(thread_id, message)
            time.sleep(delay)
    except Exception as e:
        print(f"[-] Lỗi worker spam: {e}")

def worker_file_mess(cookie, thread_id, file_path, delay, stop_event):
    try:
        if not os.path.exists(file_path): return
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        
        if not lines: return
        api = MessengerAPI(cookie)
        
        i = 0
        while not stop_event.is_set():
            msg = lines[i % len(lines)]
            api.send_message(thread_id, msg)
            i += 1
            time.sleep(delay)
    except Exception as e:
        print(f"[-] Lỗi worker file: {e}")

# ==========================================
# GIAO DIỆN & MODAL DISCORD
# ==========================================
def create_embed(title, description, color=THEME_COLOR):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="System by Sangmore Bot | 2025")
    return embed

class InputModal(discord.ui.Modal):
    def __init__(self, title, callback_func, inputs):
        super().__init__(title=title)
        self.callback_func = callback_func
        self.inputs = inputs
        for label, placeholder in inputs:
            self.add_item(discord.ui.TextInput(label=label, placeholder=placeholder, required=True))

    async def on_submit(self, interaction: discord.Interaction):
        values = [item.value for item in self.children]
        await self.callback_func(interaction, *values)

class SangmoreMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.pages = self.build_pages()
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        # Nút chức năng của trang hiện tại
        current_data = self.pages[self.current_page]
        for label, style, callback, args in current_data['buttons']:
            btn = discord.ui.Button(label=label, style=style, emoji="🔹")
            # Gán callback thủ công để truyền args
            async def wrap_callback(interaction, cb=callback, a=args):
                if not check_perm(interaction.user.id):
                    return await interaction.response.send_message(embed=create_embed("🚫 Truy Cập Bị Từ Chối", "Bạn không phải Admin Sangmore.", ERROR_COLOR), ephemeral=True)
                if a: # Nếu cần nhập liệu
                    await interaction.response.send_modal(InputModal(f"Nhập liệu: {label}", cb, a))
                else:
                    await cb(interaction)
            btn.callback = wrap_callback
            self.add_item(btn)

        # Nút điều hướng
        if self.current_page > 0:
            btn_prev = discord.ui.Button(label="Trang Trước", style=discord.ButtonStyle.secondary, row=4)
            btn_prev.callback = self.prev_page
            self.add_item(btn_prev)
            
        if self.current_page < len(self.pages) - 1:
            btn_next = discord.ui.Button(label="Trang Sau", style=discord.ButtonStyle.secondary, row=4)
            btn_next.callback = self.next_page
            self.add_item(btn_next)

    async def prev_page(self, interaction):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page]['embed'], view=self)

    async def next_page(self, interaction):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page]['embed'], view=self)

    def build_pages(self):
        # Định nghĩa các trang và nút bấm
        p1_embed = create_embed("🛠 SANGMORE CONTROL PANEL - TRANG 1", "Các chức năng Spam Messenger & Hệ thống")
        p1_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1000/1000/sangmore_logo.png") # Thay link ảnh nếu muốn
        
        p2_embed = create_embed("⚔ SANGMORE CONTROL PANEL - TRANG 2", "Các chức năng Spam Discord & Tiện ích")
        
        return [
            {
                'embed': p1_embed,
                'buttons': [
                    ("Treo Ngôn (Mess)", discord.ButtonStyle.green, cmd_ngonmess, [("ID Box", "Nhập ID Box"), ("Cookie", "Cookie FB"), ("File Txt", "Tên file.txt"), ("Delay", "Số giây")]),
                    ("Nhây (Mess)", discord.ButtonStyle.blurple, cmd_nhaymess, [("ID Box", "Nhập ID Box"), ("Cookie", "Cookie FB"), ("Delay", "Số giây")]),
                    ("Chửi Idea (Mess)", discord.ButtonStyle.danger, cmd_ideamess, [("ID Box", "Nhập ID Box"), ("Cookie", "Cookie FB"), ("Delay", "Số giây")]),
                    ("Dừng Mess", discord.ButtonStyle.red, cmd_stopmess, [("ID Box", "Nhập ID Box cần dừng")]),
                    ("Check Uptime", discord.ButtonStyle.gray, cmd_uptime, None),
                ]
            },
            {
                'embed': p2_embed,
                'buttons': [
                    ("Spam Discord", discord.ButtonStyle.green, cmd_spamds, [("ID Kênh (cách nhau dấu phẩy)", "123, 456"), ("Nội dung", "Tin nhắn"), ("Delay", "Giây")]),
                    ("Nhây Discord", discord.ButtonStyle.blurple, cmd_nhayds, [("ID Kênh", "123, 456"), ("Delay", "Giây")]),
                    ("Dừng Discord", discord.ButtonStyle.red, cmd_stopds, None),
                    ("Thêm Admin", discord.ButtonStyle.primary, cmd_addadmin, [("User ID", "ID người dùng")]),
                    ("Xóa Admin", discord.ButtonStyle.secondary, cmd_deladmin, [("User ID", "ID người dùng")]),
                    ("Upload File", discord.ButtonStyle.success, cmd_uploadhelp, None)
                ]
            }
        ]

# ==========================================
# LOGIC XỬ LÝ LỆNH
# ==========================================

def check_perm(user_id):
    return user_id == SANGMORE_ID_GOC or user_id in sangmore_admins

async def cmd_ngonmess(interaction, idbox, cookie, filename, delay):
    try:
        delay = int(delay)
        real_filename = f"{interaction.user.id}_{filename}"
        if not os.path.exists(real_filename):
            return await interaction.response.send_message(embed=create_embed("⚠ Lỗi", f"Không tìm thấy file: {real_filename}", ERROR_COLOR), ephemeral=True)
        
        # Đọc nội dung file để gửi 1 nội dung lặp lại (theo logic cũ của bạn)
        with open(real_filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if task_manager.start_messenger_task(interaction.user.id, idbox, worker_spam_mess, (cookie, idbox, content, delay)):
            await interaction.response.send_message(embed=create_embed("✅ Đã Kích Hoạt", f"Đang treo ngôn vào Box: `{idbox}`\nDelay: `{delay}s`"), ephemeral=True)
        else:
            await interaction.response.send_message(embed=create_embed("⚠ Cảnh Báo", "Task này đang chạy rồi!", ERROR_COLOR), ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

async def cmd_nhaymess(interaction, idbox, cookie, delay):
    # Dùng file nhay.txt mặc định
    if task_manager.start_messenger_task(interaction.user.id, idbox, worker_file_mess, (cookie, idbox, "nhay.txt", int(delay))):
         await interaction.response.send_message(embed=create_embed("✅ Nhây Mess", f"Đang nhây vào Box: `{idbox}`"), ephemeral=True)
    else:
         await interaction.response.send_message(embed=create_embed("⚠ Lỗi", "Đang chạy rồi", ERROR_COLOR), ephemeral=True)

async def cmd_ideamess(interaction, idbox, cookie, delay):
    # Dùng file chui.txt mặc định
    if task_manager.start_messenger_task(interaction.user.id, idbox, worker_file_mess, (cookie, idbox, "chui.txt", int(delay))):
         await interaction.response.send_message(embed=create_embed("✅ Chửi Idea", f"Đang chửi vào Box: `{idbox}`"), ephemeral=True)
    else:
         await interaction.response.send_message(embed=create_embed("⚠ Lỗi", "Đang chạy rồi", ERROR_COLOR), ephemeral=True)

async def cmd_stopmess(interaction, idbox):
    if task_manager.stop_messenger_task(interaction.user.id, idbox):
        await interaction.response.send_message(embed=create_embed("🛑 Đã Dừng", f"Đã dừng tấn công Box: `{idbox}`"), ephemeral=True)
    else:
        await interaction.response.send_message(embed=create_embed("⚠ Lỗi", "Không tìm thấy tiến trình nào cho Box này.", ERROR_COLOR), ephemeral=True)

async def cmd_uptime(interaction):
    delta = datetime.datetime.utcnow() - start_time
    await interaction.response.send_message(embed=create_embed("⏰ Uptime", f"Bot đã hoạt động: `{str(delta).split('.')[0]}`"), ephemeral=True)

async def cmd_spamds(interaction, channels, content, delay):
    ids = [int(x.strip()) for x in channels.split(",") if x.strip().isdigit()]
    delay = int(delay)
    
    async def spam_logic(channel_id):
        try:
            ch = bot.get_channel(channel_id)
            if not ch: return
            while True:
                await ch.send(content)
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Lỗi spam DS: {e}")

    count = 0
    for cid in ids:
        task = bot.loop.create_task(spam_logic(cid))
        task_manager.add_discord_task(cid, task)
        count += 1
    
    await interaction.response.send_message(embed=create_embed("✅ Spam Discord", f"Đã kích hoạt spam trên {count} kênh."), ephemeral=True)

async def cmd_nhayds(interaction, channels, delay):
    ids = [int(x.strip()) for x in channels.split(",") if x.strip().isdigit()]
    delay = int(delay)
    
    if not os.path.exists("nhay.txt"):
        return await interaction.response.send_message("Thiếu file nhay.txt", ephemeral=True)
    
    with open("nhay.txt", "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    async def nhay_logic(channel_id):
        try:
            ch = bot.get_channel(channel_id)
            if not ch: return
            i = 0
            while True:
                await ch.send(lines[i % len(lines)])
                i += 1
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            pass

    count = 0
    for cid in ids:
        task = bot.loop.create_task(nhay_logic(cid))
        task_manager.add_discord_task(cid, task)
        count += 1

    await interaction.response.send_message(embed=create_embed("✅ Nhây Discord", f"Đã kích hoạt nhây trên {count} kênh."), ephemeral=True)

async def cmd_stopds(interaction):
    count = task_manager.stop_all_discord_tasks()
    await interaction.response.send_message(embed=create_embed("🛑 Dừng Discord", f"Đã hủy {count} tác vụ spam Discord."), ephemeral=True)

async def cmd_addadmin(interaction, uid):
    try:
        uid = int(uid)
        if uid not in sangmore_admins:
            sangmore_admins.append(uid)
            await interaction.response.send_message(f"Đã thêm {uid} vào Admin.", ephemeral=True)
        else:
            await interaction.response.send_message("Đã là admin rồi.", ephemeral=True)
    except:
        await interaction.response.send_message("ID lỗi.", ephemeral=True)

async def cmd_deladmin(interaction, uid):
    try:
        uid = int(uid)
        if uid in sangmore_admins:
            sangmore_admins.remove(uid)
            await interaction.response.send_message(f"Đã xóa {uid} khỏi Admin.", ephemeral=True)
        else:
            await interaction.response.send_message("Không tìm thấy ID.", ephemeral=True)
    except:
        await interaction.response.send_message("ID lỗi.", ephemeral=True)

async def cmd_uploadhelp(interaction):
    await interaction.response.send_message(embed=create_embed("Hướng Dẫn Upload", "Hãy dùng lệnh `.setngon` kèm theo file đính kèm để upload file ngôn."), ephemeral=True)

# ==========================================
# SỰ KIỆN BOT DISCORD
# ==========================================
@bot.event
async def on_ready():
    print(f"\033[1;32m[+] Bot {bot.user} đã sẵn sàng phục vụ Sangmore!\033[0m")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name="Sangmore System v2.0"))

@bot.command()
async def menu(ctx):
    view = SangmoreMenu()
    await ctx.send(embed=view.pages[0]['embed'], view=view)

@bot.command()
async def setngon(ctx):
    if not check_perm(ctx.author.id): return
    
    if not ctx.message.attachments:
        return await ctx.send(embed=create_embed("⚠ Lỗi", "Vui lòng đính kèm file .txt", ERROR_COLOR))
    
    file = ctx.message.attachments[0]
    if not file.filename.endswith(".txt"):
        return await ctx.send(embed=create_embed("⚠ Lỗi", "Chỉ nhận file .txt", ERROR_COLOR))
    
    save_name = f"{ctx.author.id}_{file.filename}"
    await file.save(save_name)
    await ctx.send(embed=create_embed("✅ Upload Thành Công", f"Đã lưu file: `{save_name}`"))

# Chạy Bot
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"\033[31m[!] Lỗi Token: {e}\033[0m")
