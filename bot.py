import discord
from discord.ext import tasks
from discord.ui import View, Button, Modal, TextInput
import datetime
import pytz
import os  # para pegar o token do ambiente no Render

GUILD_ID = 1391955329545146498  # seu ID da guild

# IDs dos canais que você quer controlar
CANAL_IDS = [
    1402823888966123550,  # este apaga mensagens
    1391958002403246141,  # este apaga mensagens
    1391958004219379878,
    1393965566351380521,
    1403220321301168138,
    1402469246218403880,
    1391957998112342196
]

# Só estes vão apagar mensagens
CANAIS_APAGAR = [1391958002403246141, 1402823888966123550]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# Horários iniciais
fechar_hora = 0
fechar_minuto = 30
abrir_hora = 10
abrir_minuto = 0

# Fuso horário de Brasília
fuso = pytz.timezone("America/Sao_Paulo")

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"📌 {len(synced)} comandos sincronizados com a guild {GUILD_ID}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")
    check_schedule.start()

# ================== TAREFA DE HORÁRIO ==================
@tasks.loop(minutes=1)
async def check_schedule():
    agora = datetime.datetime.now(fuso)
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    canais = [guild.get_channel(cid) for cid in CANAL_IDS if guild.get_channel(cid) is not None]

    if agora.hour == fechar_hora and agora.minute == fechar_minuto:
        for canal in canais:
            if canal.id in CANAIS_APAGAR:
                try:
                    await canal.purge(limit=None)
                except Exception as e:
                    print(f"[ERRO] purge em {canal.name} -> {e}")

            await canal.set_permissions(guild.default_role, send_messages=False)
            await canal.send(
                f"🔒 Canal Fechado\n"
                f"{'Mensagens apagadas.' if canal.id in CANAIS_APAGAR else 'Mensagens preservadas.'} "
                f"Reabre às {abrir_hora:02d}:{abrir_minuto:02d} (Horário de Brasília)."
            )

    if agora.hour == abrir_hora and agora.minute == abrir_minuto:
        for canal in canais:
            await canal.set_permissions(guild.default_role, send_messages=True)
            await canal.send(
                f"🔓 Canal Aberto\nSerá fechado às {fechar_hora:02d}:{fechar_minuto:02d} (Horário de Brasília)."
            )

# ================== MODALS ==================
class EditarHorarioModal(Modal):
    def __init__(self):
        super().__init__(title="Editar Horários")
        self.add_item(TextInput(label="Hora para fechar (0-23)", placeholder="0"))
        self.add_item(TextInput(label="Minuto para fechar (0-59)", placeholder="30"))
        self.add_item(TextInput(label="Hora para abrir (0-23)", placeholder="10"))
        self.add_item(TextInput(label="Minuto para abrir (0-59)", placeholder="0"))

    async def on_submit(self, interaction: discord.Interaction):
        global fechar_hora, fechar_minuto, abrir_hora, abrir_minuto
        try:
            fechar_hora = int(self.children[0].value)
            fechar_minuto = int(self.children[1].value)
            abrir_hora = int(self.children[2].value)
            abrir_minuto = int(self.children[3].value)
            await interaction.response.send_message(
                f"✅ Horários atualizados:\nFechar: {fechar_hora:02d}:{fechar_minuto:02d}\nAbrir: {abrir_hora:02d}:{abrir_minuto:02d}",
                ephemeral=True
            )
        except Exception as e:
            print(f"[ERRO] Modal Editar Horário -> {e}")
            await interaction.response.send_message("❌ Erro: insira números válidos!", ephemeral=True)

