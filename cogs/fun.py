import discord
from discord.ext import commands
import random
import asyncio
import aiohttp

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='votar')
    async def votar(self, ctx, pergunta: str, *opcoes: str):
        """Cria uma votação com até 10 opções"""
        if len(opcoes) < 2:
            await ctx.send("❌ Você precisa fornecer pelo menos 2 opções!")
            return
        if len(opcoes) > 10:
            await ctx.send("❌ Número máximo de opções é 10!")
            return
        
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        embed = discord.Embed(
            title=f"📊 {pergunta}",
            color=discord.Color.gold()
        )
        
        for i, opcao in enumerate(opcoes):
            embed.add_field(
                name=f"Opção {i+1}",
                value=f"{emojis[i]} {opcao}",
                inline=False
            )
        
        embed.set_footer(text="Reaja para votar!")
        msg = await ctx.send(embed=embed)
        
        for i in range(len(opcoes)):
            await msg.add_reaction(emojis[i])

    @commands.command(name='dado', aliases=['rolardado'])
    async def dado(self, ctx, lados: int = 6):
        """Rola um dado (padrão: 6 lados)"""
        if lados < 2:
            await ctx.send("❌ O dado precisa ter pelo menos 2 lados!")
            return
        
        resultado = random.randint(1, lados)
        await ctx.send(f"🎲 {ctx.author.mention} rolou um dado de {lados} lados e obteve: **{resultado}**")

    @commands.command(name='moeda', aliases=['flip'])
    async def moeda(self, ctx):
        """Joga uma moeda para cara ou coroa"""
        resultado = random.choice(['Cara', 'Coroa'])
        await ctx.send(f"🪙 {ctx.author.mention} jogou a moeda e deu: **{resultado}**")

    @commands.command(name='piada')
    async def piada(self, ctx):
        """Conta uma piada aleatória"""
        piadas = [
            ("Por que o Python não gosta de festas?", "Porque tem medo de snakes!"),
            ("Qual é o contrário de volátil?", "Vem cá sobrinho!"),
            ("O que o zero disse para o oito?", "Belo cinto!"),
            ("Por que os elétrons nunca são presos?", "Porque eles sempre têm um álibi!"),
            ("Qual é o doce favorito do desenvolvedor?", "Python-doce!")
        ]
        pergunta, resposta = random.choice(piadas)
        embed = discord.Embed(title=pergunta, description=f"||{resposta}||", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name='ship')
    async def ship(self, ctx, usuario1: discord.Member, usuario2: discord.Member = None):
        """Calcula a compatibilidade entre dois usuários"""
        usuario2 = usuario2 or ctx.author
        if usuario1 == usuario2:
            await ctx.send("❌ Você não pode shippar a mesma pessoa!")
            return
        
        porcentagem = random.randint(0, 100)
        ship_name = (usuario1.display_name[:3] + usuario2.display_name[-3:]).lower()
        
        embed = discord.Embed(
            title="💖 Calculadora de Ship",
            description=f"Compatibilidade entre {usuario1.mention} e {usuario2.mention}",
            color=discord.Color.pink()
        )
        embed.add_field(name="Nome do Ship", value=f"**{ship_name}**", inline=False)
        embed.add_field(name="Compatibilidade", value=f"**{porcentagem}%**")
        
        if porcentagem > 80:
            embed.set_footer(text="Casem-se já!")
        elif porcentagem > 50:
            embed.set_footer(text="Tem potencial!")
        else:
            embed.set_footer(text="Melhor continuar amigos...")
        
        await ctx.send(embed=embed)

    @commands.command(name='gato', aliases=['cat'])
    async def gato(self, ctx):
        """Mostra uma foto aleatória de gato"""
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.thecatapi.com/v1/images/search') as r:
                if r.status == 200:
                    data = await r.json()
                    embed = discord.Embed(title="🐱 Miau!", color=discord.Color.orange())
                    embed.set_image(url=data[0]['url'])
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Não consegui encontrar um gato agora. Tente novamente mais tarde!")

    @commands.command(name='danca')
    async def danca(self, ctx):
        """Faz o bot dançar!"""
        dance_moves = ["💃", "🕺", "👯", "🎉", "✨"]
        msg = await ctx.send("Começando a dança...")
        
        for _ in range(5):
            move = random.choice(dance_moves)
            await msg.edit(content=move)
            await asyncio.sleep(0.5)
        
        await msg.edit(content=f"{random.choice(dance_moves)} Dança concluída!")

    @commands.command(name='escolher', aliases=['choose'])
    async def escolher(self, ctx, *opcoes: str):
        """Escolhe uma opção aleatória para você"""
        if len(opcoes) < 2:
            await ctx.send("❌ Forneça pelo menos 2 opções para escolher!")
            return
        
        escolha = random.choice(opcoes)
        await ctx.send(f"🎯 Eu escolho: **{escolha}**")

async def setup(bot):
    await bot.add_cog(Fun(bot))