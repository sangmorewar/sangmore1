import discord
from discord.ext import commands, tasks
import random
import json
import os
import asyncio
import time

# --- CẤU HÌNH BOT ---
TOKEN = 'MTQ2Njk4MTkyMjQyNDA5ODgyOQ.GHJDwD.fb8BULiLN26vtxzZxu2Ue0efpiEL24LHSRN5Po' # <-- Dán Token vào đây
PREFIX = '#' 

# Cấu hình Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# File lưu dữ liệu
DB_FILE = "money.json"
ASSETS_FILE = "assets.json"

# --- BANNER (LINE ART) ---
BAUCUA_BANNER = """```ansi
[1;36m  ____   __   _  _    ___  _  _   __  [0m
[1;36m (  _ \ / _\ / )( \  / __)/ )( \ / _\ [0m
[1;35m  ) _ (/    \) \/ ( ( (__ ) \/ (/    \\[0m
[1;35m (____/\_/\_/\____/  \___)\____/\_/\_/[0m
```"""

# --- CẤU HÌNH BẤT ĐỘNG SẢN ---
# ID: {Tên, Giá Gốc, Icon}
REAL_ESTATE = {
    1: {"name": "Lều Tranh Ven Sông", "base_price": 50000, "icon": "⛺"},
    2: {"name": "Nhà Cấp 4", "base_price": 500000, "icon": "🏠"},
    3: {"name": "Chung Cư Cao Cấp", "base_price": 2000000, "icon": "🏢"},
    4: {"name": "Biệt Thự Vườn", "base_price": 10000000, "icon": "🏡"},
    5: {"name": "Khách Sạn 5 Sao", "base_price": 50000000, "icon": "🏨"},
    6: {"name": "Tòa Nhà Công Ty", "base_price": 200000000, "icon": "🌇"},
    7: {"name": "Sân Golf Quốc Tế", "base_price": 1000000000, "icon": "⛳"}
}

# Biến thị trường
market_prices = {} 
market_history = {} 

# Cấu hình Game Bầu Cua
GAME_ICONS = {
    "bau": {"emoji": "🍐", "name": "Bầu"},
    "cua": {"emoji": "🦀", "name": "Cua"},
    "tom": {"emoji": "🦐", "name": "Tôm"},
    "ca":  {"emoji": "🐟", "name": "Cá"},
    "ga":  {"emoji": "🐓", "name": "Gà"},
    "nai": {"emoji": "🦌", "name": "Nai"}
}

# --- DATABASE SYSTEM ---
def load_data():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

def get_balance(user_id):
    data = load_data()
    return data.get(str(user_id), 0)

def update_balance(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid not in data: data[uid] = 0
    data[uid] += amount
    save_data(data)

# Hàm xử lý tài sản
def load_assets():
    if not os.path.exists(ASSETS_FILE): return {}
    with open(ASSETS_FILE, "r") as f: return json.load(f)

def save_assets(data):
    with open(ASSETS_FILE, "w") as f: json.dump(data, f)

def add_asset(user_id, property_id):
    data = load_assets()
    uid = str(user_id)
    if uid not in data: data[uid] = []
    data[uid].append(property_id)
    save_assets(data)

def remove_asset(user_id, property_id):
    data = load_assets()
    uid = str(user_id)
    if uid not in data: return False
    if property_id in data[uid]:
        data[uid].remove(property_id) # Chỉ xóa 1 căn nếu có nhiều căn trùng nhau
        save_assets(data)
        return True
    return False

def get_user_assets(user_id):
    data = load_assets()
    return data.get(str(user_id), [])

# --- HỆ THỐNG CHỨNG KHOÁN ---
@tasks.loop(seconds=30)
async def update_market():
    global market_prices, market_history
    
    if not market_prices:
        for pid, info in REAL_ESTATE.items():
            market_prices[pid] = info["base_price"]
            market_history[pid] = [info["base_price"]] * 10

    for pid in market_prices:
        current = market_prices[pid]
        # Biến động mạnh hơn một chút: -15% đến +15%
        percent = random.uniform(-0.15, 0.15) 
        change = int(current * percent)
        new_price = current + change
        
        base = REAL_ESTATE[pid]["base_price"]
        # Giá tối thiểu 10% giá gốc, tối đa 300% giá gốc
        if new_price < base * 0.1: new_price = int(base * 0.1)
        if new_price > base * 3.0: new_price = int(base * 3.0)
        
        market_prices[pid] = new_price
        
        market_history[pid].append(new_price)
        if len(market_history[pid]) > 15:
            market_history[pid].pop(0)

# --- SỰ KIỆN KHỞI CHẠY ---
@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} đã sẵn sàng - Code by SangMore')
    if not update_market.is_running():
        update_market.start()
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}huongdan | Bầu Cua & BĐS"))

