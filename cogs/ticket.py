import discord
from discord.ext import commands
from discord.ui import Select, View, Button
from datetime import datetime
import asyncio

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_category = "Suporte // Tickets"
        self.open_tickets = {}  # {user_id: channel_id}
        self.colors = {
            "suporte": 0x3498db,    # Azul
            "denuncia": 0xe74c3c,   # Vermelho
            "duvida": 0x2ecc71      # Verde
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Sistema de Tickets carregado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # 🎟️ Comando para criar painel de tickets
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, ctx):
        """Cria o painel de abertura de tickets"""
        embed = discord.Embed(
            title="🎫 SUPORTE DO SERVIDOR",
            description="Selecione abaixo o tipo de atendimento necessário:",
            color=0x3498db
        )
        
        options = [
            discord.SelectOption(label="🛠️ Suporte Técnico", value="suporte"),
            discord.SelectOption(label="⚠️ Denúncia/Reportar", value="denuncia"),
            discord.SelectOption(label="❓ Dúvidas Gerais", value="duvida")
        ]
        
        view = View()
        view.add_item(Select(placeholder="Selecione uma opção...", options=options, custom_id="ticket_type"))
        
        await ctx.send(embed=embed, view=view)

    # 🛠️ Função para criar tickets
    async def criar_ticket(self, interaction, tipo):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        guild = interaction.guild
        
        # Verifica se já tem ticket aberto
        if user.id in self.open_tickets:
            channel = guild.get_channel(self.open_tickets[user.id])
            if channel:
                embed = discord.Embed(
                    title="🚫 Ticket em Aberto",
                    description=f"Você já possui um ticket ativo: {channel.mention}",
                    color=0xff0000
                )
                return await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                del self.open_tickets[user.id]
        
        # Obtém ou cria a categoria
        category = discord.utils.get(guild.categories, name=self.ticket_category)
        if not category:
            category = await guild.create_category(self.ticket_category)
        
        # Configura as permissões
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True
            )
        }
        
        # Adiciona permissões para cargos de staff
        for role in guild.roles:
            if any(name in role.name.lower() for name in ["staff", "mod", "admin", "suporte"]):
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_messages=True
                )
        
        # Cria o canal do ticket
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{user.display_name}",
            overwrites=overwrites,
            topic=f"Ticket de {user} | Tipo: {tipo} | ID: {user.id}"
        )
        self.open_tickets[user.id] = ticket_channel.id
        
        # Embed de boas-vindas
        embed = discord.Embed(
            title=f"🎫 TICKET {tipo.upper()}",
            description=f"""
            ✨ Olá {user.mention}, seja bem-vindo(a) ao seu ticket!

            📌 **Por favor descreva:**
            ```Seu problema ou solicitação com detalhes```
            
            ⏱️ **Tempo de resposta:**
            ```Até 15 minutos (horário comercial)```
            """,
            color=self.colors.get(tipo, 0x5865F2)
        )
        embed.set_footer(text=f"Ticket criado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
        
        # Botão de fechar (classe corrigida)
        class TicketView(View):
            def __init__(self, cog, user_id, channel_id):
                super().__init__(timeout=None)
                self.cog = cog
                self.user_id = user_id
                self.channel_id = channel_id
            
            @discord.ui.button(label="🔒 FECHAR TICKET", style=discord.ButtonStyle.red)
            async def close_ticket(self, interaction: discord.Interaction, button: Button):
                if interaction.user.id == self.user_id or interaction.user.guild_permissions.manage_channels:
                    # Confirmação de fechamento
                    confirm_embed = discord.Embed(
                        title="✅ TICKET FECHADO",
                        description="Este ticket será deletado em 5 segundos...",
                        color=0x00ff00
                    )
                    await interaction.response.send_message(embed=confirm_embed)
                    
                    # Remove o botão
                    self.clear_items()
                    await interaction.message.edit(view=self)
                    
                    # Remove do registro e deleta o canal
                    if self.user_id in self.cog.open_tickets:
                        del self.cog.open_tickets[self.user_id]
                    
                    channel = interaction.guild.get_channel(self.channel_id)
                    if channel:
                        await asyncio.sleep(5)
                        await channel.delete(reason=f"Ticket fechado por {interaction.user}")
                else:
                    error_embed = discord.Embed(
                        title="❌ ACESSO NEGADO",
                        description="Apenas o dono do ticket ou staff podem fechá-lo!",
                        color=0xff0000
                    )
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
        
        # Envia a mensagem inicial
        view = TicketView(self, user.id, ticket_channel.id)
        await ticket_channel.send(
            content=f"{user.mention}",
            embed=embed,
            view=view
        )
        
        # Mensagem de confirmação
        success_embed = discord.Embed(
            title="✅ TICKET CRIADO",
            description=f"Seu ticket foi criado: {ticket_channel.mention}",
            color=0x00ff00
        )
        await interaction.followup.send(embed=success_embed, ephemeral=True)

    # Listener para interações
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            if interaction.data.get("custom_id") == "ticket_type":
                await self.criar_ticket(interaction, interaction.data["values"][0])

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
