import discord
from discord.ext import commands, tasks
import json
import os
import math
from pathlib import Path
from datetime import datetime, timedelta

class XPSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.xp_file = self.data_dir / "xp_data.json"
        self.xp_data = self.load_data()
        self.xp_per_message = 1
        self.messages_for_xp = 4
        self.max_level = 100
        self.inactive_days = 7  # Dias de inatividade para limpar XP
        self.cleanup_interval = 86400  # Intervalo de limpeza em segundos (24 horas)
        self.cleanup_task.start()

    def load_data(self):
        try:
            if self.xp_file.exists():
                with open(self.xp_file, 'r') as f:
                    data = json.load(f)
                    # Converter timestamps de string para datetime se necessário
                    for user_data in data.values():
                        if 'last_message' in user_data and isinstance(user_data['last_message'], str):
                            user_data['last_message'] = datetime.fromisoformat(user_data['last_message'])
                    return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar dados de XP: {e}, criando novo arquivo...")
        return {}

    def save_data(self):
        try:
            # Converter datetime para string antes de salvar
            save_data = {}
            for user_id, user_data in self.xp_data.items():
                save_data[user_id] = user_data.copy()
                if 'last_message' in save_data[user_id] and isinstance(save_data[user_id]['last_message'], datetime):
                    save_data[user_id]['last_message'] = save_data[user_id]['last_message'].isoformat()
            
            with open(self.xp_file, 'w') as f:
                json.dump(save_data, f, indent=4)
        except IOError as e:
            print(f"Erro ao salvar dados de XP: {e}")

    def cog_unload(self):
        self.cleanup_task.cancel()

    @tasks.loop(seconds=86400)  # Executa a cada 24 horas
    async def cleanup_task(self):
        await self.clean_inactive_users()

    async def clean_inactive_users(self):
        """Remove XP de usuários inativos"""
        guild = self.bot.guilds[0] if self.bot.guilds else None  # Assumindo um único servidor
        if not guild:
            return

        current_time = datetime.utcnow()
        inactive_threshold = current_time - timedelta(days=self.inactive_days)
        users_to_remove = []

        for user_id, user_data in self.xp_data.items():
            member = guild.get_member(int(user_id))
            
            # Se o membro não está mais no servidor ou nunca enviou mensagem
            if member is None:
                users_to_remove.append(user_id)
                continue
                
            # Se nunca enviou mensagem ou está inativo há mais de 7 dias
            last_message = user_data.get('last_message')
            if last_message is None or last_message < inactive_threshold:
                users_to_remove.append(user_id)

        # Remove usuários inativos
        for user_id in users_to_remove:
            del self.xp_data[user_id]
        
        if users_to_remove:
            self.save_data()
            print(f"Limpeza automática: Removidos {len(users_to_remove)} usuários inativos.")

    def get_xp_needed(self, level):
        if level < 2:
            return 0
        return 2 ** (level - 1)

    def get_level(self, xp):
        level = 1
        xp_needed = 0
        
        while level < self.max_level:
            xp_needed_for_next = self.get_xp_needed(level + 1)
            if xp >= xp_needed_for_next:
                xp_needed += xp_needed_for_next
                level += 1
            else:
                break
                
        return level

    def get_progress(self, xp, level):
        if level >= self.max_level:
            return (0, 0)
        
        xp_needed = self.get_xp_needed(level + 1)
        xp_accumulated = sum(self.get_xp_needed(l) for l in range(2, level + 1))
        current_progress = xp - xp_accumulated
        return (current_progress, xp_needed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        current_time = datetime.utcnow()
        
        # Inicializa dados do usuário se não existir
        if user_id not in self.xp_data:
            self.xp_data[user_id] = {
                'xp': 0,
                'messages': 0,
                'level': 1,
                'last_message': current_time
            }
        else:
            # Atualiza última mensagem
            self.xp_data[user_id]['last_message'] = current_time
        
        # Incrementa contador de mensagens
        self.xp_data[user_id]['messages'] += 1
        
        # Concede XP a cada 4 mensagens
        if self.xp_data[user_id]['messages'] % self.messages_for_xp == 0:
            self.xp_data[user_id]['xp'] += self.xp_per_message
            
            # Verifica se subiu de nível
            current_xp = self.xp_data[user_id]['xp']
            current_level = self.get_level(current_xp)
            
            if current_level > self.xp_data[user_id]['level']:
                self.xp_data[user_id]['level'] = current_level
                
                # Envia mensagem privada de level up
                try:
                    progress, needed = self.get_progress(current_xp, current_level)
                    embed = discord.Embed(
                        title="🎉 Level Up!",
                        description=f"Parabéns! Você alcançou o nível {current_level}!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="XP Atual", value=f"{current_xp} XP")
                    embed.add_field(name="Próximo Nível", value=f"{progress}/{needed} XP")
                    
                    await message.author.send(embed=embed)
                except discord.Forbidden:
                    # Se o usuário não aceita mensagens privadas
                    pass
        
        self.save_data()

    @commands.group(name='xp', invoke_without_command=True)
    async def xp_group(self, ctx):
        """Comandos do sistema de XP"""
        embed = discord.Embed(
            title="Sistema de XP - Comandos Disponíveis",
            description="`rank`, `level`, `list`",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @xp_group.command(name='rank', aliases=['info'])
    async def xp_rank(self, ctx, member: discord.Member = None):
        """Mostra seu rank de XP ou de outro usuário"""
        member = member or ctx.author
        user_id = str(member.id)
        
        if user_id not in self.xp_data:
            await ctx.send(f"{member.display_name} ainda não tem XP registrado.")
            return
            
        xp = self.xp_data[user_id]['xp']
        level = self.xp_data[user_id]['level']
        progress, needed = self.get_progress(xp, level)
        
        embed = discord.Embed(
            title=f"🏆 Rank de {member.display_name}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.add_field(name="Nível", value=f"`{level}`", inline=True)
        embed.add_field(name="XP Total", value=f"`{xp}`", inline=True)
        
        if level < self.max_level:
            embed.add_field(
                name="Progresso", 
                value=f"`{progress}/{needed} XP` para o próximo nível", 
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="✨ Nível máximo alcançado!",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @xp_group.command(name='level', aliases=['lvl'])
    async def xp_level(self, ctx, member: discord.Member = None):
        """Mostra seu nível ou de outro usuário"""
        member = member or ctx.author
        user_id = str(member.id)
        
        if user_id not in self.xp_data:
            await ctx.send(f"{member.display_name} ainda não tem XP registrado.")
            return
            
        level = self.xp_data[user_id]['level']
        embed = discord.Embed(
            description=f"**{member.display_name}** está no nível **{level}**!",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @xp_group.command(name='list', aliases=['top'])
    async def xp_list(self, ctx):
        """Mostra o ranking de XP do servidor"""
        if not self.xp_data:
            await ctx.send("Nenhum dado de XP registrado ainda.")
            return
        
        # Ordena usuários por XP (decrescente)
        sorted_users = sorted(
            self.xp_data.items(),
            key=lambda x: x[1]['xp'],
            reverse=True
        )
        
        embed = discord.Embed(
            title="🏆 Ranking de XP - Top 10",
            color=discord.Color.blurple()
        )
        
        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            member = ctx.guild.get_member(int(user_id))
            if member:
                embed.add_field(
                    name=f"{i}. {member.display_name}",
                    value=f"`Nível {data['level']}` | `{data['xp']} XP`",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @commands.command(name='xpcleanup', hidden=True)
    @commands.has_permissions(administrator=True)
    async def manual_cleanup(self, ctx):
        """Limpeza manual de usuários inativos (apenas administradores)"""
        await ctx.send("Iniciando limpeza manual de usuários inativos...")
        await self.clean_inactive_users()
        await ctx.send("Limpeza concluída!")

async def setup(bot):
    await bot.add_cog(XPSystem(bot))
