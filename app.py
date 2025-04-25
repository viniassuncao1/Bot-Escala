import discord
from discord import app_commands
from discord.ui import Button, View
import os
from dotenv import load_dotenv
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

# ID do canal de logs
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
# ID do canal da escala
ESCALA_CHANNEL_ID = int(os.getenv("ESCALA_CHANNEL_ID", 0))
# URL da logo
LOGO_URL = "https://cdn.discordapp.com/attachments/1195135499455697068/1303084925179924591/logo_pmc.png?ex=680be868&is=680a96e8&hm=8dc83d13a910abc5516cf3de5dbaed3f8aee53ac3217fab7ac2676ea3f64a8a8&"
ALTO_COMANDO_ROLE_ID = int(os.getenv("ALTO_COMANDO_ROLE_ID", "0"))

SHEETS_JSON = 'metropolerp-455022-91d42624740f.json'
SHEETS_NOME = 'Escala de Patrulha'

# ========== ESCALA DE PRESENÇA ==========
ESCALA_MAX = 3  # Limite de pessoas na escala
escala_participantes = []  # Lista de dicts: {id, nome, entrada, responsavel}
escala_msg_id = None  # Para manter a mensagem fixa

# Função para registrar no Google Sheets (apenas na saída)
async def registrar_no_sheets_saida(nome, horario_entrada, horario_saida, tempo_total):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SHEETS_JSON, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEETS_NOME).sheet1  # Usa a primeira aba
    sheet.append_row([
        nome,
        horario_entrada,
        horario_saida,
        tempo_total
    ])

