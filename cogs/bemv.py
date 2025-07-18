import discord
from discord.ext import commands
from discord import Embed
import json
import os
from datetime import datetime

class WelcomeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "configs/welcome_config.json"
        os.makedirs("configs", exist_ok=True)
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"[DEBUG] Novo membro detectado: {member.name}")
        guild_id = str(member.guild.id)
        
        # Verifica se as configurações existem para este servidor
        if guild_id not in self.config:
            return

        # 1. Sistema de auto-cargo
        if 'auto_role' in self.config[guild_id]:
            try:
                role = member.guild.get_role(int(self.config[guild_id]['auto_role']))
                if role:
                    await member.add_roles(role)
                    print(f"[DEBUG] Cargo {role.name} adicionado para {member.name}")
            except Exception as e:
                print(f"[ERRO] Ao adicionar cargo: {e}")

        # 2. Mensagem de boas-vindas
        if 'welcome_channel' in self.config[guild_id]:
            try:
                channel = self.bot.get_channel(int(self.config[guild_id]['welcome_channel']))
                if channel:
                    print(f"[DEBUG] Tentando enviar mensagem para #{channel.name}")
                    
                    # Criação do embed
                    embed = Embed(
                        title=f"🌟 Bem-vindo(a) ao {member.guild.name}!",
                        description=f"{member.mention} acabou de entrar no servidor!",
                        color=0x00ff00
                    )
                    embed.add_field(
                        name="📝 Informações",
                        value=f"🆔 ID: `{member.id}`\n"
                              f"📅 Conta criada: {member.created_at.strftime('%d/%m/%Y')}",
                        inline=False
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    
                    await channel.send(embed=embed)
                    print(f"[DEBUG] Mensagem enviada com sucesso!")
            except Exception as e:
                print(f"[ERRO] Ao enviar mensagem: {e}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def setar_cargo(self, ctx, role: discord.Role):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        self.config[guild_id]['auto_role'] = role.id
        self.save_config()
        await ctx.send(f"✅ Cargo automático definido para {role.mention}")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def setar_canal(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.config:
            self.config[guild_id] = {}
        
        self.config[guild_id]['welcome_channel'] = channel.id
        self.save_config()
        await ctx.send(f"✅ Canal de boas-vindas definido para {channel.mention}")

    @commands.command()
    async def testar_boasvindas(self, ctx):
        await self.on_member_join(ctx.author)
        await ctx.send("✅ Mensagem de teste disparada!")

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))
