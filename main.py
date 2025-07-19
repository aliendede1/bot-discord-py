import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging


load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=['?'], intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user.name} online!")
    await bot.change_presence(activity=discord.Game(name="Digite ?ajuda"))
    
    # Carrega os cogs
    await load_cogs()
async def load_cogs():
    try:
        await bot.load_extension('cogs.moderation')
        await bot.load_extension('cogs.utility')
        await bot.load_extension('cogs.fun')
        await bot.load_extension('cogs.error_handler')
        await bot.load_extension('cogs.economy')
        await bot.load_extension('cogs.ticket')
        await bot.load_extension('cogs.bemv')
        await bot.load_extension('cogs.xp_system')
        await bot.load_extension('cogs.log') # Novo cog
        print("Todos os cogs foram carregados com sucesso!")
    except Exception as e:
        print(f"Erro ao carregar cogs: {e}")

# deep

async def main():
    await load_cogs()
    await bot.start(os.getenv("DISCORD_TOKEN"), reconnect=True) 

logger = logging.getLogger(__name__)

# Exemplo de uso
logger.info("Bot iniciado!")  # Mensagem informativa
logger.error("Erro crítico!")  # Mensagem de erro

if __name__ == "__main__":
    if not os.getenv('DISCORD_TOKEN'):
        print("❌ Token não encontrado. Verifique seu arquivo .env")
    else:
        bot.run(os.getenv('DISCORD_TOKEN'))
