import asyncio
import discord
from discord.ext import commands
import yt_dlp
import functools
import itertools

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_states = {} # Dicionário para gerenciar o estado da reprodução por guild (servidor)

        # Configurações do yt-dlp
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
            'source_address': '0.0.0.0', # Para IPv4, pode ser necessário em alguns sistemas
        }
        print("[Music Cog] Cog de música inicializada.")

    def get_guild_state(self, guild):
        # Retorna ou cria o estado de reprodução para um servidor
        if guild.id not in self.vc_states:
            self.vc_states[guild.id] = {
                'queue': asyncio.Queue(),
                'current_song': None,
                'loop_mode': False,
                'voice_client': None,
                'skip_votes': set(),
                'playing_task': None, # Para armazenar a tarefa de reprodução
            }
            print(f"[{guild.name}] [Estado da Guild] Novo estado criado para a guild.")
        return self.vc_states[guild.id]

    async def audio_player_task(self, ctx):
        state = self.get_guild_state(ctx.guild)
        while True:
            print(f"[{ctx.guild.name}] [Player Task] Esperando próxima música...")
            try:
                # Espera por uma música na fila
                state['current_song'] = await state['queue'].get()
                print(f"[{ctx.guild.name}] [Player Task] Pegou música da fila: {state['current_song']['title']}")
            except asyncio.CancelledError:
                # Tarefa cancelada, sair do loop
                print(f"[{ctx.guild.name}] [Player Task] Tarefa de reprodução cancelada.")
                break
            except Exception as e:
                print(f"[{ctx.guild.name}] [Player Task] Erro inesperado ao pegar da fila: {e}")
                continue

            if state['current_song'] is None:
                print(f"[{ctx.guild.name}] [Player Task] Música atual é None, pulando iteração.")
                continue # Pula se por algum motivo a música for None

            player_source = discord.FFmpegPCMAudio(state['current_song']['url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 20')
            print(f"[{ctx.guild.name}] [Player Task] Fonte FFmpegPCMAudio criada para: {state['current_song']['title']}")

            try:
                # Mensagem de "Tocando agora" em Embed
                embed = discord.Embed(
                    title="🎧 Tocando Agora",
                    description=f"**[{state['current_song']['title']}]({state['current_song']['url']})**",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Artista/Uploader", value=state['current_song']['uploader'], inline=True)
                # Você pode adicionar a duração aqui se quiser
                # embed.add_field(name="Duração", value=str(datetime.timedelta(seconds=state['current_song']['duration'])), inline=True)
                embed.set_thumbnail(url=state['current_song'].get('thumbnail')) # Adiciona a thumbnail se disponível

                await ctx.send(embed=embed)
                print(f"[{ctx.guild.name}] [Player Task] Tentando iniciar reprodução de: {state['current_song']['title']}")
                state['voice_client'].play(player_source, after=lambda e: self.bot.loop.call_soon_threadsafe(self.play_next_song, ctx, e))
                # Espera até a música terminar ou ser interrompida
                while state['voice_client'].is_playing() or state['voice_client'].is_paused():
                    await asyncio.sleep(1)
                print(f"[{ctx.guild.name}] [Player Task] Reprodução de {state['current_song']['title']} terminada ou interrompida.")

            except Exception as e:
                print(f"[{ctx.guild.name}] [Player Task] Erro crítico ao tocar áudio: {e}")
                error_embed = discord.Embed(
                    title="⚠️ Erro na Reprodução",
                    description=f"Opa! Não consegui tocar essa música. Erro: `{e}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
            finally:
                print(f"[{ctx.guild.name}] [Player Task] Bloco finally: Limpando votos de skip e verificando loop/fila.")
                state['skip_votes'].clear()
                if state['loop_mode']:
                    await state['queue'].put(state['current_song'])
                    print(f"[{ctx.guild.name}] [Player Task] Música {state['current_song']['title']} recolocada na fila (loop ativo).")
                state['current_song'] = None

                if state['queue'].empty() and not state['loop_mode']:
                    print(f"[{ctx.guild.name}] [Player Task] Fila vazia e sem loop. Aguardando 5s antes de desconectar por inatividade.")
                    await asyncio.sleep(5)
                    if state['voice_client'] and not state['voice_client'].is_playing() and state['queue'].empty():
                        print(f"[{ctx.guild.name}] [Player Task] Desconectando do canal de voz por inatividade.")
                        await state['voice_client'].disconnect()
                        state['voice_client'] = None
                        print(f"[{ctx.guild.name}] [Player Task] Desconectado do canal de voz em {ctx.guild.name}.")
                        if ctx.guild.id in self.vc_states:
                            del self.vc_states[ctx.guild.id]
                            print(f"[{ctx.guild.name}] [Player Task] Estado da guild removido.")


    def play_next_song(self, ctx, error):
        state = self.get_guild_state(ctx.guild)
        if error:
            print(f'[{ctx.guild.name}] [Play Next Song Callback] Erro durante a reprodução da música anterior: {error}')
            error_embed = discord.Embed(
                title="❌ Erro de Reprodução",
                description=f"Ocorreu um erro durante a reprodução da música: `{error}`",
                color=discord.Color.red()
            )
            asyncio.run_coroutine_threadsafe(ctx.send(embed=error_embed), self.bot.loop)

        if state['queue'].empty() and not state['loop_mode'] and state['playing_task'] and not (state['voice_client'] and state['voice_client'].is_playing()):
            print(f"[{ctx.guild.name}] [Play Next Song Callback] Fila vazia, sem loop. Cancelando player task e desconectando.")
            if state['playing_task']:
                state['playing_task'].cancel()
                state['playing_task'] = None
            if state['voice_client']:
                asyncio.run_coroutine_threadsafe(state['voice_client'].disconnect(), self.bot.loop)
                state['voice_client'] = None
            if ctx.guild.id in self.vc_states:
                del self.vc_states[ctx.guild.id]
                print(f"[{ctx.guild.name}] [Play Next Song Callback] Estado da guild removido após inatividade total.")
            return
        elif state['loop_mode'] and state['current_song']:
            print(f"[{ctx.guild.name}] [Play Next Song Callback] Modo loop ativo. A música atual já foi recolocada na fila.")
            pass
        elif not state['queue'].empty():
            print(f"[{ctx.guild.name}] [Play Next Song Callback] Fila não vazia. Próxima música será pega pelo audio_player_task.")
            pass
        else:
            print(f"[{ctx.guild.name}] [Play Next Song Callback] Condição final não tratada: Fila vazia, sem loop, mas player_task talvez não cancelado.")
            if state['playing_task']:
                state['playing_task'].cancel()
                state['playing_task'] = None
            if state['voice_client']:
                asyncio.run_coroutine_threadsafe(state['voice_client'].disconnect(), self.bot.loop)
                state['voice_client'] = None
            if ctx.guild.id in self.vc_states:
                del self.vc_states[ctx.guild.id]


    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, search: str):
        print(f"[{ctx.guild.name}] [Comando Play] Recebido comando 'play' com busca: '{search}'")
        if not ctx.author.voice:
            print(f"[{ctx.guild.name}] [Comando Play] Usuário não está em canal de voz.")
            embed = discord.Embed(
                title="⚠️ Sem Canal de Voz",
                description="Você precisa estar em um canal de voz para usar este comando!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        channel = ctx.author.voice.channel
        state = self.get_guild_state(ctx.guild)

        if state['voice_client'] is None or not state['voice_client'].is_connected():
            print(f"[{ctx.guild.name}] [Comando Play] Bot não conectado ou desconectado. Tentando conectar a: {channel.name}")
            try:
                state['voice_client'] = await channel.connect()
                embed = discord.Embed(
                    title="🔊 Conectado!",
                    description=f"Conectado ao canal de voz: **{channel.name}**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                print(f"[{ctx.guild.name}] [Comando Play] Conectado com sucesso ao canal de voz.")
            except Exception as e:
                print(f"[{ctx.guild.name}] [Comando Play] Erro ao conectar ao canal de voz: {e}")
                embed = discord.Embed(
                    title="❌ Erro de Conexão",
                    description=f"Não consegui conectar ao canal de voz. Erro: `{e}`",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
        elif state['voice_client'].channel != channel:
            print(f"[{ctx.guild.name}] [Comando Play] Bot já está em outro canal de voz.")
            embed = discord.Embed(
                title="❌ Já Estou Conectado",
                description="Já estou em outro canal de voz neste servidor!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        else:
            print(f"[{ctx.guild.name}] [Comando Play] Bot já está conectado no canal correto.")


        print(f"[{ctx.guild.name}] [Comando Play] Iniciando busca com yt-dlp para '{search}'...")
        func = functools.partial(yt_dlp.YoutubeDL(self.YTDL_OPTIONS).extract_info, search, download=False)
        try:
            info = await self.bot.loop.run_in_executor(None, func)
            print(f"[{ctx.guild.name}] [Comando Play] Busca yt-dlp concluída. Info: {'entries' if 'entries' in info else 'single video'}")
        except Exception as e:
            print(f"[{ctx.guild.name}] [Comando Play] ERRO ao buscar vídeo com yt-dlp: {e}")
            embed = discord.Embed(
                title="🔍 Erro na Busca",
                description=f"Não consegui encontrar essa música. Erro: `{e}`\n(Tente ser mais específico na sua busca!)",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        song = None
        if 'entries' in info:
            if info['entries']:
                song = info['entries'][0]
                print(f"[{ctx.guild.name}] [Comando Play] Playlist detectada. Usando primeira entrada: {song.get('title', 'N/A')}")
            else:
                print(f"[{ctx.guild.name}] [Comando Play] Playlist detectada, mas sem entradas.")
                embed = discord.Embed(
                    title="🔎 Nenhuma Entrada Encontrada",
                    description="Não encontrei resultados para sua busca.",
                    color=discord.Color.orange()
                )
                return await ctx.send(embed=embed)
        else:
            song = info
            print(f"[{ctx.guild.name}] [Comando Play] Vídeo único detectado: {song.get('title', 'N/A')}")

        if song:
            song_data = {
                'url': song.get('url'),
                'title': song.get('title', 'Título Desconhecido'),
                'uploader': song.get('uploader', 'Uploader Desconhecido'),
                'duration': song.get('duration', 'N/A'),
                'thumbnail': song.get('thumbnail', None) # Adiciona a URL da thumbnail
            }
            if not song_data['url']:
                print(f"[{ctx.guild.name}] [Comando Play] URL da música não encontrada na info do yt-dlp: {song_data['title']}")
                embed = discord.Embed(
                    title="❌ URL de Áudio Não Encontrada",
                    description="Não foi possível obter a URL de áudio para esta música.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            await state['queue'].put(song_data)
            embed = discord.Embed(
                title="➕ Música Adicionada à Fila",
                description=f"**[{song_data['title']}]({song_data['url']})**",
                color=discord.Color.green()
            )
            if song_data['thumbnail']:
                embed.set_thumbnail(url=song_data['thumbnail'])
            embed.add_field(name="Uploader", value=song_data['uploader'], inline=True)
            await ctx.send(embed=embed)
            print(f"[{ctx.guild.name}] [Comando Play] Música adicionada à fila: {song_data['title']}")

            if state['playing_task'] is None or state['playing_task'].done():
                print(f"[{ctx.guild.name}] [Comando Play] Player task não está rodando ou terminou. Criando nova tarefa.")
                state['playing_task'] = self.bot.loop.create_task(self.audio_player_task(ctx))
            else:
                print(f"[{ctx.guild.name}] [Comando Play] Player task já está rodando. Música será adicionada à fila e tocada em sequência.")
        else:
            print(f"[{ctx.guild.name}] [Comando Play] Nenhuma música encontrada após processamento.")
            embed = discord.Embed(
                title="🔎 Nenhuma Música Encontrada",
                description="Não encontrei resultados para sua busca.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)


    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        print(f"[{ctx.guild.name}] [Comando Skip] Recebido comando 'skip'.")
        state = self.get_guild_state(ctx.guild)
        if not state['voice_client'] or not state['voice_client'].is_playing():
            print(f"[{ctx.guild.name}] [Comando Skip] Nenhuma música tocando para pular.")
            embed = discord.Embed(
                title="🚫 Nenhuma Música Tocando",
                description="Não tem nenhuma música tocando para pular.",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        voter = ctx.author
        if voter.id in state['skip_votes']:
            print(f"[{ctx.guild.name}] [Comando Skip] Usuário {voter.name} já votou para pular.")
            embed = discord.Embed(
                title="🗳️ Voto Duplicado",
                description=f"{voter.mention}, você já votou para pular esta música!",
                color=discord.Color.light_grey()
            )
            return await ctx.send(embed=embed)

        state['skip_votes'].add(voter.id)
        members_in_vc = [member for member in state['voice_client'].channel.members if not member.bot]
        required_votes = max(1, len(members_in_vc) // 2)
        print(f"[{ctx.guild.name}] [Comando Skip] Voto de {voter.name} adicionado. Votos atuais: {len(state['skip_votes'])}, necessários: {required_votes}.")

        if len(state['skip_votes']) >= required_votes:
            embed = discord.Embed(
                title="⏭️ Música Pulada!",
                description=f"Votação para pular aprovada! Pulando **{state['current_song']['title']}**.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            print(f"[{ctx.guild.name}] [Comando Skip] Votos suficientes. Pulando a música.")
            state['voice_client'].stop()
            state['skip_votes'].clear()
        else:
            embed = discord.Embed(
                title="🗳️ Voto Registrado",
                description=f"Seu voto para pular foi adicionado. Faltam **{required_votes - len(state['skip_votes'])}** votos para pular.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Votos atuais: {len(state['skip_votes'])}/{required_votes}")
            await ctx.send(embed=embed)


    @commands.command(name='stop')
    async def stop(self, ctx):
        print(f"[{ctx.guild.name}] [Comando Stop] Recebido comando 'stop'.")
        state = self.get_guild_state(ctx.guild)
        if state['voice_client'] and state['voice_client'].is_connected():
            print(f"[{ctx.guild.name}] [Comando Stop] Bot conectado. Parando e limpando...")
            state['queue'] = asyncio.Queue()
            state['loop_mode'] = False
            if state['playing_task']:
                print(f"[{ctx.guild.name}] [Comando Stop] Cancelando player task.")
                state['playing_task'].cancel()
                state['playing_task'] = None
            state['voice_client'].stop()
            await state['voice_client'].disconnect()
            state['voice_client'] = None
            if ctx.guild.id in self.vc_states:
                del self.vc_states[ctx.guild.id]
                print(f"[{ctx.guild.name}] [Comando Stop] Estado da guild removido.")
            embed = discord.Embed(
                title="⏹️ Parado!",
                description="Parece que a festa acabou. Desconectado e fila limpa!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            print(f"[{ctx.guild.name}] [Comando Stop] Bot não está conectado a um canal de voz.")
            embed = discord.Embed(
                title="🚫 Não Conectado",
                description="Não estou conectado a um canal de voz.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @commands.command(name='loop')
    async def loop(self, ctx):
        print(f"[{ctx.guild.name}] [Comando Loop] Recebido comando 'loop'.")
        state = self.get_guild_state(ctx.guild)
        if not state['voice_client'] or not state['voice_client'].is_playing():
            print(f"[{ctx.guild.name}] [Comando Loop] Nenhuma música tocando para colocar em loop.")
            embed = discord.Embed(
                title="🚫 Nenhuma Música Tocando",
                description="Não tem nenhuma música tocando para colocar em loop.",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        state['loop_mode'] = not state['loop_mode']
        if state['loop_mode']:
            embed = discord.Embed(
                title="🔁 Loop Ativado!",
                description=f"O modo de loop para **{state['current_song']['title']}** foi **ativado**!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            print(f"[{ctx.guild.name}] [Comando Loop] Loop ativado para {state['current_song']['title']}.")
        else:
            embed = discord.Embed(
                title="🔂 Loop Desativado!",
                description="O modo de loop foi **desativado**.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            print(f"[{ctx.guild.name}] [Comando Loop] Loop desativado.")

    @commands.command(name='queue', aliases=['q'])
    async def show_queue(self, ctx):
        print(f"[{ctx.guild.name}] [Comando Queue] Recebido comando 'queue'.")
        state = self.get_guild_state(ctx.guild)
        if state['queue'].empty() and not state['current_song']:
            print(f"[{ctx.guild.name}] [Comando Queue] Fila de reprodução vazia.")
            embed = discord.Embed(
                title="Empty Queue",
                description="A fila de reprodução está vazia. Adicione algumas músicas com `!play <nome da música>`!",
                color=discord.Color.dark_grey()
            )
            return await ctx.send(embed=embed)

        queue_list = list(state['queue']._queue)
        embed = discord.Embed(title="Fila de Reprodução", color=discord.Color.blue())
        print(f"[{ctx.guild.name}] [Comando Queue] Gerando embed da fila.")

        if state['current_song']:
            embed.add_field(name="Tocando agora:", value=f"**[{state['current_song']['title']}]({state['current_song']['url']})** por {state['current_song']['uploader']}", inline=False)
            print(f"[{ctx.guild.name}] [Comando Queue] Adicionado música atual ao embed: {state['current_song']['title']}")

        if not queue_list:
            embed.description = "Nenhuma música na fila (além da atual)."
            print(f"[{ctx.guild.name}] [Comando Queue] Nenhuma música na fila, apenas a atual.")
        else:
            queue_str = ""
            for i, song in enumerate(queue_list):
                queue_str += f"{i+1}. **[{song['title']}]({song['url']})** por {song['uploader']}\n"
                if len(queue_str) > 1000:
                    queue_str += f"\n... e mais {len(queue_list) - (i+1)} músicas."
                    print(f"[{ctx.guild.name}] [Comando Queue] Fila muito longa, truncada para o embed.")
                    break
            embed.description = queue_str
            print(f"[{ctx.guild.name}] [Comando Queue] Fila adicionada ao embed.")
        
        embed.set_footer(text=f"Total na fila: {len(queue_list)} músicas")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))
    print("[Music Cog] Cog de música adicionada ao bot.")
