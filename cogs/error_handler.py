import discord
from discord.ext import commands

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Manipulador global de erros para comandos"""
        
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Comando não encontrado. Digite `?ajuda` para ver os comandos disponíveis.")
            return
            
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para usar este comando!")
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Argumento faltando! Use: `?{ctx.command.name} {ctx.command.signature}`")
            return
            
        if isinstance(error, commands.BadArgument):
            await ctx.send("❌ Argumento inválido. Verifique os parâmetros do comando.")
            return
            
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Este comando está em cooldown! Tente novamente em {error.retry_after:.1f} segundos.")
            return
            
        # Log de erros não tratados
        print(f"Erro não tratado em {ctx.command.name}: {error}")
        await ctx.send("❌ Ocorreu um erro ao executar este comando.")

    # Você pode adicionar manipuladores específicos para cada comando aqui
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        """Manipulador de erros para comandos de barra (slash commands)"""
        if isinstance(error, commands.CheckFailure):
            await ctx.respond("❌ Você não tem permissão para usar este comando!", ephemeral=True)
        else:
            await ctx.respond("❌ Ocorreu um erro ao executar este comando.", ephemeral=True)
            print(f"Erro em slash command: {error}")

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))