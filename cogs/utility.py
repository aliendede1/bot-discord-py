import discord
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ajuda(self, ctx):
        """Mostra esta mensagem de ajuda"""
        try:
            embed = discord.Embed(
                title="📋 Central de Ajuda - " + ctx.guild.name,
                description="Lista de todos os comandos disponíveis(com o prefixo):",
                color=discord.Color.blue()
            )
            
            # Categorias e comandos conforme mostrado na imagem
            categorias = {
                "🛡️ Moderaao":["?clear", "?ban", "?banid", "?unban","?unlock", "?lock"],
                "💰 Economia": ["?saldo", "?pagar", "?trabalhar"],
                "ℹ️ informação": ["?ajuda", "?userinfo", "?serverinfo", "?xp rank", "?xp list", "?xp level"],
                "🎉 Diversão": ["?votar", "?dado", "?moeda", "?piada", "?ship", "?gato"],
                "🎵 Music": [".play", ".skip", ".loop" , ".stop"],
            }

            # Adiciona cada categoria ao embed
            for categoria, comandos in categorias.items():
                embed.add_field(
                    name=categoria,
                    value="\n".join([f"`{cmd}`" for cmd in comandos]),
                    inline=True
                )

            # Configurações de rodapé e thumbnail
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            embed.set_footer(text=f"Pedido por {ctx.author.display_name}", 
                           icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Erro no comando ajuda: {e}")
            await ctx.send("❌ Ocorreu um erro ao exibir a ajuda. Por favor, tente novamente.")

    @commands.command(name='serverinfo', aliases=['infoserver'])
    async def serverinfo(self, ctx):
        """Mostra informações detalhadas do servidor"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 Informações do Servidor - {guild.name}",
            color=discord.Color.green()
        )
        
        embed.add_field(name="👑 Dono", value=guild.owner.mention, inline=True)
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        
        embed.add_field(name="👥 Membros", value=guild.member_count, inline=True)
        embed.add_field(name="💬 Canais", value=f"{len(guild.text_channels)} Texto | {len(guild.voice_channels)} Voz", inline=True)
        embed.add_field(name="😎 Emojis", value=f"{len(guild.emojis)}/{guild.emoji_limit}", inline=True)
        
        embed.add_field(name="📈 Nível de Boost", value=f"Nível {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="🔐 Verificação", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="🎭 Roles", value=f"{len(guild.roles)} cargos", inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
            
        await ctx.send(embed=embed)

    @commands.command(name='userinfo')
    async def userinfo(self, ctx, member: discord.Member = None):
        """Mostra informações sobre um membro"""
        member = member or ctx.author
        roles = [role for role in member.roles if role.name != "@everyone"]
        
        embed = discord.Embed(
            title=f"ℹ️ Informações de {member.display_name}",
            color=member.color
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        
        embed.add_field(name="Nome", value=member.name, inline=True)
        embed.add_field(name="Apelido", value=member.nick or "Nenhum", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        
        embed.add_field(
            name="Conta criada em", 
            value=member.created_at.strftime("%d/%m/%Y %H:%M"), 
            inline=True
        )
        
        embed.add_field(
            name="Entrou no servidor em", 
            value=member.joined_at.strftime("%d/%m/%Y %H:%M"), 
            inline=True
        )
        
        if roles:
            embed.add_field(
                name=f"Cargos ({len(roles)})",
                value=" ".join([role.mention for role in roles]),
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
