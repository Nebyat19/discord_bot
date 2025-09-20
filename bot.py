import discord
from discord import app_commands
from discord.ext import commands
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from keep_alive import keep_alive

keep_alive()

# Get the token from environment variable
token = os.getenv('DISCORD_BOT_TOKEN')

# ---------------------- Intents ----------------------
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

VOICE_CHANNEL_ID = 1417512186456051824  # Replace with your VC ID
WHO_IS_HERE_CHANNEL_ID = 1417941986463191112  # Replace with your text channel ID
DATA_FILE = "attendance.json"

# ---------------------- Load Data ----------------------
try:
    with open(DATA_FILE, "r") as f:
        attendance = json.load(f)
except:
    attendance = {}

# ---------------------- Voice Join Event ----------------------
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == VOICE_CHANNEL_ID:
        if not before.channel or before.channel.id != VOICE_CHANNEL_ID:
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in attendance:
                attendance[today] = []
            if member.id not in attendance[today]:
                attendance[today].append(member.id)
                with open(DATA_FILE, "w") as f:
                    json.dump(attendance, f, indent=4)

                channel = bot.get_channel(WHO_IS_HERE_CHANNEL_ID)
                await channel.send(f"🎤 {member.mention} joined the session!")

# ---------------------- Slash Commands ----------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot logged in as {bot.user}")

@bot.tree.command(name="today", description="Show today's session participants")
async def today(interaction: discord.Interaction):
    today_date = datetime.now().strftime("%Y-%m-%d")
    users_ids = attendance.get(today_date, [])
    mentions = [f"<@{uid}>" for uid in users_ids]

    msg = "==========================\n"
    msg += f"📅 Today's Session Participants ({len(mentions)}):\n"
    msg += "\n".join(mentions)
    msg += "\n==========================\n"
    msg += f"🎉 {len(mentions)} friends joined today — awesome!"

    await interaction.response.send_message(msg)

@bot.tree.command(name="leaderboard", description="Show attendance leaderboard")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer()  # Acknowledge quickly

    streaks = {}
    for date, users_ids in attendance.items():
        for uid in users_ids:
            streaks[uid] = streaks.get(uid, 0) + 1

    sorted_streaks = sorted(streaks.items(), key=lambda x: x[1], reverse=True)

    msg = "==========================\n"
    msg += "🏆 Our Voice Session Champions \n\n"

    for i, (uid, count) in enumerate(sorted_streaks, 1):
        member = interaction.guild.get_member(uid)
        if not member:
            continue
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}️⃣"
        msg += f"{medal} {member.mention} - {count} days\n"

    msg += "==========================\n"
    msg += "🔥 Keep joining daily and climb the leaderboard!"

    # Use followup instead of response
    await interaction.followup.send(msg)
# ---------------------- Run Bot ----------------------
bot.run(token)

