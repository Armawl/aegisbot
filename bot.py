import discord
from discord.ext import commands
import os

# Intents nécessaires pour lire les messages et gérer les rôles
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Liste des serveurs premium (mettre l'ID des serveurs qui paient)
PREMIUM_SERVERS = [
    # Exemple : 123456789012345678
]

# Dictionnaire des mots interdits premium
premium_bad_words = {
    # server_id: ["badword1", "badword2"]
}

# Tracking du spam (FREE)
spam_counter = {}

# Fonction pour vérifier si un serveur est premium
def is_premium(server_id):
    return server_id in PREMIUM_SERVERS

# Événement au démarrage
@bot.event
async def on_ready():
    print(f"AegisBot connected as {bot.user}")

# Événement pour gérer les messages
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild = message.guild
    member = message.author
    content = message.content.lower()

    # Auto-spam (gratuit)
    user_id = member.id
    spam_counter.setdefault(user_id, 0)
    spam_counter[user_id] += 1

    if spam_counter[user_id] > 5:
        await mute_user(message, "Spam detected")
        spam_counter[user_id] = 0
        return

    # Premium bad words
    if is_premium(guild.id):
        bad_words = premium_bad_words.get(guild.id, [])
        if any(word in content for word in bad_words):
            await mute_user(message, "Used banned word")
            return

    await bot.process_commands(message)

# Fonction pour mute un utilisateur
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

# Commande pour ajouter un mot interdit (admins only)
@bot.command()
@commands.has_permissions(administrator=True)
async def addword(ctx, *, word):
    if not is_premium(ctx.guild.id):
        await ctx.send("❌ This feature is premium only.")
        return

    premium_bad_words.setdefault(ctx.guild.id, [])
    premium_bad_words[ctx.guild.id].append(word.lower())
    await ctx.send(f"✅ Added `{word}` to banned words.")

# Commande pour supprimer un mot interdit (admins only)
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

# Démarrage du bot avec le token sécurisé
bot.run(os.getenv("DISCORD_TOKEN"))
