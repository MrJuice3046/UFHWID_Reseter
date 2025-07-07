import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread
import time
import datetime
import os
from dotenv import load_dotenv  # <-- Add this

# ---- Load .env file ----
load_dotenv()  # <-- Load environment variables from .env file

# ---- Track bot start time ----
start_time = time.time()

def get_uptime():
    seconds = int(time.time() - start_time)
    return str(datetime.timedelta(seconds=seconds))

# ---- Flask keep-alive server ----
app = Flask('')

@app.route('/')
def home():
    return f"✅ Bot is alive! Uptime: {get_uptime()}"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ---- Discord bot setup ----
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

# ---- Log uptime every 1 min ----
@tasks.loop(minutes=1)
async def log_uptime():
    print(f"[LOG] Uptime: {get_uptime()}")

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    log_uptime.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    if "hwid reset" in content or bot.user in message.mentions:
        await message.reply(f"/force-resethwid user:{message.author.id}")
        await message.add_reaction("✅")
        await message.channel.send("✅ Done, Enjoy Universal Farm!")

    await bot.process_commands(message)

@bot.command()
async def uptime(ctx):
    await ctx.send(f"🕒 Bot has been alive for: `{get_uptime()}`")

# ---- Start everything ----
keep_alive()

# Load token from environment variable
bot_token = os.getenv('DISCORD_BOT_TOKEN')
if bot_token is None:
    print("❌ DISCORD_BOT_TOKEN is not set in the environment.")
else:
    bot.run(bot_token)
