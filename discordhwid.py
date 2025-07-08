import discord
from discord.ext import commands, tasks
import time
import datetime
import os
from dotenv import load_dotenv
from keep_alive import keep_alive  # ⬅️ Import keep_alive

load_dotenv()

start_time = time.time()

def get_uptime():
    return str(datetime.timedelta(seconds=int(time.time() - start_time)))

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

reset_data = {}
MAX_RESETS_PER_DAY = 6
COOLDOWN_HOURS = 2

def reset_daily_counts():
    reset_data.clear()
    print("[LOG] Reset daily reset counts.")

@tasks.loop(hours=24)
async def daily_reset_task():
    reset_daily_counts()

@tasks.loop(minutes=1)
async def log_uptime():
    print(f"[LOG] Uptime: {get_uptime()}")

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"⚠️ Failed to sync commands: {e}")
    log_uptime.start()
    daily_reset_task.start()

# --- Slash Command: /ping ---
@bot.tree.command(name="ping", description="Check if the bot is alive")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! The bot is alive.")

# --- HWID Reset Logic ---
async def try_reset(ctx_or_message):
    user_id = None
    send_func = None

    if isinstance(ctx_or_message, commands.Context):
        user_id = ctx_or_message.author.id
        send_func = ctx_or_message.send
    else:
        user_id = ctx_or_message.author.id
        send_func = ctx_or_message.channel.send

    now = datetime.datetime.utcnow()
    user_data = reset_data.get(user_id, {"count": 0, "last_reset": None})

    if user_data["last_reset"]:
        elapsed = now - user_data["last_reset"]
        if elapsed < datetime.timedelta(hours=COOLDOWN_HOURS):
            remaining = datetime.timedelta(hours=COOLDOWN_HOURS) - elapsed
            minutes = int(remaining.total_seconds() // 60)
            await send_func(f"⏳ Please wait {minutes} more minute(s) before resetting again.")
            return False

    if user_data["count"] >= MAX_RESETS_PER_DAY:
        await send_func(f"🚫 You have reached the maximum of {MAX_RESETS_PER_DAY} HWID resets today. Try again tomorrow.")
        return False

    user_data["count"] += 1
    user_data["last_reset"] = now
    reset_data[user_id] = user_data

    await send_func(f"✅ HWID reset done! You have used {user_data['count']}/{MAX_RESETS_PER_DAY} resets today.")
    return True

@bot.command()
async def force_resethwid(ctx):
    await try_reset(ctx)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    if "hwid reset" in content or bot.user in message.mentions:
        success = await try_reset(message)
        if success:
            try:
                await message.reply(f"/force-resethwid user:{message.author.id}")
                await message.add_reaction("✅")
                await message.channel.send("✅ Done, Enjoy Universal Farm!")
            except:
                pass
    await bot.process_commands(message)

@bot.command()
async def uptime(ctx):
    await ctx.send(f"🕒 Bot has been alive for: `{get_uptime()}`")

# --- Start Flask Server to Keep Alive ---
keep_alive()  # 🟢 This starts the Flask server for Render

# --- Run Bot ---
token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    print("❌ DISCORD_BOT_TOKEN is not set")
else:
    bot.run(token)
