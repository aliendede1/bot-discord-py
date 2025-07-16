import os
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'  # Caminho pode ser ajustado conforme o ambiente
)
logger = logging.getLogger(__name__)

# Configuração dos Intents
intents = discord.Intents.all()

# Instância do bot
bot = commands.Bot(command_prefix=['?', '.'], intents=intents)

# Evento de quando o bot está pronto
@bot.event
async def on_ready():
    logger.info(f'Bot {bot.user} está online!')
    await bot.change_presence(activity=discord.Game(name="Digite ?ajuda"))
    await load_cogs()

# Carregamento dos Cogs
async def load_cogs():
    cogs = [
        'cogs.moderation',
        'cogs.utility',
        'cogs.fun',
        'cogs.error_handler',
        'cogs.music',
        'cogs.economy'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'✅ Cog carregado: {cog}')
        except Exception as e:
            logger.error(f'❌ Erro ao carregar {cog}: {e}')

# Função principal
async def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.critical("❌ Token do Discord não encontrado no .env.")
        return

    try:
        await bot.start(token, reconnect=True)
    except Exception as e:
        logger.critical(f'Erro crítico ao iniciar o bot: {e}')

# Ponto de entrada
if __name__ == "__main__":
    asyncio.run(main())
