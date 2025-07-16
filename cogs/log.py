import discord
from discord.ext import commands
import datetime
import os

# Define o caminho base para a pasta de logs
LOGS_DIR = "/home/pi/bot/bot/logs"

class LogGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Garante que o diretório de logs exista ao carregar a cog
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
            print(f"Diretório de logs criado: {LOGS_DIR}")

    @commands.command(name="gerarlog")
    async def generate_log_file(self, ctx):
        """
        Gera um arquivo de log simples na pasta /home/pi/bot/bot/logs.
        """
        # Nome do arquivo de log com timestamp para ser único
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"log_gerado_{timestamp}.txt"
        file_path = os.path.join(LOGS_DIR, file_name)

        log_content = (
            f"--- Log Gerado pelo Bot Discord ---\n"
            f"Data e Hora: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Comando executado por: {ctx.author.name} (ID: {ctx.author.id})\n"
            f"Canal: {ctx.channel.name} (ID: {ctx.channel.id})\n"
            f"Guilda: {ctx.guild.name} (ID: {ctx.guild.id})\n\n"
            f"Este é um exemplo de conteúdo de log gerado por uma cog.\n"
            f"Você pode adicionar qualquer informação relevante aqui.\n"
        )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            await ctx.send(f"Arquivo de log '{file_name}' gerado com sucesso em `{LOGS_DIR}`.")
            print(f"Log gerado: {file_path}") # Isso aparecerá no journalctl
        except Exception as e:
            await ctx.send(f"Erro ao gerar o arquivo de log: {e}")
            print(f"Erro ao gerar log: {e}") # Isso aparecerá no journalctl

    @commands.command(name="listlogs")
    async def list_log_files(self, ctx):
        """
        Lista os arquivos de log na pasta /home/pi/bot/bot/logs.
        """
        try:
            files = [f for f in os.listdir(LOGS_DIR) if os.path.isfile(os.path.join(LOGS_DIR, f))]
            if files:
                file_list_str = "\n".join(files)
                await ctx.send(f"Arquivos na pasta `{LOGS_DIR}`:\n```\n{file_list_str}\n```")
            else:
                await ctx.send(f"Nenhum arquivo encontrado na pasta `{LOGS_DIR}`.")
        except FileNotFoundError:
            await ctx.send(f"A pasta de logs `{LOGS_DIR}` não foi encontrada.")
        except Exception as e:
            await ctx.send(f"Erro ao listar arquivos de log: {e}")


async def setup(bot):
    await bot.add_cog(LogGenerator(bot))
