import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import os
from datetime import datetime

# --- ตั้งค่า Bot ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# --- Database ---
db = sqlite3.connect('fivem_data.db')
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        discord_id TEXT PRIMARY KEY, ic_name TEXT, ic_age INTEGER, ic_height INTEGER, steam_url TEXT, reg_date TEXT
    )
''')
db.commit()

# --- Variables ---
TOKEN = os.getenv('TOKEN')
REG_LOG_CHANNEL_ID = int(os.getenv('REG_LOG_CHANNEL_ID')) if os.getenv('REG_LOG_CHANNEL_ID') else None

# --- Modal หน้าต่างกรอกข้อมูล ---
class RegisterModal(discord.ui.Modal, title='📝 ลงทะเบียนเข้าเมือง FiveM'):
    ic_name = discord.ui.TextInput(label='ชื่อ-นามสกุล ใน IC', placeholder='เช่น: Somchai Sakuldee', min_length=3)
    ic_age = discord.ui.TextInput(label='อายุใน IC', placeholder='เช่น: 25', min_length=1, max_length=2)
    ic_height = discord.ui.TextInput(label='ส่วนสูงใน IC', placeholder='เช่น: 175', min_length=2, max_length=3)
    steam_url = discord.ui.TextInput(label='Link Profile Steam', placeholder='https://steamcommunity.com/id/xxxx/')

    async def on_submit(self, interaction: discord.Interaction):
        if "steamcommunity.com" not in self.steam_url.value:
            return await interaction.response.send_message("❌ ลิงก์ Steam ไม่ถูกต้อง!", ephemeral=True)
        try:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            cursor.execute('INSERT OR REPLACE INTO players VALUES (?,?,?,?,?,?)', 
                           (str(interaction.user.id), self.ic_name.value, int(self.ic_age.value), int(self.ic_height.value), self.steam_url.value, now))
            db.commit()

            log_ch = bot.get_channel(REG_LOG_CHANNEL_ID)
            if log_ch:
                embed = discord.Embed(title="🆕 มีสมาชิกลงทะเบียนใหม่!", color=0x00ff00)
                embed.add_field(name="ชื่อ IC", value=f"```\n{self.ic_name.value}\n```", inline=False)
                embed.add_field(name="ข้อมูล", value=f"อายุ: {self.ic_age.value} | สูง: {self.ic_height.value}", inline=True)
                embed.add_field(name="Steam", value=f"[คลิกดูโปรไฟล์]({self.steam_url.value})", inline=True)
                embed.set_footer(text=f"By p.hxmster | {now}")
                await log_ch.send(embed=embed)

            await interaction.response.send_message("✅ ลงทะเบียนสำเร็จ! ข้อมูลถูกส่งให้แอดมินแล้ว", ephemeral=True)
        except:
            await interaction.response.send_message("❌ กรอกข้อมูลผิดพลาด (อายุ/ส่วนสูง ต้องเป็นตัวเลข)", ephemeral=True)

# --- สร้าง View ที่มีปุ่มกด ---
class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # timeout=None ทำให้ปุ่มไม่หมดอายุ

    @discord.ui.button(label='📝 ลงทะเบียนเข้าเมือง', style=discord.ButtonStyle.success, custom_id='reg_btn')
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal())

@bot.event
async def on_ready():
    bot.add_view(RegisterView()) # ทำให้ปุ่มทำงานได้แม้บอทรีสตาร์ท
    print(f'✅ บอทปุ่มกด FiveM พร้อมใช้งาน! | p.hxmster')

# --- คำสั่งสร้างปุ่ม (พิมพ์แค่ครั้งเดียวตอนเริ่ม) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🏢 ระบบลงทะเบียนประชากร FiveM",
        description="กรุณากดปุ่มด้านล่างเพื่อทำการลงทะเบียนเข้าเมือง\nข้อมูลจะถูกส่งให้ทีมงานตรวจสอบโดยตรง",
        color=0x2f3136
    )
    # ใส่รูปภาพตกแต่ง (เปลี่ยน URL รูปได้ตามใจชอบ)
    embed.set_image(url="https://auto.creavite.co/api/out/1Nt54ky9V3Yetcqd58_static.png") 
    embed.set_footer(text="Created by p.hxmster | 30/03/2026")
    
    await ctx.send(embed=embed, view=RegisterView())
    await ctx.message.delete()

bot.run(TOKEN)
