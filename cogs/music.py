import asyncio
import discord
from discord.ext import commands
import yt_dlp
import functools

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_states = {}

        # Configurações otimizadas do yt-dlp
        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
        }
        print("[Music Cog] Cog de música inicializada com configurações otimizadas.")

    def get_guild_state(self, guild):
        if guild.id not in self.vc_states:
            self.vc_states[guild.id] = {
                'queue': asyncio.Queue(),
                'current_song': None,
                'loop_mode': False,
                'voice_client': None,
                'skip_votes': set(),
                'playing_task': None,
            }
        return self.vc_states[guild.id]

    async def audio_player_task(self, ctx):
        state = self.get_guild_state(ctx.guild)
        while True:
            try:
                # Verificação de conexão robusta
                if state['voice_client'] is None or not state['voice_client'].is_connected():
                    print(f"[{ctx.guild.name}] [Player Task] Voice client disconnected, exiting task")
                    break

                print(f"[{ctx.guild.name}] [Player Task] Waiting for next song...")
                state['current_song'] = await state['queue'].get()
                
                # Configuração melhorada do FFmpeg
                player_source = discord.FFmpegPCMAudio(
                    state['current_song']['url'],
                    before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
                    options='-vn -filter:a "volume=0.8"'
                )

                # Embed de "Tocando agora" melhorado
                embed = discord.Embed(
                    title="🎵 Tocando Agora",
                    description=f"**[{state['current_song']['title']}]({state['current_song']['url']})**",
                    color=discord.Color.blurple()
                )
                embed.add_field(name="Canal", value=state['current_song']['uploader'], inline=True)
                if 'thumbnail' in state['current_song']:
                    embed.set_thumbnail(url=state['current_song']['thumbnail'])

                await ctx.send(embed=embed)

                # Sistema de reprodução mais resiliente
                def after_playing(error):
                    if error:
                        print(f'[{ctx.guild.name}] Error in after_playing: {error}')
                    self.bot.loop.create_task(self.play_next_song(ctx, error))

                state['voice_client'].play(player_source, after=after_playing)

                # Monitoramento contínuo da reprodução
                while state['voice_client'].is_playing() or state['voice_client'].is_paused():
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                print(f"[{ctx.guild.name}] [Player Task] Task cancelled")
                break
            except discord.ClientException as e:
                print(f"[{ctx.guild.name}] [Player Task] Discord error: {e}")
                await asyncio.sleep(5)
                continue
            except Exception as e:
                print(f"[{ctx.guild.name}] [Player Task] Unexpected error: {e}")
                await asyncio.sleep(2)
                continue
            finally:
                state['skip_votes'].clear()
                if state['loop_mode'] and state['current_song']:
                    await state['queue'].put(state['current_song'])

                # Verificação de inatividade melhorada
                if state['queue'].empty() and not state['loop_mode']:
                    await asyncio.sleep(10)  # Tempo maior antes de desconectar
                    if (state['voice_client'] and 
                        not state['voice_client'].is_playing() and 
                        state['queue'].empty()):
                        await self.cleanup_voice_state(ctx.guild)

    async def play_next_song(self, ctx, error):
        state = self.get_guild_state(ctx.guild)
        if error:
            print(f'[{ctx.guild.name}] Playback error: {error}')
            error_embed = discord.Embed(
                title="❌ Erro de Reprodução",
                description=f"Ocorreu um erro: `{error}`",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

        # Lógica de limpeza melhorada
        if state['queue'].empty() and not state['loop_mode']:
            if state['playing_task'] and not state['playing_task'].done():
                state['playing_task'].cancel()
            await self.cleanup_voice_state(ctx.guild)

    async def cleanup_voice_state(self, guild):
        state = self.get_guild_state(guild)
        if state['voice_client']:
            try:
                await state['voice_client'].disconnect()
            except:
                pass
        if guild.id in self.vc_states:
            del self.vc_states[guild.id]
        print(f"[{guild.name}] Cleaned up voice state")

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, search: str):
        # Verificação de canal de voz melhorada
        if not ctx.author.voice:
            embed = discord.Embed(
                title="🔇 Sem Conexão",
                description="Entre em um canal de voz primeiro!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        channel = ctx.author.voice.channel
        state = self.get_guild_state(ctx.guild)

        # Sistema de conexão mais robusto
        if state['voice_client'] is None:
            try:
                state['voice_client'] = await channel.connect()
                print(f"[{ctx.guild.name}] Connected to voice channel")
            except Exception as e:
                print(f"[{ctx.guild.name}] Connection error: {e}")
                embed = discord.Embed(
                    title="❌ Erro de Conexão",
                    description=f"Não consegui conectar: `{e}`",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
        elif state['voice_client'].channel != channel:
            try:
                await state['voice_client'].move_to(channel)
                print(f"[{ctx.guild.name}] Moved to new channel")
            except Exception as e:
                print(f"[{ctx.guild.name}] Move error: {e}")
                embed = discord.Embed(
                    title="❌ Erro de Movimento",
                    description=f"Não consegui mudar de canal: `{e}`",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

        # Busca de música com tratamento de erros melhorado
        try:
            func = functools.partial(yt_dlp.YoutubeDL(self.YTDL_OPTIONS).extract_info, 
                                   search, download=False)
            info = await self.bot.loop.run_in_executor(None, func)
            
            if not info:
                raise Exception("Nenhum resultado encontrado")

            song = info['entries'][0] if 'entries' in info else info
            
            song_data = {
                'url': song['url'],
                'title': song.get('title', 'Título desconhecido'),
                'uploader': song.get('uploader', 'Artista desconhecido'),
                'thumbnail': song.get('thumbnail'),
                'duration': song.get('duration', 0)
            }

            await state['queue'].put(song_data)
            
            # Embed de confirmação melhorado
            embed = discord.Embed(
                title="🎶 Adicionado à Fila",
                description=f"**[{song_data['title']}]({song_data['url']})**",
                color=discord.Color.green()
            )
            if song_data['thumbnail']:
                embed.set_thumbnail(url=song_data['thumbnail'])
            embed.add_field(name="Duração", 
                           value=f"{int(song_data['duration']//60)}:{int(song_data['duration']%60):02d}", 
                           inline=True)
            await ctx.send(embed=embed)

            # Iniciar player task se necessário
            if state['playing_task'] is None or state['playing_task'].done():
                state['playing_task'] = self.bot.loop.create_task(self.audio_player_task(ctx))

        except Exception as e:
            print(f"[{ctx.guild.name}] Search error: {e}")
            embed = discord.Embed(
                title="🔍 Erro na Busca",
                description=f"Não encontrei resultados para: `{search}`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    # [asfasdfasfda

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        state = self.get_guild_state(ctx.guild)
        
        if not state['voice_client'] or not state['voice_client'].is_playing():
            embed = discord.Embed(
                title="⏭️ Nada para Pular",
                description="Não há música tocando no momento!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        voter = ctx.author
        if voter.id in state['skip_votes']:
            embed = discord.Embed(
                title="🗳️ Voto Já Registrado",
                description="Você já votou para pular esta música!",
                color=discord.Color.light_grey()
            )
            return await ctx.send(embed=embed)
        
        state['skip_votes'].add(voter.id)
        members_in_vc = len([m for m in state['voice_client'].channel.members if not m.bot])
        required_votes = max(1, (members_in_vc // 2) + (members_in_vc % 2))
        
        if len(state['skip_votes']) >= required_votes:
            embed = discord.Embed(
                title="⏭️ Música Pulada!",
                description=f"Pulando: **{state['current_song']['title']}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            state['voice_client'].stop()
            state['skip_votes'].clear()
        else:
            embed = discord.Embed(
                title="🗳️ Voto para Pular",
                description=f"Voto registrado! Faltam {required_votes - len(state['skip_votes'])} votos para pular.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    @commands.command(name='stop')
    async def stop(self, ctx):
        state = self.get_guild_state(ctx.guild)
        
        if not state['voice_client'] or not state['voice_client'].is_connected():
            embed = discord.Embed(
                title="⏹️ Não Conectado",
                description="O bot não está conectado a um canal de voz!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        # Limpar fila e parar reprodução
        state['queue'] = asyncio.Queue()
        state['loop_mode'] = False
        
        if state['playing_task']:
            state['playing_task'].cancel()
            state['playing_task'] = None
            
        state['voice_client'].stop()
        await state['voice_client'].disconnect()
        
        if ctx.guild.id in self.vc_states:
            del self.vc_states[ctx.guild.id]
            
        embed = discord.Embed(
            title="⏹️ Reprodução Parada",
            description="A música foi parada e a fila foi limpa!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name='loop')
    async def loop(self, ctx):
        state = self.get_guild_state(ctx.guild)
        
        if not state['voice_client'] or not state['voice_client'].is_playing():
            embed = discord.Embed(
                title="🔁 Nada Tocando",
                description="Não há música tocando para colocar em loop!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        state['loop_mode'] = not state['loop_mode']
        
        embed = discord.Embed(
            title="🔁 Modo Loop",
            description=f"O modo loop foi **{'ativado' if state['loop_mode'] else 'desativado'}**!",
            color=discord.Color.green() if state['loop_mode'] else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name='queue', aliases=['q', 'fila'])
    async def queue(self, ctx):
        state = self.get_guild_state(ctx.guild)
        
        if state['queue'].empty() and not state['current_song']:
            embed = discord.Embed(
                title="📋 Fila Vazia",
                description="Não há músicas na fila de reprodução!",
                color=discord.Color.light_grey()
            )
            return await ctx.send(embed=embed)
        
        queue_list = list(state['queue']._queue)
        embed = discord.Embed(title="📋 Fila de Reprodução", color=discord.Color.blue())
        
        if state['current_song']:
            embed.add_field(
                name="🎵 Tocando Agora",
                value=f"[{state['current_song']['title']}]({state['current_song']['url']})",
                inline=False
            )
        
        if queue_list:
            songs_list = "\n".join(
                f"**{i+1}.** [{song['title']}]({song['url']})" 
                for i, song in enumerate(queue_list[:10])  # Mostrar apenas as 10 primeiras
            )
            
            if len(queue_list) > 10:
                songs_list += f"\n\n... e mais {len(queue_list) - 10} músicas"
                
            embed.add_field(
                name=f"Próximas Músicas ({len(queue_list)})",
                value=songs_list,
                inline=False
            )
        else:
            embed.add_field(
                name="Próximas Músicas",
                value="Nenhuma música na fila",
                inline=False
            )
        
        if state['loop_mode']:
            embed.set_footer(text="🔁 Modo loop ativado")
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
    print("[Music Cog] Cog carregada com sucesso!")
