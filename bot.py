import discord
from discord.ext import commands
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Evento: quando o bot ficar online
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

# Comando /painel
@bot.tree.command(name="painel", description="Exibe o painel de controle")
async def painel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Painel de Controle",
        description="Bem-vindo ao painel do bot!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Comando de anúncio", value="Use `/anuncio` para enviar anúncios.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Comando /anuncio
@bot.tree.command(name="anuncio", description="Envia um anúncio em um canal específico")
@app_commands.describe(canal="Canal onde o anúncio será enviado", mensagem="Mensagem do anúncio")
async def anuncio(interaction: discord.Interaction, canal: discord.TextChannel, mensagem: str):
    try:
        embed = discord.Embed(
            title="📢 Anúncio",
            description=mensagem,
            color=discord.Color.gold()
        )
        await canal.send(embed=embed)
        await interaction.response.send_message(f"✅ Anúncio enviado em {canal.mention}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao enviar anúncio: {e}", ephemeral=True)

# Iniciar o bot
import os
TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    print("❌ ERRO: Variável de ambiente DISCORD_TOKEN não configurada no Render.")
else:
    bot.run(TOKEN)