# --- MENU HƯỚNG DẪN ---
@bot.command(name="huongdan", aliases=["menu", "help"])
async def huongdan(ctx):
    embed = discord.Embed(title="📜 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG", color=discord.Color.from_rgb(47, 49, 54))
    
    embed.description = f"{BAUCUA_BANNER}\nChào mừng **{ctx.author.name}**."
    
    economy_text = (
        f"🔹 **`{PREFIX}daily`** : Nhận 10k/ngày.\n"
        f"🔹 **`{PREFIX}sodu`** : Xem tiền mặt.\n"
        f"🔹 **`{PREFIX}bo_thi`** : #bo_thi <@ten> <tiền> Chuyển tiền."
    )
    embed.add_field(name="💳 TÀI CHÍNH", value=economy_text, inline=True)

    game_text = (
        f"🔸 **`{PREFIX}baucua <con> <tiền>`**\n"
        f"   (bau, cua, tom, ca, ga, nai)"
    )
    embed.add_field(name="🎲 BẦU CUA", value=game_text, inline=True)

    bds_text = (
        f"📈 **`{PREFIX}thitruong`**\n   ╚ Xem giá nhà hiện tại (Live).\n"
        f"📊 **`{PREFIX}gianha <id>`**\n   ╚ Biểu đồ giá (Gõ số 1-7).\n"
        f"🏠 **`{PREFIX}muanha <id>`**\n   ╚ Mua nhà ở hoặc đầu tư.\n"
        f"💵 **`{PREFIX}banna <id>`**\n   ╚ Bán nhà chốt lời/cắt lỗ.\n"
        f"🎒 **`{PREFIX}taisan`**\n   ╚ Xem sổ đỏ của bạn."
    )
    embed.add_field(name="🏙️ CHỨNG KHOÁN BĐS", value=bds_text, inline=False)
    
    embed.set_footer(text="Code by SangMore") 
    await ctx.send(embed=embed)


# --- CÁC LỆNH BẤT ĐỘNG SẢN ---

@bot.command(name="thitruong", aliases=["market"])
async def thitruong(ctx):
    embed = discord.Embed(title="🏙️ SÀN GIAO DỊCH BẤT ĐỘNG SẢN", color=discord.Color.gold())
    embed.description = "Giá biến động liên tục. ID nằm ở đầu dòng (1, 2...)."
    
    for pid, info in REAL_ESTATE.items():
        curr_price = market_prices.get(pid, info["base_price"])
        base_price = info["base_price"]
        
        diff = curr_price - base_price
        percent = (diff / base_price) * 100
        
        if diff > 0:
            trend = f"📈 (+{percent:.1f}%)"
            status = "🔥"
        elif diff < 0:
            trend = f"📉 ({percent:.1f}%)"
            status = "❄️"
        else:
            trend = "━ (0%)"
            status = "⚖️"

        embed.add_field(
            name=f"#{pid}. {info['icon']} {info['name']}",
            value=f"Giá: **{curr_price:,}** | {trend}",
            inline=True
        )
    embed.set_footer(text=f"Dùng lệnh {PREFIX}gianha <id> để xem biểu đồ")
    await ctx.send(embed=embed)

@bot.command(name="gianha", aliases=["chart"])
async def gianha(ctx, property_id: int = None):
    if not property_id or property_id not in REAL_ESTATE:
        await ctx.send(f"⚠️ Nhập ID nhà (1-7). Xem `{PREFIX}thitruong`")
        return

    history = market_history.get(property_id, [])
    if not history: return await ctx.send("⏳ Đang cập nhật dữ liệu...")

    info = REAL_ESTATE[property_id]
    current_price = history[-1]
    
    # Vẽ biểu đồ ASCII
    chart_str = ""
    for i in range(1, len(history)):
        prev, curr = history[i-1], history[i]
        if curr > prev: chart_str += " / " 
        elif curr < prev: chart_str += " \\ "
        else: chart_str += " - "
            
    graph_display = f"""```ansi
[1;34m{info['icon']} {info['name'].upper()}[0m

Giá (VNĐ)
  ^
  |                   {chart_str} [1;31m⬤ ({current_price:,})[0m
  |         [1;33m////[0m     /
  |  [1;32m////[0m  /    \   /
__|_______________________> Thời gian
```"""

    embed = discord.Embed(color=discord.Color.dark_blue())
    embed.description = graph_display
    embed.set_footer(text="Code by SangMore")
    await ctx.send(embed=embed)

