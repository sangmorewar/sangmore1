import discord
from discord.ext import commands, tasks
import random
import json
import os
import asyncio

# --- CẤU HÌNH BOT ---
TOKEN = 'MTQ2Njk4MTkyMjQyNDA5ODgyOQ.GZ22ik.m_If-qEcubyBE0zVqAOkEDhUgs_HEOwWz08vjA' 
PREFIX = '#' 
ADMIN_ID = 1464171574600138815 # <--- THAY ID CỦA BẠN VÀO ĐÂY ĐỂ DÙNG LỆNH ADMIN

# Cấu hình Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# File lưu dữ liệu
DB_FILE = "money.json"
ASSETS_FILE = "assets.json"

# --- BANNER ---
SEPARATOR_LINE = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
HEADER_TEXT = "🏛️  **HỆ THỐNG TÀI CHÍNH & BĐS** 🏛️"

# --- CẤU HÌNH BẤT ĐỘNG SẢN ---
REAL_ESTATE = {
    1: {"name": "Lều Tranh", "base_price": 50000, "icon": "⛺"},
    2: {"name": "Nhà Cấp 4", "base_price": 500000, "icon": "🏠"},
    3: {"name": "Chung Cư", "base_price": 2000000, "icon": "🏢"},
    4: {"name": "Biệt Thự", "base_price": 10000000, "icon": "🏡"},
    5: {"name": "Khách Sạn", "base_price": 50000000, "icon": "🏨"},
    6: {"name": "Landmark 81", "base_price": 500000000, "icon": "🌇"},
    7: {"name": "Đảo Tư Nhân", "base_price": 2000000000, "icon": "🏝️"}
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
        data[uid].remove(property_id)
        save_assets(data)
        return True
    return False

def get_user_assets(user_id):
    data = load_assets()
    return data.get(str(user_id), [])

# --- HỆ THỐNG THỊ TRƯỜNG "REAL LIFE" ---
@tasks.loop(seconds=30)
async def update_market():
    global market_prices, market_history
    
    if not market_prices:
        for pid, info in REAL_ESTATE.items():
            market_prices[pid] = info["base_price"]
            market_history[pid] = [info["base_price"]] * 10

    for pid in market_prices:
        current = market_prices[pid]
        
        # --- THUẬT TOÁN "REAL LIFE" ---
        chance = random.randint(1, 100)
        
        if chance <= 60:
            # 60% BÌNH ỔN: Tăng nhẹ tích sản (Giống ngoài đời)
            # Từ -1% đến +10%
            percent = random.uniform(-0.01, 0.1)
            
        elif chance <= 90:
            # 30% SÔI ĐỘNG: Biến động vừa phải
            # Từ -3% đến +15%
            percent = random.uniform(-0.03, 0.15)
            
        else:
            # 10% BIẾN ĐỘNG MẠNH (Sốt đất hoặc Đóng băng)
            # Từ -10% đến +25%
            percent = random.uniform(-0.10, 0.25)

        change = int(current * percent)
        new_price = current + change
        
        # Giới hạn giá sàn (Không bao giờ thấp hơn 50% giá gốc - BĐS luôn có giá trị thực)
        base = REAL_ESTATE[pid]["base_price"]
        if new_price < int(base * 0.5): new_price = int(base * 0.5)
        
        market_prices[pid] = new_price
        
        market_history[pid].append(new_price)
        if len(market_history[pid]) > 15:
            market_history[pid].pop(0)

# --- SỰ KIỆN KHỞI CHẠY ---
@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} đã sẵn sàng!')
    if not update_market.is_running():
        update_market.start()
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}huongdan | Real Estate Sim"))

# --- MENU HƯỚNG DẪN ---
@bot.command(name="huongdan", aliases=["menu", "help"])
async def huongdan(ctx):
    embed = discord.Embed(color=discord.Color.dark_grey())
    
    header = f"{SEPARATOR_LINE}\n{HEADER_TEXT}\n{SEPARATOR_LINE}\n"
    embed.description = f"{header}\nChào nhà đầu tư **{ctx.author.name}**!"
    
    economy_text = (
        f"💸 **`{PREFIX}daily`** ➜ Lương 10k\n"
        f"💳 **`{PREFIX}sodu`** ➜ Xem ví\n"
        f"💸 **`{PREFIX}bo_thi`** ➜ Chuyển tiền"
    )
    embed.add_field(name="💰 TÀI CHÍNH", value=economy_text, inline=True)

    game_text = (
        f"🎲 **`{PREFIX}baucua`**➜ #baucua <con> <vnd>\n"
        f"(bau, cua, tom, ca, ga, nai)"
    )
    embed.add_field(name="🎰 GIẢI TRÍ", value=game_text, inline=True)

    bds_text = (
        f"📈 **`{PREFIX}thitruong`** : Bảng giá (Live)\n"
        f"📊 **`{PREFIX}gianha <id>`** : Biểu đồ nến\n"
        f"🏠 **`{PREFIX}muanha <id>`** : Mua tích sản\n"
        f"💵 **`{PREFIX}banna <id>`** : Bán chốt lời\n"
        f"🎒 **`{PREFIX}taisan`** : Sổ đỏ của bạn"
    )
    embed.add_field(name="🏙️ ĐẦU TƯ BĐS", value=bds_text, inline=False)

    if ctx.author.id == ADMIN_ID:
        embed.add_field(name="🔒 ADMIN CONTROL", value=f"🛠️ **`{PREFIX}daygia <id> <%>`** : Thao túng giá", inline=False)
    
    embed.set_footer(text="Code by SangMore") 
    await ctx.send(embed=embed)


