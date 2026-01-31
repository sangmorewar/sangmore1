import discord
from discord.ext import commands
import random
import json
import os
import asyncio
from datetime import datetime

# --- CẤU HÌNH ---
TOKEN = 'TOKEN_CUA_BAN_O_DAY'  # <-- Dán Token bot của bạn vào đây
PREFIX = '#' 

# Cấu hình Intents (QUAN TRỌNG: Cần bật Message Content & Members trong Developer Portal)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# File lưu dữ liệu tiền
DB_FILE = "money.json"

# Cấu hình Game (Icon và Tên hiển thị)
GAME_ICONS = {
    "bau": {"emoji": "🍐", "name": "Bầu"},
    "cua": {"emoji": "🦀", "name": "Cua"},
    "tom": {"emoji": "🦐", "name": "Tôm"},
    "ca":  {"emoji": "🐟", "name": "Cá"},
    "ga":  {"emoji": "🐓", "name": "Gà"},
    "nai": {"emoji": "🦌", "name": "Nai"}
}

# --- HỆ THỐNG DATABASE (LƯU TIỀN) ---
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

# --- SỰ KIỆN BOT ---
@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} đã sẵn sàng phục vụ!')
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}huongdan | Game Bầu Cua"))

# --- MENU HƯỚNG DẪN CHI TIẾT ---

