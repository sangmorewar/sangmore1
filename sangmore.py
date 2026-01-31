import discord
from discord.ext import commands, tasks
import random
import json
import os
import asyncio
from datetime import datetime

# --- CẤU HÌNH BOT ---
TOKEN = 'TOKEN_CUA_BAN_O_DAY' 
PREFIX = '#' 

# Cấu hình Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# File lưu dữ liệu
DB_FILE = "money.json"
ASSETS_FILE = "portfolio.json"

# Danh sách người đang làm việc
working_users = set()

# --- BANNER ---
SEPARATOR = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
HEADER = "💰 **SÀN CHỨNG KHOÁN TỶ PHÚ** 💰"

# --- DANH SÁCH 30 CÔNG TY (GIÁ TỪ TRIỆU ĐẾN TỶ) ---
# div: Cổ tức nhận được mỗi phút (Khoảng 0.1% giá trị cổ phiếu)
STOCKS = {
    # --- NHÓM GIÁ RẺ (1M - 50M) ---
    "NVL":  {"name": "Novaland", "base": 1500000, "div": 1500, "icon": "🧱"},
    "HAG":  {"name": "Hoàng Anh Gia Lai", "base": 2800000, "div": 2000, "icon": "🍌"},
    "ROS":  {"name": "Faros Construction", "base": 3500000, "div": 2500, "icon": "🏗️"},
    "STB":  {"name": "Sacombank", "base": 5000000, "div": 4000, "icon": "🏦"},
    "POW":  {"name": "PV Power", "base": 8500000, "div": 7000, "icon": "⚡"},
    "GVR":  {"name": "Cao Su VN", "base": 12000000, "div": 10000, "icon": "🌳"},
    "SSI":  {"name": "Chứng khoán SSI", "base": 25000000, "div": 22000, "icon": "📉"},
    "VRE":  {"name": "Vincom Retail", "base": 30000000, "div": 28000, "icon": "🏬"},
    "PLX":  {"name": "Petrolimex", "base": 45000000, "div": 40000, "icon": "🛢️"},
    "FPT":  {"name": "FPT Corp", "base": 90000000, "div": 85000, "icon": "💻"},

    # --- NHÓM TẦM TRUNG (100M - 900M) ---
    "PNJ":  {"name": "Vàng PNJ", "base": 120000000, "div": 110000, "icon": "💍"},
    "MWG":  {"name": "Thế Giới Di Động", "base": 150000000, "div": 140000, "icon": "📱"},
    "MSN":  {"name": "Masan Group", "base": 180000000, "div": 170000, "icon": "🍜"},
    "GAS":  {"name": "PV Gas", "base": 220000000, "div": 200000, "icon": "⛽"},
    "SAB":  {"name": "Sabeco", "base": 250000000, "div": 230000, "icon": "🍺"},
    "VJC":  {"name": "Vietjet Air", "base": 300000000, "div": 280000, "icon": "✈️"},
    "VCB":  {"name": "Vietcombank", "base": 450000000, "div": 420000, "icon": "💳"},
    "VIC":  {"name": "Vingroup", "base": 600000000, "div": 550000, "icon": "🏙️"},
    "VNM":  {"name": "Vinamilk", "base": 800000000, "div": 750000, "icon": "🥛"},
    "SJC":  {"name": "Vàng SJC (1 Lượng)", "base": 950000000, "div": 880000, "icon": "🥇"},

    # --- NHÓM ĐẠI GIA (1 TỶ - 10 TỶ) ---
    "NFLX": {"name": "Netflix", "base": 1200000000, "div": 1100000, "icon": "🎬"},
    "META": {"name": "Meta (Facebook)", "base": 1800000000, "div": 1600000, "icon": "📘"},
    "TSLA": {"name": "Tesla Motors", "base": 2500000000, "div": 2300000, "icon": "🚗"},
    "NVDA": {"name": "NVIDIA", "base": 3200000000, "div": 3000000, "icon": "🎮"},
    "AMZN": {"name": "Amazon", "base": 4000000000, "div": 3800000, "icon": "📦"},
    "GOOG": {"name": "Google (Alphabet)", "base": 5500000000, "div": 5000000, "icon": "🔍"},
    "MSFT": {"name": "Microsoft", "base": 6800000000, "div": 6500000, "icon": "🪟"},
    "AAPL": {"name": "Apple Inc", "base": 8000000000, "div": 7500000, "icon": "🍎"},
    "BTC":  {"name": "Bitcoin", "base": 9500000000, "div": 9000000, "icon": "🪙"},
    "BRK":  {"name": "Berkshire Hathaway", "base": 15000000000, "div": 14000000, "icon": "📈"}
}

