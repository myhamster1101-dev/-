import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime

# --- การตั้งค่าบอท ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- ระบบฐานข้อมูล ---
db = sqlite3.connect('fivem_data.db')
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        discord_id TEXT PRIMARY KEY,
        ic_name TEXT,
        ic_age INTEGER,
        ic_height INTEGER,
        steam_url TEXT,
        reg_date TEXT
    )
''')
db.commit()

# --- ดึงค่า Variables จาก Railway ---
TOKEN = os.getenv('TOKEN')
REG_LOG_CHANNEL_ID = int(os.getenv('REG_LOG_CHANNEL_ID')) if os.getenv('REG_LOG_CHANNEL_ID') else None

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'------------------------------------------')
    print(f'✅ FiveM Registration Bot Online!')
    print(f'👤 Created by: p.hxmster')
    print(f'📅 Date: 30/03/2026')
    print(f'------------------------------------------')

# --- หน้าต่างกรอกข้อมูล (Registration Modal) ---
class RegisterModal(discord.ui.Modal, title='📝 ลงทะเบียนเข้าเมือง FiveM'):
    ic_name = discord.ui.TextInput(label='ชื่อ-นามสกุล ใน IC', placeholder='เช่น: Somsak Siriwan', min_length=3, max_length=50)
    ic_age = discord.ui.TextInput(label='อายุใน IC', placeholder='ระบุเป็นตัวเลข เช่น: 22', min_length=1, max_length=2)
    ic_height = discord.ui.TextInput(label='ส่วนสูงใน IC', placeholder='ระบุเป็นตัวเลข เช่น: 175', min_length=2, max_length=3)
    steam_url = discord.ui.TextInput(label='Link Profile Steam', placeholder='https://steamcommunity.com/id/xxxxxxxx/')

    async def on_submit(self, interaction: discord.Interaction):
        # ตรวจสอบลิงก์ Steam เบื้องต้น
        if "steamcommunity.com" not in self.steam_url.value:
            return await interaction.response.send_message("❌ ลิงก์ Steam ไม่ถูกต้อง กรุณาใช้ลิงก์จากหน้าโปรไฟล์ Steam ของคุณ", ephemeral=True)

        try:
            discord_id = str(interaction.user.id)
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            # บันทึกข้อมูลเข้า Database
            cursor.execute('''
                INSERT OR REPLACE INTO players (discord_id, ic_name, ic_age, ic_height, steam_url, reg_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (discord_id, self.ic_name.value, int(self.ic_age.value), int(self.ic_height.value), self.steam_url.value, now))
            db.commit()

            # ส่งข้อมูลไปที่ห้อง Log สำหรับ Admin
            log_channel = bot.get_channel(REG_LOG_CHANNEL_ID)
            if log_channel:
                embed = discord.Embed(
                    title="🆕 สมาชิกลงทะเบียนเข้าเมืองใหม่!",
                    description=f"มีการส่งใบลงทะเบียนจาก {interaction.user.mention}",
                    color=0x2f3136,
                    timestamp=datetime.now()
                )
                embed.add_field(name="🏷️ ชื่อในเมือง (IC)", value=f"```\n{self.ic_name.value}\n```", inline=False)
                embed.add_field(name="🎂 อายุ", value=f"**{self.ic_age.value} ปี**", inline=True)
                embed.add_field(name="📏 ส่วนสูง", value=f"**{self.ic_height.value} ซม.**", inline=True)
                embed.add_field(name="🔗 Steam Profile", value=f"[คลิกเพื่อดูโปรไฟล์]({self.steam_url.value})", inline=False)
                embed.set_footer(text=f"ID สมาชิก: {discord_id} | Created by p.hxmster")
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                
                await log_channel.send(embed=embed)

            await interaction.response.send_message(f"✅ ข้อมูลของคุณถูกส่งให้แอดมินเรียบร้อยแล้ว ขอบคุณที่ลงทะเบียนครับ!", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ กรุณากรอกอายุและส่วนสูงเป็นตัวเลขเท่านั้นครับ", ephemeral=True)

# --- คำสั่ง Slash Command สำหรับเรียกหน้าลงทะเบียน ---
@bot.tree.command(name="register", description="ลงทะเบียนข้อมูล IC และเชื่อมต่อ Steam เข้าเมือง")
async def register(interaction: discord.Interaction):
    await interaction.response.send_modal(RegisterModal())

bot.run(TOKEN)
