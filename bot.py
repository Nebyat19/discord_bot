import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client
from keep_alive import keep_alive

# Load environment variables from .env file
load_dotenv()
keep_alive()

# ---------------------- Supabase Setup ----------------------
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# ---------------------- Bot Setup ----------------------
token = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

VOICE_CHANNEL_IDS = {
    1417512186456051824: "Daily Session 1",  # Channel ID: Channel Name
    1418305785515086014: "Daily Session 2",
    1418509411722465423: "Daily Session 3"
}
WHO_IS_HERE_CHANNEL_ID = 1417941986463191112

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id in VOICE_CHANNEL_IDS:
        if not before.channel or before.channel.id not in VOICE_CHANNEL_IDS:
            today = datetime.now().strftime("%Y-%m-%d")

            existing = supabase.table("attendance").select("*") \
                .eq("user_id", member.id).eq("date", today).execute()

            if not existing.data:
                supabase.table("attendance").insert({
                    "user_id": member.id,
                    "date": today
                }).execute()

                channel = bot.get_channel(WHO_IS_HERE_CHANNEL_ID)
                channel_name = VOICE_CHANNEL_IDS[after.channel.id]
                await channel.send(f"🎤 {member.mention} joined the {channel_name}")

# ---------------------- Slash Commands ----------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot logged in as {bot.user}")

@bot.tree.command(name="today", description="Show today's session participants")
async def today(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("⚠️ This command can only be used in a server, not in DMs.")
        return

    today_date = datetime.now().strftime("%Y-%m-%d")
    data = supabase.table("attendance").select("user_id").eq("date", today_date).execute()
    users_ids = [row["user_id"] for row in data.data]

    if not users_ids:
        await interaction.response.send_message("No one has joined today's session yet.")
        return

    mentions = [f"<@{uid}>" for uid in users_ids]

    msg = "==========================\n"
    msg += f"📅 Today's Session Participants ({len(mentions)}):\n\n"
    msg += "\n".join(mentions)
    msg += "\n\n==========================\n"
    msg += f"🎉 {len(mentions)} friends joined today — awesome!"

    await interaction.response.send_message(msg)

@bot.tree.command(name="leaderboard", description="Show attendance leaderboard")
async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer()

    if not interaction.guild:
        await interaction.followup.send("⚠️ This command can only be used in a server, not in DMs.")
        return

    data = supabase.table("attendance").select("user_id").execute()
    from collections import Counter
    streaks = Counter([row["user_id"] for row in data.data])
    sorted_streaks = sorted(streaks.items(), key=lambda x: x[1], reverse=True)[:20]  # Limit to top 20

    msg = "==========================\n"
    msg += "🏆 Top 20 Voice Session Champions\n\n"

    last_count = None
    last_medal = None
    rank = 0

    for uid, count in sorted_streaks:
        member = interaction.guild.get_member(uid)
        if not member:
            continue

        if count == last_count:
            medal = last_medal
        else:
            rank += 1
            if rank == 1:
                medal = "🥇"
            elif rank == 2:
                medal = "🥈"
            elif rank == 3:
                medal = "🥉"
            else:
                medal = f"{rank}️⃣"

        msg += f"{medal} {member.display_name} - {count} days\n"
        last_count = count
        last_medal = medal

    total_participants = len(streaks.keys())
    msg += "\n==========================\n"
    msg += f"🔥 Keep joining and climb higher!\n"
    msg += f"👥 Total participants: {total_participants}"

    if len(msg) > 2000:
        msg = msg[:1997] + "..."

    await interaction.followup.send(msg)



# give role to user if they have joined for 100 days
# give role if user joined voice channel for 5 days

# ---------------------- Run Bot ----------------------
bot.run(token)