market_prices = {} 

# --- HỆ THỐNG DỮ LIỆU ---
def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, "r") as f: return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f)

def get_balance(user_id):
    data = load_json(DB_FILE)
    return data.get(str(user_id), 0)

def update_balance(user_id, amount):
    data = load_json(DB_FILE)
    uid = str(user_id)
    if uid not in data: data[uid] = 0
    data[uid] += amount
    save_json(DB_FILE, data)

def get_portfolio(user_id):
    data = load_json(ASSETS_FILE)
    return data.get(str(user_id), {})

def update_portfolio(user_id, symbol, amount):
    data = load_json(ASSETS_FILE)
    uid = str(user_id)
    if uid not in data: data[uid] = {}
    current_qty = data[uid].get(symbol, 0)
    new_qty = current_qty + amount
    if new_qty <= 0:
        if symbol in data[uid]: del data[uid][symbol]
    else:
        data[uid][symbol] = new_qty
    save_json(ASSETS_FILE, data)

# --- GLOBAL CHECK ---
@bot.check
async def check_if_working(ctx):
    if ctx.author.id in working_users:
        await ctx.send(f"🚫 {ctx.author.mention}, bạn đang bận làm việc! Đừng phân tâm.")
        return False
    return True

# --- BACKGROUND TASKS ---
@tasks.loop(seconds=30)
async def update_market_task():
    global market_prices
    if not market_prices:
        for symbol, info in STOCKS.items():
            market_prices[symbol] = info["base"]

    for symbol in market_prices:
        current = market_prices[symbol]
        base = STOCKS[symbol]["base"]
        chance = random.randint(1, 100)
        
        # Biến động mạnh hơn vì giá to
        if chance <= 60: percent = random.uniform(-0.02, 0.03) # Ổn định
        elif chance <= 90: percent = random.uniform(-0.05, 0.08) # Biến động
        else: percent = random.uniform(-0.15, 0.20) # Sốc
            
        change = int(current * percent)
        new_price = current + change
        if new_price < int(base * 0.3): new_price = int(base * 0.3) # Giá sàn
        market_prices[symbol] = new_price

@tasks.loop(seconds=60)
async def pay_dividends():
    data = load_json(ASSETS_FILE)
    money_data = load_json(DB_FILE)
    total_paid = 0
    for user_id, portfolio in data.items():
        user_income = 0
        for symbol, qty in portfolio.items():
            if symbol in STOCKS:
                income = qty * STOCKS[symbol]["div"]
                user_income += income
        if user_income > 0:
            if user_id not in money_data: money_data[user_id] = 0
            money_data[user_id] += user_income
            total_paid += user_income
            
    if total_paid > 0:
        save_json(DB_FILE, money_data)
        # print(f"Đã trả {total_paid} cổ tức")

# --- SỰ KIỆN BOT ---
@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} online - Mode: Tỷ Phú')
    update_market_task.start()
    pay_dividends.start()
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}menu | Sàn Tỷ Đô"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        m, s = divmod(error.retry_after, 60)
        await ctx.send(f"⏳ Nghỉ ngơi đi đại gia! Chờ `{int(m)}p {int(s)}s` nữa.")
    elif isinstance(error, commands.CheckFailure): pass