# --- LỆNH ADMIN ---
@bot.command(name="daygia", aliases=["push"])
async def daygia(ctx, pid: int = None, percent: float = None):
    if ctx.author.id != ADMIN_ID:
        return await ctx.send("🚫 Bạn không có quyền thao túng thị trường!")
    
    if not pid or not percent or pid not in REAL_ESTATE:
        return await ctx.send(f"⚠️ Cú pháp: `{PREFIX}daygia <id> <%>`")

    current = market_prices.get(pid, REAL_ESTATE[pid]["base_price"])
    change = int(current * (percent / 100))
    new_price = current + change
    if new_price < 1000: new_price = 1000 
    
    market_prices[pid] = new_price
    market_history[pid].append(new_price)
    if len(market_history[pid]) > 15: market_history[pid].pop(0)
    
    icon = "🚀" if percent > 0 else "📉"
    embed = discord.Embed(title=f"{icon} TIN MẬT (ADMIN)", color=discord.Color.magenta())
    embed.description = f"Thị trường **{REAL_ESTATE[pid]['name']}** vừa biến động **{percent}%**\nGiá mới: **{new_price:,} VNĐ**"
    await ctx.send(embed=embed)


# --- CÁC LỆNH BẤT ĐỘNG SẢN ---

@bot.command(name="thitruong", aliases=["market"])
async def thitruong(ctx):
    embed = discord.Embed(title="📈 BẢNG GIÁ THỊ TRƯỜNG", color=discord.Color.gold())
    embed.description = "*Thị trường BĐS ổn định, phù hợp đầu tư dài hạn.*"
    
    for pid, info in REAL_ESTATE.items():
        curr_price = market_prices.get(pid, info["base_price"])
        base_price = info["base_price"]
        
        diff = curr_price - base_price
        percent = (diff / base_price) * 100
        
        if diff > 0:
            trend = f"📈 Tăng: **{percent:.1f}%**"
            status = "Tốt"
        elif diff < 0:
            trend = f"📉 Giảm: **{percent:.1f}%**"
            status = "DIP"
        else:
            trend = "➖ 0%"
            status = "Ổn"

        embed.add_field(
            name=f"{info['icon']} {info['name']} (#{pid})",
            value=f"Giá: **{curr_price:,}**\n{trend}",
            inline=True
        )
    embed.set_footer(text=f"Muốn xem biểu đồ? Gõ {PREFIX}gianha <id>")
    await ctx.send(embed=embed)

@bot.command(name="gianha", aliases=["chart"])
async def gianha(ctx, property_id: int = None):
    if not property_id or property_id not in REAL_ESTATE:
        await ctx.send(f"⚠️ Nhập ID nhà (1-7). Xem `{PREFIX}thitruong`")
        return

    history = market_history.get(property_id, [])
    info = REAL_ESTATE[property_id]
    current_price = history[-1]
    
    chart_str = ""
    for i in range(1, len(history)):
        prev, curr = history[i-1], history[i]
        if curr > prev: chart_str += " / " 
        elif curr < prev: chart_str += " \ " 
        else: chart_str += " - "
            
    graph_display = f"""```ansi
[1;34m{info['icon']} {info['name'].upper()}[0m

Giá (VNĐ)
  ^
  |                   {chart_str} [1;31m⬤ ({current_price:,})[0m
  |         [1;33m////[0m     /
  |  [1;32m////[0m  /    \   /
__|_______________________>
```"""

    embed = discord.Embed(color=discord.Color.dark_blue())
    embed.description = graph_display
    await ctx.send(embed=embed)

@bot.command(name="muanha", aliases=["buy"])
async def muanha(ctx, property_id: int = None):
    if not property_id or property_id not in REAL_ESTATE:
        return await ctx.send(f"⚠️ Nhập ID nhà (1-7). Xem `{PREFIX}thitruong`")

    price = market_prices.get(property_id, REAL_ESTATE[property_id]["base_price"])
    bal = get_balance(ctx.author.id)

    if bal < price:
        return await ctx.send(f"💸 **Thiếu tiền!** Cần: {price:,} VNĐ")

    update_balance(ctx.author.id, -price)
    add_asset(ctx.author.id, property_id)
    
    embed = discord.Embed(title="✅ MUA NHÀ THÀNH CÔNG", color=discord.Color.green())
    embed.description = f"Sở hữu: **{REAL_ESTATE[property_id]['name']}**\nGiá mua: `{price:,} VNĐ`"
    await ctx.send(embed=embed)

