import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

TARGET_CHANNEL_ID = 1339597202774950070

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    has_attachments = any(
        attachment.content_type and attachment.content_type.startswith('image')
        for attachment in message.attachments
    )

    if has_attachments:
        thread = await message.create_thread(
            name=f"{message.author.display_name}のすばらしい絵！",
            auto_archive_duration=60
        )
        print(f"🧵 スレッドを作成: {thread.name}")
    else:
        await message.delete()
        print(f"🗑️ メッセージ削除: {message.content}")

bot.run(TOKEN)