# --- CÁC LỆNH ---

@bot.command(name="menu", aliases=["help", "huongdan"])
async def menu(ctx):
    embed = discord.Embed(color=discord.Color.gold())
    embed.description = f"{SEPARATOR}\n{HEADER}\n{SEPARATOR}\nXin chào Tỷ phú **{ctx.author.name}**."
    
    economy = (
        f"🛠️ **`{PREFIX}lamviec`** : Bạn sẽ đi ký hợp đồng với các công ty và nhận tiền.\n"
        f"💸 **`{PREFIX}daily`** : Quà điểm danh.\n"
        f"💳 **`{PREFIX}sodu`** : Kiểm tra két sắt.\n"
        f"💼 **`{PREFIX}tuido`** : Danh mục đầu tư.\n"
    )
    embed.add_field(name="💰 TÀI CHÍNH", value=economy, inline=False)
    
    stock = (
        f"📊 **`{PREFIX}bang`** : Bảng giá (Live).\n"
        f"📈 **`{PREFIX}mua <mã> <sl>`** : Mua vào.\n"
        f"📉 **`{PREFIX}ban <mã> <sl>`** : Bán ra.\n"
        f"ℹ️ **`{PREFIX}xem <mã>`** : Soi giá."
    )
    embed.add_field(name="🏙️ ĐẦU TƯ", value=stock, inline=False)
    embed.set_footer(text="Code by SangMore")
    await ctx.send(embed=embed)

@bot.command(name="daily")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    amount = 500000
    update_balance(ctx.author.id, amount)
    await ctx.send(f"✅ **{ctx.author.name}** đã nhận tiền tiêu vặt: **+{amount:,} VNĐ**")

@bot.command(name="lamviec", aliases=["work"])
@commands.cooldown(1, 300, commands.BucketType.user)
async def lamviec(ctx):
    job_symbol = random.choice(list(STOCKS.keys()))
    job_info = STOCKS[job_symbol]
    
    # Lương cơ bản 1 Triệu + Thưởng theo giá trị cty
    base_salary = 1000000 
    bonus = int(job_info["base"] / 5000) # Cty càng to lương càng cao
    salary = base_salary + bonus
    
    working_users.add(ctx.author.id)
    
    embed = discord.Embed(title=f"💼 ĐANG HỌP TẠI {job_info['name'].upper()}", color=discord.Color.orange())
    embed.description = f"🏢 Địa điểm: {job_info['icon']}\n⏳ Thời gian: 30 giây..."
    msg = await ctx.send(embed=embed)
    
    await asyncio.sleep(30)
    
    update_balance(ctx.author.id, salary)
    working_users.remove(ctx.author.id)
    
    embed_done = discord.Embed(title="✅ ĐÃ KÝ HỢP ĐỒNG XONG", color=discord.Color.green())
    embed_done.description = f"Bạn nhận được thù lao: **{salary:,} VNĐ**"
    await msg.edit(embed=embed_done)

@bot.command(name="sodu", aliases=["bal"])
async def sodu(ctx):
    bal = get_balance(ctx.author.id)
    await ctx.send(f"💳 Két sắt: **{bal:,} VNĐ**")

@bot.command(name="bang", aliases=["price"])
async def bang(ctx):
    embed = discord.Embed(title="📊 BẢNG ĐIỆN TỬ (TỶ ĐỒNG)", color=discord.Color.blue())
    desc = ""
    # Sắp xếp theo giá tăng dần để dễ nhìn
    sorted_stocks = sorted(market_prices.items(), key=lambda x: x[1])
    
    # Chỉ hiện 15 mã tiêu biểu
    for symbol, price in sorted_stocks[:15]:
        info = STOCKS[symbol]
        base = info["base"]
        percent = ((price - base) / base) * 100
        icon_trend = "🟢" if percent >= 0 else "🔴"
        desc += f"{info['icon']} **{symbol}**: `{price:,}` ({icon_trend} {percent:.1f}%)\n"
        
    embed.description = desc + "\n*... (Gõ lệnh xem mã cụ thể)*"
    embed.set_footer(text="Code by SangMore")
    await ctx.send(embed=embed)