@bot.command(name="banna", aliases=["sell"])
async def banna(ctx, property_id: int = None):
    if not property_id: return await ctx.send(f"⚠️ Gõ: `{PREFIX}banna <id>`")
    
    user_assets = get_user_assets(ctx.author.id)
    if property_id not in user_assets:
        return await ctx.send("🚫 Bạn không có nhà này!")

    info = REAL_ESTATE[property_id]
    base_price = info["base_price"]
    current_price = market_prices.get(property_id, base_price)
    
    remove_asset(ctx.author.id, property_id)
    update_balance(ctx.author.id, current_price)

    profit = current_price - base_price
    
    if profit > 0:
        status = "LÃI📈"
        color = discord.Color.green()
        profit_str = f"+{profit:,}"
    elif profit < 0:
        status = "LỖ📉"
        color = discord.Color.red()
        profit_str = f"{profit:,}"
    else:
        status = "HÒA​⚖️"
        color = discord.Color.light_grey()
        profit_str = "0"

    embed = discord.Embed(title=f"💵 ĐÃ BÁN: {info['name']}", color=color)
    embed.add_field(name="Giá Bán", value=f"**{current_price:,} VNĐ**", inline=False)
    embed.add_field(name="Hiệu Quả", value=f"{status} ({profit_str} VNĐ)", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="taisan", aliases=["assets"])
async def taisan(ctx):
    assets = get_user_assets(ctx.author.id)
    if not assets: return await ctx.send(f"🏚️ Chưa có nhà nào.")

    total_value = 0
    desc = ""
    from collections import Counter
    counts = Counter(assets)

    for pid, count in counts.items():
        info = REAL_ESTATE[pid]
        curr_price = market_prices.get(pid, info["base_price"])
        val = curr_price * count
        total_value += val
        
        if curr_price > info["base_price"]: icon = "📈"
        else: icon = "🔻"
        
        desc += f"**{info['name']}** (x{count})\n   └ Giá: `{curr_price:,}` {icon} | Tổng: `{val:,}`\n"

    embed = discord.Embed(title=f"🎒 TÀI SẢN: {ctx.author.name.upper()}", color=discord.Color.teal())
    embed.description = desc
    embed.set_footer(text=f"Tổng giá trị ước tính: {total_value:,} VNĐ")
    await ctx.send(embed=embed)

# --- CÁC LỆNH KHÁC ---
@bot.command(name="daily")
async def daily(ctx):
    update_balance(ctx.author.id, 10000)
    await ctx.send(embed=discord.Embed(description=f"✅ +10,000 VNĐ", color=discord.Color.green()))

@bot.command(name="sodu")
async def sodu(ctx):
    await ctx.send(embed=discord.Embed(description=f"💰 Ví: `{get_balance(ctx.author.id):,} VNĐ`", color=discord.Color.blue()))

@bot.command(name="bo_thi")
async def bo_thi(ctx, member: discord.Member = None, amount: int = None):
    if not member or not amount or amount <= 0 or get_balance(ctx.author.id) < amount:
        return await ctx.send("⚠️ Lỗi giao dịch.")
    update_balance(ctx.author.id, -amount)
    update_balance(member.id, amount)
    await ctx.send(f"✅ Đã chuyển {amount:,} VNĐ cho {member.mention}")

@bot.command(name="baucua", aliases=["bc"])
async def baucua(ctx, choice: str = None, bet: int = None):
    if not choice or not bet or bet <= 0 or get_balance(ctx.author.id) < bet:
        return await ctx.send("⚠️ Lỗi đặt cược.")
    
    choice = choice.lower()
    mapping = {"bầu":"bau", "tôm":"tom", "gà":"ga", "cá":"ca"}
    if choice in mapping: choice = mapping[choice]
    if choice not in GAME_ICONS: return await ctx.send("⚠️ Sai tên con vật.")

    update_balance(ctx.author.id, -bet)
    
    msg = await ctx.send(embed=discord.Embed(title="🎲 ĐANG LẮC...", color=discord.Color.purple()))
    await asyncio.sleep(2)
    
    keys = list(GAME_ICONS.keys())
    dices = [random.choice(keys) for _ in range(3)]
    win = dices.count(choice)
    winnings = bet + (bet * win) if win > 0 else 0
    
    if win > 0: update_balance(ctx.author.id, winnings)
    
    res_str = " ".join([GAME_ICONS[d]['emoji'] for d in dices])
    status = "THẮNG" if win > 0 else "THUA"
    color = discord.Color.green() if win > 0 else discord.Color.red()
    
    embed = discord.Embed(title=f"{status} {res_str}", color=color)
    embed.add_field(name="Kết quả", value=f"{'+' if win else '-'}{winnings if win else bet:,} VNĐ")
    await msg.edit(embed=embed)

bot.run(TOKEN)