@bot.command(name="huongdan", aliases=["menu", "help"])
async def huongdan(ctx):
    """Hiển thị menu hướng dẫn chi tiết"""
    embed = discord.Embed(
        title="📜 MENU HƯỚNG DẪN SỬ DỤNG",
        description=f"Chào mừng bạn đến với sòng Bầu Cua! Dưới đây là danh sách tất cả các lệnh:",
        color=discord.Color.gold()
    )
    
    # Mục 1: Tài Chính
    economy_desc = (
        f"👉 **`{PREFIX}daily`**\n"
        f"   - Điểm danh hàng ngày nhận **10,000 VNĐ**.\n"
        f"👉 **`{PREFIX}sodu`**\n"
        f"   - Kiểm tra số dư hiện tại trong ví của bạn.\n"
        f"👉 **`{PREFIX}bo_thi @nguoi_nhan <số tiền>`**\n"
        f"   - Chuyển tiền (bố thí) cho người khác.\n"
        f"   - *Ví dụ:* `{PREFIX}bo_thi @Nam 50000`"
    )
    embed.add_field(name="💰 KINH TẾ & TÀI CHÍNH", value=economy_desc, inline=False)
    
    # Mục 2: Trò Chơi
    game_desc = (
        f"👉 **`{PREFIX}baucua <con vật> <số tiền>`**\n"
        f"   - Đặt cược vào linh vật may mắn.\n"
        f"   - *Danh sách linh vật:* 🍐Bầu, 🦀Cua, 🦐Tôm, 🐟Cá, 🐓Gà, 🦌Nai.\n"
        f"   - *Ví dụ:* `{PREFIX}baucua bau 5000` (Cược Bầu 5k)."
    )
    embed.add_field(name="🎲 TRÒ CHƠI BẦU CUA", value=game_desc, inline=False)

    # Mục 3: Luật Lệ
    rules_desc = (
        "🏆 **Cơ Chế Trả Thưởng:**\n"
        "   - **Trúng 1 con:** Nhận lại Vốn + Lãi x1\n"
        "   - **Trúng 2 con:** Nhận lại Vốn + Lãi x2\n"
        "   - **Trúng 3 con:** Nhận lại Vốn + Lãi x3\n\n"
        "⚠️ **Lưu ý:** Tiền cược phải lớn hơn 0 và không quá số dư hiện có."
    )
    embed.add_field(name="⚖️ LUẬT CHƠI", value=rules_desc, inline=False)
    
    # Footer
    embed.set_footer(text=f"Bot được yêu cầu bởi {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.set_thumbnail(url="https://i.imgur.com/P7X2N4H.png") # Ảnh minh họa (tùy chọn)

    await ctx.send(embed=embed)


# --- CÁC LỆNH CHỨC NĂNG ---

@bot.command(name="daily")
async def daily(ctx):
    user_id = ctx.author.id
    amount = 10000
    update_balance(user_id, amount)
    
    embed = discord.Embed(title="🧧 Điểm Danh Nhận Lương", color=discord.Color.green())
    embed.description = f"Chúc mừng {ctx.author.mention}!\nBạn đã nhận được **{amount:,} VNĐ**."
    embed.set_footer(text=f"Tổng tài sản: {get_balance(user_id):,} VNĐ")
    await ctx.send(embed=embed)

@bot.command(name="sodu", aliases=["bal", "tien"])
async def sodu(ctx):
    bal = get_balance(ctx.author.id)
    embed = discord.Embed(color=discord.Color.blue())
    embed.set_author(name=f"Ví tiền của {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.description = f"💸 Số dư khả dụng: **{bal:,} VNĐ**"
    await ctx.send(embed=embed)

@bot.command(name="bo_thi", aliases=["pay", "give"])
async def bo_thi(ctx, member: discord.Member = None, amount: int = None):
    # Check lỗi
    if member is None or amount is None:
        await ctx.send(f"⚠️ **Sai cú pháp!**\nDùng lệnh: `{PREFIX}bo_thi @nguoi_nhan <so_tien>`")
        return
    if member.id == ctx.author.id:
        await ctx.send("🤔 Bạn không thể tự chuyển tiền cho chính mình.")
        return
    if amount <= 0:
        await ctx.send("⚠️ Số tiền chuyển phải lớn hơn 0.")
        return
    
    sender_bal = get_balance(ctx.author.id)
    if sender_bal < amount:
        await ctx.send(f"💸 **Không đủ tiền!** Bạn chỉ còn: {sender_bal:,} VNĐ.")
        return

    # Giao dịch
    update_balance(ctx.author.id, -amount)
    update_balance(member.id, amount)

    # Embed Hóa Đơn
    embed = discord.Embed(title="💳 GIAO DỊCH THÀNH CÔNG", color=discord.Color.teal())
    embed.add_field(name="Người Gửi", value=ctx.author.mention, inline=True)
    embed.add_field(name="Người Nhận", value=member.mention, inline=True)
    embed.add_field(name="Số Tiền", value=f"**{amount:,} VNĐ**", inline=False)
    embed.set_footer(text=f"Số dư còn lại của bạn: {get_balance(ctx.author.id):,} VNĐ")
    
    await ctx.send(embed=embed)

@bot.command(name="baucua", aliases=["bc"])
async def baucua(ctx, choice: str = None, bet: int = None):
    if choice is None or bet is None:
        await ctx.send(f"⚠️ **Sai cú pháp!** Xem hướng dẫn: `{PREFIX}huongdan`")
        return

    # Xử lý tên
    choice = choice.lower()
    mapping_dau = {"tôm": "tom", "bầu": "bau", "gà": "ga", "cá": "ca"}
    if choice in mapping_dau: choice = mapping_dau[choice]

    if choice not in GAME_ICONS:
        await ctx.send(f"⚠️ Không có con vật `{choice}`. (Chọn: bau, cua, tom, ca, ga, nai)")
        return

    if bet <= 0:
        await ctx.send("⚠️ Tiền cược không hợp lệ.")
        return

    cur_bal = get_balance(ctx.author.id)
    if cur_bal < bet:
        await ctx.send(f"💸 **Không đủ tiền cược!** Ví bạn còn: {cur_bal:,} VNĐ.")
        return

    # Trừ tiền
    update_balance(ctx.author.id, -bet)

    # Lắc
    msg = await ctx.send(embed=discord.Embed(title="🎲 Đang lắc...", description="🎰 🎰 🎰", color=discord.Color.gold()))
    await asyncio.sleep(2)

    # Kết quả
    keys = list(GAME_ICONS.keys())
    dices = [random.choice(keys) for _ in range(3)]
    
    win_count = dices.count(choice)
    winnings = 0
    
    if win_count > 0:
        winnings = bet + (bet * win_count)
        update_balance(ctx.author.id, winnings)
        status = f"THẮNG (x{win_count})"
        color = discord.Color.green()
    else:
        status = "THUA"
        color = discord.Color.red()

    res_emoji = "  ".join([GAME_ICONS[d]['emoji'] for d in dices])
    res_text = ", ".join([GAME_ICONS[d]['name'] for d in dices])

    # Embed Kết quả
    embed = discord.Embed(title=f"🎰 Kết Quả: {status}", color=color)
    embed.add_field(name="Đặt Cược", value=f"{GAME_ICONS[choice]['emoji']} **{bet:,} VNĐ**", inline=True)
    embed.add_field(name="Kết Quả Về", value=f"{res_emoji}\n({res_text})", inline=True)
    
    if win_count > 0:
        embed.add_field(name="Tổng Nhận", value=f"**+{winnings:,} VNĐ**", inline=False)
    else:
        embed.add_field(name="Thất Thoát", value=f"-{bet:,} VNĐ", inline=False)
        
    embed.set_footer(text=f"Số dư mới: {get_balance(ctx.author.id):,} VNĐ")
    
    await msg.edit(embed=embed)

bot.run(TOKEN)