@bot.command(name="xem", aliases=["check"])
async def xem(ctx, symbol: str = None):
    if not symbol: return await ctx.send(f"⚠️ Nhập mã. VD: `{PREFIX}xem BTC`")
    symbol = symbol.upper()
    if symbol not in STOCKS: return await ctx.send("🚫 Mã không tồn tại.")
    info = STOCKS[symbol]
    price = market_prices.get(symbol, info["base"])
    base = info["base"]
    percent = ((price - base) / base) * 100
    color = discord.Color.green() if percent >= 0 else discord.Color.red()
    
    embed = discord.Embed(title=f"{info['icon']} {info['name']} ({symbol})", color=color)
    embed.add_field(name="Giá hiện tại", value=f"**{price:,} VNĐ**", inline=True)
    embed.add_field(name="Biến động", value=f"{percent:.2f}%", inline=True)
    embed.add_field(name="Cổ tức/Phút", value=f"💸 **+{info['div']:,} VNĐ**", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="mua", aliases=["buy"])
async def mua(ctx, symbol: str = None, amount: int = None):
    if not symbol or not amount or amount <= 0: return await ctx.send("⚠️ Lỗi cú pháp.")
    symbol = symbol.upper()
    if symbol not in STOCKS: return await ctx.send("🚫 Sai mã.")
    price = market_prices.get(symbol, STOCKS[symbol]["base"])
    total = price * amount
    if get_balance(ctx.author.id) < total: return await ctx.send("💸 Tiền đâu mà mua?")
    update_balance(ctx.author.id, -total)
    update_portfolio(ctx.author.id, symbol, amount)
    await ctx.send(f"✅ Đã chốt **{amount} {symbol}** giá `{total:,} VNĐ`")

@bot.command(name="ban", aliases=["sell"])
async def ban(ctx, symbol: str = None, amount: int = None):
    if not symbol or not amount or amount <= 0: return await ctx.send("⚠️ Lỗi cú pháp.")
    symbol = symbol.upper()
    port = get_portfolio(ctx.author.id)
    if port.get(symbol, 0) < amount: return await ctx.send("🚫 Không đủ hàng.")
    price = market_prices.get(symbol, STOCKS[symbol]["base"])
    total = price * amount
    update_portfolio(ctx.author.id, symbol, -amount)
    update_balance(ctx.author.id, total)
    await ctx.send(f"✅ Đã xả **{amount} {symbol}** thu về `{total:,} VNĐ`")

@bot.command(name="tuido", aliases=["my"])
async def tuido(ctx):
    port = get_portfolio(ctx.author.id)
    if not port: return await ctx.send("💼 Bạn chưa đầu tư gì cả.")
    desc = ""
    total_val = 0
    total_div = 0
    for s, q in port.items():
        if s in STOCKS:
            p = market_prices.get(s, STOCKS[s]["base"])
            val = p * q
            div = q * STOCKS[s]["div"]
            total_val += val
            total_div += div
            desc += f"**{s}**: {q:,} cp ➜ `{val:,}` (+{div:,}/p)\n"
    embed = discord.Embed(title=f"💼 DANH MỤC CỦA {ctx.author.name.upper()}", color=discord.Color.purple())
    embed.description = desc
    embed.add_field(name="Tổng Giá Trị", value=f"`{total_val:,} VNĐ`")
    embed.add_field(name="Lãi Thụ Động", value=f"`+{total_div:,}/phút`")
    await ctx.send(embed=embed)

bot.run(TOKEN)