class EntrarEscalaButton(Button):
    def __init__(self):
        super().__init__(label="Entrar na Escala", style=discord.ButtonStyle.success, custom_id="entrar_escala")

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=False)
            user_id = interaction.user.id
            nome = interaction.user.display_name
            if any(p['id'] == user_id for p in escala_participantes):
                await interaction.followup.send("Você já está na escala!", ephemeral=True)
                return
            if len(escala_participantes) >= ESCALA_MAX:
                await interaction.followup.send("O limite de policiais na escala foi atingido!", ephemeral=True)
                return
            responsavel = len(escala_participantes) == 0
            agora = datetime.now()
            escala_participantes.append({
                'id': user_id,
                'nome': nome,
                'entrada': agora,
                'responsavel': responsavel
            })
            canal_log = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if canal_log:
                embed_log = discord.Embed(
                    title="✅ Entrada na Escala",
                    description=f"**{nome}** entrou na escala!",
                    color=discord.Color.green()
                )
                if responsavel:
                    embed_log.add_field(name="Responsável", value="👑 Sim", inline=True)
                embed_log.timestamp = agora
                await canal_log.send(embed=embed_log)
            await atualizar_escala_embed(interaction)
        except Exception as e:
            print(f"Erro no callback EntrarEscalaButton: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("Ocorreu um erro ao processar sua entrada na escala.", ephemeral=True)
                else:
                    await interaction.followup.send("Ocorreu um erro ao processar sua entrada na escala.", ephemeral=True)
            except Exception:
                pass

class SairEscalaButton(Button):
    def __init__(self):
        super().__init__(label="Sair da Escala", style=discord.ButtonStyle.danger, custom_id="sair_escala")

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=False)
            user_id = interaction.user.id
            participante = next((p for p in escala_participantes if p['id'] == user_id), None)
            if not participante:
                await interaction.followup.send("Você não está na escala.", ephemeral=True)
                return
            agora = datetime.now()
            tempo_total = agora - participante['entrada']
            escala_participantes.remove(participante)
            canal_log = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if canal_log:
                embed_log = discord.Embed(
                    title="🚪 Saída da Escala",
                    description=f"**{interaction.user.display_name}** saiu da escala.",
                    color=discord.Color.orange()
                )
                embed_log.add_field(name="Tempo total", value=f"`{str(tempo_total).split('.')[0]}`", inline=True)
                if participante.get('responsavel', False):
                    embed_log.add_field(name="Responsável", value="👑 Sim", inline=True)
                embed_log.timestamp = agora
                await canal_log.send(embed=embed_log)
            await registrar_no_sheets_saida(
                interaction.user.display_name,
                participante['entrada'].strftime('%d/%m/%Y %H:%M:%S'),
                agora.strftime('%d/%m/%Y %H:%M:%S'),
                str(tempo_total).split('.')[0]
            )
            await atualizar_escala_embed(interaction)
        except Exception as e:
            print(f"Erro no callback SairEscalaButton: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("Ocorreu um erro ao processar sua saída da escala.", ephemeral=True)
                else:
                    await interaction.followup.send("Ocorreu um erro ao processar sua saída da escala.", ephemeral=True)
            except Exception:
                pass

async def atualizar_escala_embed(interaction):
    global escala_msg_id
    canal = interaction.guild.get_channel(ESCALA_CHANNEL_ID) or interaction.channel
    # Mensagem dinâmica da escala (compacta e bonita)
    embed = discord.Embed(
        title="🚨 ESCALA DE PRESENÇA - RECEPÇÃO  🚨",
        color=discord.Color.red()
    )
    embed.set_thumbnail(url=LOGO_URL)
    if escala_participantes:
        desc = ""
        for idx, p in enumerate(escala_participantes):
            if p['responsavel']:
                desc += f"🟢 <@{p['id']}> **(Responsável)** — Entrou: {p['entrada'].strftime('%H:%M:%S')}\n"
            else:
                desc += f"🔵 <@{p['id']}> — Entrou: {p['entrada'].strftime('%H:%M:%S')}\n"
        embed.description = desc
    else:
        embed.description = "📭 Ninguém está na escala no momento.\nClique em **Entrar na Escala** para ser o primeiro a assumir!"
    view = View(timeout=None)
    # Adiciona botão apenas na mensagem dinâmica
    if len(escala_participantes) < ESCALA_MAX:
        view.add_item(EntrarEscalaButton())
    for p in escala_participantes:
        if p['id'] == interaction.user.id:
            view.add_item(SairEscalaButton())
            break
    # Edita ou envia
    if escala_msg_id:
        try:
            msg = await canal.fetch_message(escala_msg_id)
            await msg.edit(embed=embed, view=view)
            await interaction.response.defer() if not interaction.response.is_done() else None
        except Exception as e:
            escala_msg_id = None
            print(f"Erro ao editar mensagem da escala: {e}")
    if not escala_msg_id:
        msg = await canal.send(embed=embed, view=view)
        escala_msg_id = msg.id
        try:
            await interaction.response.defer() if not interaction.response.is_done() else None
        except Exception:
            pass

async def garantir_mensagem_info(canal):
    info_title = "📋 Escala de Atendimento – Recepção 🚔  `BETA`"
    info_desc = (
        "🚨 **ATENÇÃO! A recepção é a linha de frente da nossa corporação.**\n"
        "Manter a escala ativa é essencial para o bom funcionamento do batalhão.\n\n"
        "👮‍♂️ **Presença de responsável (SD+) é obrigatória!**\n"
        "Nenhuma patrulha deve começar sem um policial qualificado presente.\n\n"
        "🚷 **Recrutas NUNCA devem ficar sozinhos na recepção.**\n"
        "Aguarde um superior iniciar a escala.\n\n"
        "🧍 **Limite máximo: 3 policiais simultâneos.**\n"
        "Ao atingir o limite, novas entradas serão bloqueadas até que haja vagas.\n\n"
        "🎖️ **O primeiro a entrar é automaticamente o responsável da escala.**\n"
        "Se não for SD+, aguarde.\n\n"
        "⏱️ **Permanência mínima recomendada: 1 hora.**\n"
        "Seu tempo será registrado automaticamente nos **logs e relatórios**.\n\n"
        "📲 **Use os botões abaixo para ENTRAR ou SAIR da escala.**\n"
        "Sua presença será monitorada com horário de entrada e saída.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ":information_source: **DÚVIDAS?** Procure: Mikaela Khakeesi ou Jake Machado"
    )
    async for msg in canal.history(limit=20):
        if msg.author == canal.guild.me and msg.embeds:
            if msg.embeds[0].title and "Escala de Atendimento" in msg.embeds[0].title:
                return  # Já existe
    embed = discord.Embed(title=info_title, description=info_desc, color=discord.Color.dark_blue())
    embed.set_thumbnail(url=LOGO_URL)
    await canal.send(embed=embed)

# Comando para iniciar a escala (admin)
@discord.app_commands.command(name="iniciar_escala", description="Posta a mensagem fixa da escala de presença.")
async def iniciar_escala(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Apenas administradores podem usar este comando.", ephemeral=True)
        return
    global escala_msg_id
    escala_participantes.clear()
    escala_msg_id = None
    await atualizar_escala_embed(interaction)

# Comando para resetar a escala (Alto Comando)
@app_commands.command(name="resetar_escala", description="Limpa e reinicia a escala do canal (apenas para Alto Comando)")
async def resetar_escala(interaction: discord.Interaction):
    if not any(role.id == ALTO_COMANDO_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "Você precisa do cargo autorizado para usar este comando.", ephemeral=True)
        return
    canal = interaction.guild.get_channel(ESCALA_CHANNEL_ID)
    if not canal:
        await interaction.response.send_message("Canal da escala não encontrado.", ephemeral=True)
        return
    # Apaga todas as mensagens do bot
    async for msg in canal.history(limit=100):
        if msg.author == interaction.client.user:
            try:
                await msg.delete()
            except Exception as e:
                print(f"Erro ao deletar mensagem: {e}")
    global escala_participantes, escala_msg_id
    escala_participantes = []
    escala_msg_id = None
    await garantir_mensagem_info(canal)
    class DummyInteraction:
        def __init__(self, guild, channel, user):
            self.guild = guild
            self.channel = channel
            self.user = user
            class DummyResponse:
                def __init__(self):
                    self._done = True
                def is_done(self):
                    return True
                async def defer(self):
                    pass
            self.response = DummyResponse()
    fake_interaction = DummyInteraction(canal.guild, canal, interaction.client.user)
    await atualizar_escala_embed(fake_interaction)
    await interaction.response.send_message("Escala reiniciada com sucesso!", ephemeral=True)

class Bot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild_id = os.getenv("GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.add_command(iniciar_escala, guild=guild)
            self.tree.add_command(resetar_escala, guild=guild)
            await self.tree.sync(guild=guild)
        else:
            self.tree.add_command(iniciar_escala)
            self.tree.add_command(resetar_escala)
            await self.tree.sync()

    async def on_ready(self):
        print(f"Bot conectado como {self.user}")
        print("Comandos de barra sincronizados!")

        # Limpa todas as mensagens do bot no canal da escala
        canal = self.get_channel(ESCALA_CHANNEL_ID)
        if not canal:
            print("[ERRO] Canal da escala não encontrado. Verifique ESCALA_CHANNEL_ID.")
            return
        # Apaga todas as mensagens do bot
        async for msg in canal.history(limit=100):
            if msg.author == self.user:
                try:
                    await msg.delete()
                except Exception as e:
                    print(f"Erro ao deletar mensagem: {e}")
        global escala_participantes, escala_msg_id
        escala_participantes = []
        escala_msg_id = None
        # Posta novamente as mensagens
        await garantir_mensagem_info(canal)
        # Garante que só uma mensagem dinâmica será criada
        class DummyInteraction:
            def __init__(self, guild, channel, user):
                self.guild = guild
                self.channel = channel
                self.user = user
                class DummyResponse:
                    def __init__(self):
                        self._done = True
                    def is_done(self):
                        return True
                    async def defer(self):
                        pass
                self.response = DummyResponse()
        fake_interaction = DummyInteraction(canal.guild, canal, self.user)
        await atualizar_escala_embed(fake_interaction)
        print("Mensagens da escala limpas e recriadas!")

if __name__ == "__main__":
    client = Bot()
    client.run(os.getenv("TOKEN_DISCORD"))