class AnunciarModal(Modal):
    def __init__(self):
        super().__init__(title="Anunciar Mensagem")
        self.add_item(TextInput(label="ID do canal", placeholder="Digite o ID"))
        self.add_item(TextInput(label="Mensagem", style=discord.TextStyle.long, placeholder="Digite a mensagem"))

    async def on_submit(self, interaction: discord.Interaction):
        guild = bot.get_guild(GUILD_ID)
        try:
            canal_id = int(self.children[0].value)
            canal = guild.get_channel(canal_id)
            if canal:
                await canal.send(self.children[1].value)
                await interaction.response.send_message("📢 Mensagem enviada!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Canal não encontrado.", ephemeral=True)
        except Exception as e:
            print(f"[ERRO] Modal Anunciar -> {e}")
            await interaction.response.send_message("❌ ID inválido ou erro ao enviar.", ephemeral=True)

# ================== VIEW (BOTÕES) ==================
class PainelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar canais", style=discord.ButtonStyle.danger)
    async def fechar_canais(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            guild = bot.get_guild(GUILD_ID)
            canais = [guild.get_channel(cid) for cid in CANAL_IDS if guild.get_channel(cid) is not None]

            for canal in canais:
                if canal.id in CANAIS_APAGAR:
                    try:
                        await canal.purge(limit=None)
                    except Exception as e:
                        print(f"[ERRO] purge em {canal.name} -> {e}")

                await canal.set_permissions(guild.default_role, send_messages=False)
                await canal.send(
                    f"🔒 Fechado manualmente por {interaction.user.mention}\n"
                    f"{'(Mensagens apagadas)' if canal.id in CANAIS_APAGAR else '(Mensagens preservadas)'}"
                )

            await interaction.followup.send("🔒 Canais fechados! (mensagens só apagadas nos permitidos)", ephemeral=True)
        except Exception as e:
            print(f"[ERRO] Botão Fechar -> {e}")
            await interaction.followup.send("❌ Erro ao fechar canais.", ephemeral=True)

    @discord.ui.button(label="Abrir canais", style=discord.ButtonStyle.success)
    async def abrir_canais(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            guild = bot.get_guild(GUILD_ID)
            canais = [guild.get_channel(cid) for cid in CANAL_IDS if guild.get_channel(cid) is not None]
            for canal in canais:
                await canal.set_permissions(guild.default_role, send_messages=True)
                await canal.send(f"🔓 Aberto manualmente por {interaction.user.mention}")
            await interaction.followup.send("🔓 Canais abertos!", ephemeral=True)
        except Exception as e:
            print(f"[ERRO] Botão Abrir -> {e}")
            await interaction.followup.send("❌ Erro ao abrir os canais.", ephemeral=True)

    @discord.ui.button(label="Editar horários", style=discord.ButtonStyle.primary)
    async def editar_horarios(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        try:
            await interaction.response.send_modal(EditarHorarioModal())
        except Exception as e:
            print(f"[ERRO] Botão Editar Horário -> {e}")
            await interaction.followup.send("❌ Erro ao abrir o modal.", ephemeral=True)

    @discord.ui.button(label="Anunciar", style=discord.ButtonStyle.secondary)
    async def anunciar(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
        try:
            await interaction.response.send_modal(AnunciarModal())
        except Exception as e:
            print(f"[ERRO] Botão Anunciar -> {e}")
            await interaction.followup.send("❌ Erro ao abrir o modal.", ephemeral=True)

# ================== SLASH COMMAND ==================
@tree.command(name="painel", description="Mostra o painel de controle dos canais", guild=discord.Object(id=GUILD_ID))
async def painel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você não tem permissão.", ephemeral=True)
        return

    view = PainelView()
    try:
        await interaction.response.send_message("📋 Painel de controle:", view=view, ephemeral=True)
    except Exception as e:
        print(f"[ERRO] Comando /painel -> {e}")
        if interaction.response.is_done():
            await interaction.followup.send("❌ Erro ao abrir o painel.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro ao abrir o painel.", ephemeral=True)

# ================== INICIAR ==================
TOKEN = os.getenv("DISCORD_TOKEN")  # variável de ambiente no Render

if TOKEN is None:
    print("❌ ERRO: Variável de ambiente DISCORD_TOKEN não encontrada!")
else:
    bot.run(TOKEN)
