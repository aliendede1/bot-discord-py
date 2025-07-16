import discord
from discord.ext import commands
import random

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users_currency = {}  # Simulando um banco de dados simples

    @commands.command(name='saldo', aliases=['balance'])
    async def saldo(self, ctx, member: discord.Member = None):
        """Verifica seu saldo ou de outro membro"""
        member = member or ctx.author
        balance = self.users_currency.get(member.id, 0)
        
        embed = discord.Embed(
            title=f"💰 Saldo de {member.display_name}",
            description=f"**{balance} moedas**",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.command(name='pagar', aliases=['pay'])
    async def pagar(self, ctx, member: discord.Member, amount: int):
        """Transfere moedas para outro usuário"""
        if amount <= 0:
            await ctx.send("❌ Valor deve ser positivo!")
            return
            
        if ctx.author.id == member.id:
            await ctx.send("❌ Não pode pagar a si mesmo!")
            return
            
        sender_balance = self.users_currency.get(ctx.author.id, 0)
        if sender_balance < amount:
            await ctx.send("❌ Saldo insuficiente!")
            return
            
        # Atualiza saldos
        self.users_currency[ctx.author.id] = sender_balance - amount
        self.users_currency[member.id] = self.users_currency.get(member.id, 0) + amount
        
        embed = discord.Embed(
            title="💸 Transferência concluída",
            description=f"{ctx.author.mention} pagou {amount} moedas para {member.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='trabalhar')
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1h de cooldown
    async def trabalhar(self, ctx):
        """Ganhe moedas trabalhando (cooldown: 1h)"""
        earnings = random.randint(50, 200)
        self.users_currency[ctx.author.id] = self.users_currency.get(ctx.author.id, 0) + earnings
        
        embed = discord.Embed(
            title="🛠️ Trabalho concluído",
            description=f"Você ganhou {earnings} moedas!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))