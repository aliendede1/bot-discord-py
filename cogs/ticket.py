import discord
from discord.ext import commands
from discord.ui import Select, View

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_category = "Suporte // Tickets"  # Nome da categoria existente
        self.banner_url = "https://www.milldesk.com.br/blog/wp-content/uploads/2023/03/suporte-ao-cliente-escritorio-contabilidade.jpg"  # URL do banner

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"✅ Sistema de Tickets carregado!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx):
        """Envia o embed de abertura de tickets"""
        # Limpa mensagens anteriores do bot
        async for msg in ctx.channel.history(limit=10):
            if msg.author == self.bot.user and "ticket" in msg.content.lower():
                await msg.delete()

        # Embed principal
        embed = discord.Embed(
            title="🎫 SUPORTE PERSONALIZADO",
            description=(
                "📩 Precisando de ajuda? Selecione o tipo de ticket abaixo!\n"
                "🔧 Nossa equipe está pronta para te ajudar\n"
                "⏳ Resposta em até 24 horas"
            ),
            color=0xFF5733  # Laranja personalizado
        )
        embed.set_footer(text="© User Server Suporte")
        embed.set_thumbnail(url="https://imgur.com/gallery/anime-audio-systems-lqKMK86#hirEdpK")  # Thumbnail exemplo

        # Dropdown para seleção de tipo
        class TicketDropdown(View):
            def __init__(self):
                super().__init__(timeout=None)
                
                options = [
                    discord.SelectOption(label="Suporte", emoji="🛠️", description="Problemas técnicos"),
                    discord.SelectOption(label="Denúncia", emoji="⚠️", description="Reportar usuários"),
                    discord.SelectOption(label="Dúvida", emoji="❓", description="Perguntas gerais")
                ]
                
                self.select = Select(
                    placeholder="Selecione o tipo de ticket...",
                    options=options,
                    custom_id="ticket_type"
                )
                self.add_item(self.select)

        view = TicketDropdown()
        await ctx.send(embed=embed, view=view)

    async def criar_ticket(self, interaction, ticket_type="Suporte Geral"):
        guild = interaction.guild
        user = interaction.user
        
        # Verifica se a categoria existe
        category = discord.utils.get(guild.categories, name=self.ticket_category)
        if not category:
            await interaction.response.send_message(
                f"❌ Categoria '{self.ticket_category}' não encontrada!",
                ephemeral=True
            )
            return

        # Verifica se o usuário já tem um ticket aberto
        for channel in category.channels:
            if channel.topic and str(user.id) in channel.topic:
                await interaction.response.send_message(
                    f"❌ Você já tem um ticket aberto: {channel.mention}",
                    ephemeral=True
                )
                return

        # Configura permissões
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True)
        }
        
        # Adiciona cargos de staff
        for role_name in ["Staff", "Moderadores"]:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)

        # Cria o canal
        ticket_channel = await category.create_text_channel(
            name=f"ticket-{user.display_name}",
            overwrites=overwrites,
            topic=f"Ticket de {user.id} | Tipo: {ticket_type}"
        )
        
        # Embed do ticket
        embed = discord.Embed(
            title=f"TICKET DE {user.display_name.upper()}",
            color=0x00FF00
        )
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.add_field(name="📌 Status", value="Aberto", inline=True)
        embed.add_field(name="⏳ Criado em", value=interaction.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="🔍 Tipo", value=ticket_type, inline=False)
        embed.set_image(url=self.banner_url)  # Usa o banner personalizado

        # Botão para fechar
        close_button = Button(
            label="FECHAR TICKET",
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            custom_id=f"fechar_ticket_{user.id}"
        )
        
        view = View(timeout=None)
        view.add_item(close_button)
        
        # Mensagem inicial
        await ticket_channel.send(
            content=(
                f"✨ **Bem-vindo(a), {user.mention}!**\n\n"
                "• Descreva seu problema detalhadamente\n"
                "• Anexe prints se necessário\n"
                "• Paciência, a equipe chegará em breve!\n\n"
                f"🔐 Para fechar: Clique no botão abaixo"
            ),
            embed=embed,
            view=view
        )
        
        # Logs
        log_channel = discord.utils.get(guild.channels, name="📜ticket-logs")
        if log_channel:
            await log_channel.send(
                f"📬 **Novo ticket criado**\n"
                f"• Usuário: {user.mention}\n"
                f"• Canal: {ticket_channel.mention}\n"
                f"• Tipo: {ticket_type}"
            )

        await interaction.response.send_message(
            f"🎫 Ticket criado em {ticket_channel.mention}!",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            
            # Fechar ticket
            if custom_id.startswith("fechar_ticket"):
                user_id = int(custom_id.split("_")[-1])
                
                if interaction.user.id == user_id or any(role.name in ["Sub Dono", "Mod", "Suporte"] for role in interaction.user.roles):
                    await interaction.channel.delete()
                    
                    # Log de fechamento
                    log_channel = discord.utils.get(interaction.guild.channels, name="📜ticket-logs")
                    if log_channel:
                        await log_channel.send(
                            f"📭 **Ticket fechado**\n"
                            f"• Canal: #{interaction.channel.name}\n"
                            f"• Por: {interaction.user.mention}"
                        )
                else:
                    await interaction.response.send_message(
                        "❌ Apenas o dono do ticket ou staff pode fechá-lo!",
                        ephemeral=True
                    )
            
            # Seleção de tipo
            elif custom_id == "ticket_type":
                await interaction.response.defer()
                await self.criar_ticket(interaction, interaction.data["values"][0])

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
