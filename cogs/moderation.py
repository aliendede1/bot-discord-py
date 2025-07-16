import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='clear', aliases=['limpar'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Limpa uma quantidade específica de mensagens"""
        if amount <= 0:
            await ctx.send("❌ Por favor, especifique um número maior que zero!")
            return
            
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"✅ {amount} mensagens foram limpas!")
        await msg.delete(delay=3)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="Sem motivo"):
        """Bane um membro do servidor"""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="🔨 Membro Banido",
                description=f"{member.mention} foi banido por {ctx.author.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="Motivo", value=reason)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para banir este membro!")
        except Exception as e:
            await ctx.send(f"❌ Ocorreu um erro: {e}")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Você não tem permissão para banir membros!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Mencione quem deseja banir! Ex: `?ban @usuário motivo`")

    @commands.command(name="banid", aliases=["banporid"])
    @commands.has_permissions(ban_members=True)
    async def banid(self, ctx, user_id: int, *, reason="Motivo não informado"):
        """Bane um usuário por ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.ban(user, reason=reason)
            await ctx.send(f"🔨 Usuário com ID `{user_id}` foi banido. Motivo: {reason}")
        except discord.NotFound:
            await ctx.send("❌ Usuário não encontrado. Verifique o ID.")
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para banir este usuário.")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason="Sem motivo"):
        """Desbane um usuário por ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(f"✅ Usuário com ID `{user_id}` foi desbanido. Motivo: {reason}")
        except discord.NotFound:
            await ctx.send("❌ ID inválido ou usuário não encontrado.")
        except discord.Forbidden:
            await ctx.send("❌ Sem permissão para desbanir.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Trava o canal atual"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f'🔒 Canal {ctx.channel.mention} foi bloqueado!')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Destrava o canal atual"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f'🔓 Canal {ctx.channel.mention} foi desbloqueado!')

async def setup(bot):
    await bot.add_cog(Moderation(bot))