@bot.command(name="muanha", aliases=["buy"])
async def muanha(ctx, property_id: int = None):
    if not property_id or property_id not in REAL_ESTATE:
        return await ctx.send(f"⚠️ Nhập ID nhà (1-7). Xem `{PREFIX}thitruong`")

    price = market_prices.get(property_id, REAL_ESTATE[property_id]["base_price"])
    bal = get_balance(ctx.author.id)

    if bal < price:
        return await ctx.send(f"💸 **Không đủ tiền!**\nCần: {price:,} VNĐ\nCó: {bal:,} VNĐ")

    update_balance(ctx.author.id, -price)
    add_asset(ctx.author.id, property_id)
    
    embed = discord.Embed(title="✅ MUA NHÀ THÀNH CÔNG", color=discord.Color.green())
    embed.description = f"Bạn đã sở hữu **{REAL_ESTATE[property_id]['name']}**\nGiá mua: `{price:,} VNĐ`"
    embed.set_footer(text="Giữ nhà đợi giá lên rồi bán nhé!")
    await ctx.send(embed=embed)

@bot.command(name="banna", aliases=["sell"])
async def banna(ctx, property_id: int = None):
    # 1. Kiểm tra đầu vào
    if not property_id: 
        return await ctx.send(f"⚠️ Bạn muốn bán nhà nào? Gõ: `{PREFIX}banna <id>`")
    
    # 2. Kiểm tra sở hữu
    user_assets = get_user_assets(ctx.author.id)
    if property_id not in user_assets:
        return await ctx.send("🚫 Bạn đâu có căn nhà này mà bán!")

    # 3. Tính toán giá cả
    info = REAL_ESTATE[property_id]
    base_price = info["base_price"]
    current_price = market_prices.get(property_id, base_price)
    
    # 4. Thực hiện giao dịch
    remove_asset(ctx.author.id, property_id) # Xóa nhà
    update_balance(ctx.author.id, current_price) # Cộng tiền

    # 5. Tính Lời/Lỗ
    profit = current_price - base_price
    
    if profit > 0:
        status = "LÃI ĐẬM 📈"
        color = discord.Color.green()
        profit_str = f"+{profit:,} VNĐ"
    elif profit < 0:
        status = "LỖ VỐN 📉"
        color = discord.Color.red()
        profit_str = f"{profit:,} VNĐ"
    else:
        status = "HÒA VỐN ⚖️"
        color = discord.Color.light_grey()
        profit_str = "0 VNĐ"

    # 6. Xuất hóa đơn đẹp
    embed = discord.Embed(title=f"💵 ĐÃ BÁN: {info['name']}", color=color)
    embed.description = BAUCUA_BANNER
    
    embed.add_field(name="Vốn gốc", value=f"{base_price:,} VNĐ", inline=True)
    embed.add_field(name="Giá bán", value=f"**{current_price:,} VNĐ**", inline=True)
    embed.add_field(name="Hiệu quả", value=f"```diff\n{status}\n{profit_str}\n```", inline=False)
    
    embed.set_footer(text=f"Số dư mới: {get_balance(ctx.author.id):,} VNĐ")
    await ctx.send(embed=embed)

