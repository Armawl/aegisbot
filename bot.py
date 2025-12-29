import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Serveur premium
PREMIUM_SERVERS = [
    1455308297770107055
]

# Dictionnaire des mots interdits premium
premium_bad_words = {}

# Dictionnaire pour suivre les infractions par membre
infractions = {}

# Durées progressives des mutes en secondes
MUTE_DURATIONS = [5, 30, 300, 1800, 10800, 86400]  # 5s, 30s, 5min, 30min, 3h, 1j

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

    # Supprimer le message si mot banni (premium)
    if is_premium(guild.id):
        bad_words = premium_bad_words.get(guild.id, [])
        if any(word in content for word in bad_words):
            await message.delete()
            await progressive_mute(member, guild)
            return

    await bot.process_commands(message)

async def progressive_mute(member, guild):
    user_id = member.id
    infractions.setdefault(user_id, 0)
    idx = min(infractions[user_id], len(MUTE_DURATIONS)-1)
    duration = MUTE_DURATIONS[idx]
    infractions[user_id] += 1

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
    
    # Message dans le salon
    if guild.system_channel:
        await guild.system_channel.send(
            f"🔇 {member.mention} has been muted for {duration} seconds due to banned words."
        )
    
    # Message privé
    try:
        await member.send(f"You have been muted for {duration} seconds due to banned words.")
    except:
        pass

    await asyncio.sleep(duration)

    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        try:
            await member.send("✅ You have been unmuted.")
        except:
            pass

# Commande pour ajouter un mot banni (admin only)
@bot.command()
@commands.has_permissions(administrator=True)
async def addword(ctx, *, word):
    if not is_premium(ctx.guild.id):
        await ctx.send("❌ This feature is premium only.")
        return

    premium_bad_words.setdefault(ctx.guild.id, [])
    premium_bad_words[ctx.guild.id].append(word.lower())
    await ctx.send(f"✅ Added `{word}` to banned words.")

# Commande pour supprimer un mot banni (admin only)
@bot.command()
@commands.has_permissions(administrator=True)
async def removeword(ctx, *, word):
    if not is_premium(ctx.guild.id):
        await ctx.send("❌ This feature is premium only.")
        return

    bad_words = premium_bad_words.get(ctx.guild.id, [])
    if word.lower() in bad_words:
        bad_words.remove(word.lower())
        await ctx.send(f"✅ Removed `{word}` from banned words.")
    else:
        await ctx.send(f"❌ `{word}` is not in the banned words list.")

bot.run(os.getenv("DISCORD_TOKEN"))
