import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

PREMIUM_SERVERS = [
    # example: 123456789012345678
]

spam_counter = {}

def is_premium(server_id):
    return server_id in PREMIUM_SERVERS

@bot.event
async def on_ready():
    print(f"AegisBot connected as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild = message.guild
    member = message.author
    content = message.content.lower()

    # Auto-spam (FREE)
    user_id = member.id
    spam_counter.setdefault(user_id, 0)
    spam_counter[user_id] += 1

    if spam_counter[user_id] > 5:
        await mute_user(message, "Spam detected")
        spam_counter[user_id] = 0
        return

    await bot.process_commands(message)

async def mute_user(message, reason):
    guild = message.guild
    member = message.author

    muted_role = discord.utils.get(guild.roles, name="Muted")
    if not muted_role:
        muted_role = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(
                muted_role,
                send_messages=False,
                speak=False
            )

    await member.add_roles(muted_role)
    await message.channel.send(
        f"🔇 {member.mention} has been muted ({reason})."
    )
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! ✅")
bot.run(os.getenv("DISCORD_TOKEN"))