@bot.command(name="taisan", aliases=["assets", "myhouse"])
async def taisan(ctx):
    assets = get_user_assets(ctx.author.id)
    if not assets:
        return await ctx.send(f"🏚️ Bạn chưa có nhà. Mua ngay: `{PREFIX}muanha <id>`")

    total_value = 0
    desc = ""
    
    from collections import Counter
    counts = Counter(assets) # Đếm số lượng

    for pid, count in counts.items():
        info = REAL_ESTATE[pid]
        curr_price = market_prices.get(pid, info["base_price"])
        val = curr_price * count
        total_value += val
        
        # So sánh giá hiện tại với giá gốc để hiện mũi tên
        trend = "▲" if curr_price > info["base_price"] else "▼"
        
        desc += f"**{info['icon']} {info['name']}** (x{count})\n   ╚ Giá: `{curr_price:,}` {trend} | Tổng: `{val:,}`\n"

    embed = discord.Embed(title=f"🎒 TÀI SẢN CỦA {ctx.author.name.upper()}", color=discord.Color.teal())
    embed.description = desc
    embed.add_field(name="💰 TỔNG GIÁ TRỊ TÀI SẢN", value=f"```css\n{total_value:,} VNĐ\n```", inline=False)
    embed.set_footer(text="Code by SangMore")
    await ctx.send(embed=embed)

# --- CÁC LỆNH KHÁC (GIỮ NGUYÊN) ---

@bot.command(name="daily")
async def daily(ctx):
    user_id = ctx.author.id
    amount = 10000
    update_balance(user_id, amount)
    embed = discord.Embed(color=discord.Color.green(), description=f"✅ Nhận lương: `+ {amount:,} VNĐ`")
    await ctx.send(embed=embed)

@bot.command(name="sodu")
async def sodu(ctx):
    bal = get_balance(ctx.author.id)
    embed = discord.Embed(color=discord.Color.blue(), description=f"💰 Tiền mặt: `{bal:,} VNĐ`")
    await ctx.send(embed=embed)

@bot.command(name="bo_thi")
async def bo_thi(ctx, member: discord.Member = None, amount: int = None):
    if member is None or amount is None: return await ctx.send(f"⚠️ Cú pháp: `{PREFIX}bo_thi @ten <tien>`")
    if get_balance(ctx.author.id) < amount or amount <= 0: return await ctx.send("🚫 Lỗi tiền tệ.")
    update_balance(ctx.author.id, -amount)
    update_balance(member.id, amount)
    embed = discord.Embed(title="🧾 CHUYỂN TIỀN", color=discord.Color.teal())
    embed.add_field(name="Gửi", value=ctx.author.mention)
    embed.add_field(name="Nhận", value=member.mention)
    embed.add_field(name="Số tiền", value=f"**{amount:,} VNĐ**")
    await ctx.send(embed=embed)

@bot.command(name="baucua", aliases=["bc"])
async def baucua(ctx, choice: str = None, bet: int = None):
    if choice is None or bet is None: return await ctx.send(f"Cách chơi: `{PREFIX}baucua <con> <tiền>`")
    choice = choice.lower()
    mapping = {"bầu":"bau", "tôm":"tom", "gà":"ga", "cá":"ca"}
    if choice in mapping: choice = mapping[choice]
    if choice not in GAME_ICONS or bet <= 0: return await ctx.send("⚠️ Lỗi cú pháp.")
    if get_balance(ctx.author.id) < bet: return await ctx.send("💸 Không đủ tiền.")

    update_balance(ctx.author.id, -bet)
    embed = discord.Embed(title="🎲 ĐANG QUAY...", color=discord.Color.purple())
    msg = await ctx.send(embed=embed)

    keys = list(GAME_ICONS.keys())
    for _ in range(3):
        res = "  ".join([GAME_ICONS[random.choice(keys)]['emoji'] for _ in range(3)])
        embed.description = f"**{res}**"
        await msg.edit(embed=embed)
        await asyncio.sleep(0.8)

    dices = [random.choice(keys) for _ in range(3)]
    win = dices.count(choice)
    winnings = bet + (bet * win) if win > 0 else 0
    if win > 0: update_balance(ctx.author.id, winnings)
    
    status = f"THẮNG (x{win})" if win > 0 else "THUA"
    color = discord.Color.green() if win > 0 else discord.Color.red()
    
    res_str = "  ".join([GAME_ICONS[d]['emoji'] for d in dices])
    embed = discord.Embed(title=status, color=color, description=BAUCUA_BANNER)
    embed.add_field(name="Cược", value=f"{GAME_ICONS[choice]['emoji']} {bet:,}")
    embed.add_field(name="Về", value=f"# {res_str}")
    embed.add_field(name="Tổng", value=f"+{winnings:,}" if win else f"-{bet:,}")
    embed.set_footer(text="Code by SangMore")
    await msg.edit(embed=embed)

bot.run(TOKEN)
