import discord
from discord.ext import commands, tasks
import time
import datetime
import os
import json
from dotenv import load_dotenv
from keep_alive import keep_alive  # Flask server

load_dotenv()

start_time = time.time()

RESET_FILE = "reset_data.json"
reset_data = {}

MAX_RESETS_PER_DAY = 6
COOLDOWN_HOURS = 2

# Load saved resets
def load_reset_data():
    global reset_data
    if os.path.exists(RESET_FILE):
        with open(RESET_FILE, "r") as f:
            reset_data.update(json.load(f))
            print("[LOG] Reset data loaded.")

# Save resets to file
def save_reset_data():
    with open(RESET_FILE, "w") as f:
        json.dump(reset_data, f)

def get_uptime():
    return str(datetime.timedelta(seconds=int(time.time() - start_time)))

# --- Discord Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

recent_resets = []

def log_reset(user_id):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    recent_resets.append(f"{timestamp} - User ID: {user_id}")
    if len(recent_resets) > 10:
        recent_resets.pop(0)

def reset_daily_counts():
    for user in reset_data:
        reset_data[user]["count"] = 0
    save_reset_data()
    print("[LOG] Daily reset counts cleared.")

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

@bot.tree.command(name="ping", description="Check if the bot is alive")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is alive.")

async def try_reset(ctx_or_msg):
    user_id = str(ctx_or_msg.author.id)
    send = ctx_or_msg.send if isinstance(ctx_or_msg, commands.Context) else ctx_or_msg.channel.send

    now = datetime.datetime.utcnow()
    user_data = reset_data.get(user_id, {"count": 0, "last_reset": None})

    if user_data["last_reset"]:
        last_reset_time = datetime.datetime.fromisoformat(user_data["last_reset"])
        elapsed = now - last_reset_time
        if elapsed < datetime.timedelta(hours=COOLDOWN_HOURS):
            remaining = datetime.timedelta(hours=COOLDOWN_HOURS) - elapsed
            mins = int(remaining.total_seconds() // 60)
            await send(f"⏳ Please wait {mins} more minute(s) before resetting again.")
            return False

    if user_data["count"] >= MAX_RESETS_PER_DAY:
        await send(f"🚫 You have reached {MAX_RESETS_PER_DAY} HWID resets today.")
        return False

    user_data["count"] += 1
    user_data["last_reset"] = now.isoformat()
    reset_data[user_id] = user_data
    save_reset_data()
    log_reset(user_id)

    await send(f"✅ Done, Enjoy Universal Farm! You have {user_data['count']}/{MAX_RESETS_PER_DAY} resets left.")
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
            except:
                pass
    await bot.process_commands(message)

@bot.command()
async def uptime(ctx):
    await ctx.send(f"🕒 Bot has been alive for: `{get_uptime()}`")

# --- Start Flask Server ---
keep_alive(get_uptime, recent_resets)  # <- Pass values

# --- Run Bot ---
token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    print("❌ DISCORD_BOT_TOKEN not set")
else:
    load_reset_data()
    bot.run(token)
