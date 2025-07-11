import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
from keep_alive import keep_alive

FARMING_ROLE_ID = 1354047540869337089
DATA_FILE = "farmings.json"

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Load data from file
def load_data():
    global farmings
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            farmings = json.load(f)
    else:
        farmings = {}

# Save data to file
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(farmings, f, indent=2)

# Generate a random 10-digit farming code
def generate_code():
    return str(random.randint(10**9, 10**10 - 1))

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="create", description="Create a new farming session")
@app_commands.checks.has_role(FARMING_ROLE_ID)
async def create(interaction: discord.Interaction):
    load_data()
    code = generate_code()
    farmings[code] = {
        "creator_id": interaction.user.id,
        "status": "open",
        "participants": {}
    }
    save_data()
    await interaction.response.send_message(f"✅ Farming session created with code: `{code}`")

@tree.command(name="join", description="Join an open farming session")
@app_commands.describe(code="10-digit farming code", nickname="Your nickname for the farming")
async def join(interaction: discord.Interaction, code: str, nickname: str):
    load_data()
    if code not in farmings:
        await interaction.response.send_message("❌ Invalid farming code.")
        return

    session = farmings[code]
    if session["status"] != "open":
        await interaction.response.send_message("❌ This farming session is closed.")
        return

    if str(interaction.user.id) in session["participants"]:
        await interaction.response.send_message("❌ You have already joined this farming session.")
        return

    session["participants"][str(interaction.user.id)] = nickname
    save_data()
    await interaction.response.send_message(f"✅ You joined farming `{code}` as **{nickname}**.")

@tree.command(name="close", description="Close a farming session")
@app_commands.checks.has_role(FARMING_ROLE_ID)
@app_commands.describe(code="10-digit farming code")
async def close(interaction: discord.Interaction, code: str):
    load_data()
    if code not in farmings:
        await interaction.response.send_message("❌ Invalid farming code.")
        return

    farmings[code]["status"] = "closed"
    save_data()
    await interaction.response.send_message(f"🔒 Farming session `{code}` has been closed.")

@tree.command(name="view", description="View a farming session")
@app_commands.describe(code="10-digit farming code")
async def view(interaction: discord.Interaction, code: str):
    load_data()
    if code not in farmings:
        await interaction.response.send_message("❌ Invalid farming code.")
        return

    session = farmings[code]
    status = session["status"]
    participants = session["participants"]
    if not participants:
        members = "No participants yet."
    else:
        members = "\n".join([f"<@{uid}> — **{nick}**" for uid, nick in participants.items()])

    embed = discord.Embed(
        title=f"📋 Farming Session `{code}`",
        description=f"**Status:** {status.upper()}",
        color=discord.Color.green() if status == "open" else discord.Color.red()
    )
    embed.add_field(name="Participants", value=members, inline=False)

    await interaction.response.send_message(embed=embed)

@tree.command(name="list", description="Get a random nickname list from a farming session")
@app_commands.describe(code="10-digit farming code")
async def list_command(interaction: discord.Interaction, code: str):
    load_data()

    if code not in farmings:
        await interaction.response.send_message("❌ Invalid farming code.")
        return

    session = farmings[code]
    participants = session["participants"]

    if not participants:
        await interaction.response.send_message("❌ No participants in this farming session.")
        return

    nicknames = list(participants.values())
    random.shuffle(nicknames)

    result = "\n".join([f"{i+1}. {nick}" for i, nick in enumerate(nicknames)])

    embed = discord.Embed(
        title=f"🎲 Random Farming Order for `{code}`",
        description=result,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed)

# Handle missing role errors
@create.error
@close.error
async def role_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingRole):
        await interaction.response.send_message("❌ You don’t have permission to use this command.")

# Start the keep-alive server and run the bot
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))