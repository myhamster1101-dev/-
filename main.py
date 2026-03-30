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

# --- Variables จาก Railway ---
TOKEN = os.getenv('TOKEN')
REG_LOG_CHANNEL_ID = int(os.getenv('REG_LOG_CHANNEL_ID')) if os.getenv('REG_LOG_CHANNEL_ID') else None

# --- หน้าต่างกรอกข้อมูล (Modal) ---
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

            # --- ส่งข้อมูลไปยังห้องแจ้งข้อมูล (REG_LOG_CHANNEL_ID) ---
            log_ch = bot.get_channel(REG_LOG_CHANNEL_ID)
            if log_ch:
                embed = discord.Embed(title="🆕 พบสมาชิกลงทะเบียนใหม่!", color=0x3498db, timestamp=datetime.now())
                embed.add_field(name="👤 ผู้ลงทะเบียน", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
                embed.add_field(name="🏷️ ชื่อในเมือง (IC)", value=f"```\n{self.ic_name.value}\n```", inline=False)
                embed.add_field(name="🎂 อายุใน IC", value=f"{self.ic_age.value} ปี", inline=True)
                embed.add_field(name="📏 ส่วนสูง", value=f"{self.ic_height.value} ซม.", inline=True)
                embed.add_field(name="🔗 Steam Profile", value=f"[คลิกเปิดโปรไฟล์]({self.steam_url.value})", inline=False)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.set_footer(text=f"System by p.hxmster | {now}")
                await log_ch.send(embed=embed)

            await interaction.response.send_message("✅ ลงทะเบียนสำเร็จ! ข้อมูลถูกส่งให้แอดมินตรวจสอบแล้วครับ", ephemeral=True)
        except Exception as e:
            print(f"Error: {e}")
            await interaction.response.send_message("❌ เกิดข้อผิดพลาด กรุณากรอกอายุและส่วนสูงเป็นตัวเลขเท่านั้น", ephemeral=True)

# --- ระบบปุ่มกดถาวร ---
class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='📝 คลิกที่นี่เพื่อลงทะเบียน', style=discord.ButtonStyle.success, custom_id='reg_btn_v2')
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegisterModal())

@bot.event
async def on_ready():
    bot.add_view(RegisterView())
    print(f'✅ FiveM Register Bot Online!')
    print(f'👤 Created by p.hxmster | 30/03/2026')

# --- คำสั่งสร้างปุ่ม (!setup) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🌟 ระบบลงทะเบียนประชากร FiveM 🌟",
        description="ยินดีต้อนรับสู่เมืองของเรา! กรุณากดปุ่มด้านล่างเพื่อกรอกข้อมูลลงทะเบียน\n\n**กรุณาเตรียมข้อมูลดังนี้:**\n1. ชื่อ-นามสกุล (IC)\n2. อายุ และ ส่วนสูง\n3. ลิงก์ Steam Profile ของคุณ",
        color=0xf1c40f
    )
    # --- แก้ไขลิงก์รูปตรงนี้ ---
    # ถ้ายังไม่มีรูป ให้ใช้ลิงก์ภาพเมืองสวยๆ จากอินเทอร์เน็ตมาใส่แทนครับ
    embed.set_image(url="https://i.imgur.com/rN975W6.png") 
    embed.set_footer(text="Created by p.hxmster | 30/03/2026")
    
    await ctx.send(embed=embed, view=RegisterView())
    await ctx.message.delete()

bot.run(TOKEN)
