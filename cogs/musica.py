import asyncio
import discord
from discord.ext import commands
import yt_dlp
import functools

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vc_states = {}
        
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

    def get_guild_state(self, guild):
        if guild.id not in self.vc_states:
            self.vc_states[guild.id] = {
                'queue': asyncio.Queue(),
                'current_song': None,
                'loop_mode': False,
                'voice_client': None,
                'skip_votes': set(),
                'playing_task': None,
                'is_playing': False,
            }
        return self.vc_states[guild.id]

    async def cleanup_voice_state(self, guild):
        state = self.get_guild_state(guild)
        if state['voice_client']:
            try:
                await state['voice_client'].disconnect()
            except:
                pass
        if guild.id in self.vc_states:
            del self.vc_states[guild.id]

    async def player_task(self, ctx):
        state = self.get_guild_state(ctx.guild)
        while True:
            try:
                state['is_playing'] = False
                state['current_song'] = await state['queue'].get()
                
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
                    'options': '-vn -filter:a "volume=0.8"'
                }
                
                source = discord.FFmpegPCMAudio(state['current_song']['url'], **ffmpeg_options)
                
                def after_playing(error):
                    coro = self.play_next(ctx, error)
                    asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                
                state['voice_client'].play(source, after=after_playing)
                state['is_playing'] = True
                
                await ctx.send(f"🎶 Tocando agora: **{state['current_song']['title']}**")
                
                while state['voice_client'].is_playing() or state['voice_client'].is_paused():
                    await asyncio.sleep(1)
                
                if state['loop_mode']:
                    await state['queue'].put(state['current_song'])
                    
            except Exception as e:
                print(f"Erro no player_task: {e}")
                await asyncio.sleep(2)
                continue

    async def play_next(self, ctx, error):
        state = self.get_guild_state(ctx.guild)
        if error:
            print(f"Erro na reprodução: {error}")
            await ctx.send(f"❌ Erro na reprodução: {error}")
        
        if state['queue'].empty() and not state['loop_mode']:
            await self.cleanup_voice_state(ctx.guild)
            await ctx.send("🎵 Fila terminada, desconectando...")

    @commands.command(name='play', aliases=['p', 'tocar'])
    async def play(self, ctx, *, search: str):
        """Toca uma música do YouTube"""
        if not ctx.author.voice:
            return await ctx.send("Você precisa estar em um canal de voz!")
        
        try:
            state = self.get_guild_state(ctx.guild)
            
            # Conectar ao canal de voz
            if not state['voice_client']:
                state['voice_client'] = await ctx.author.voice.channel.connect()
            elif state['voice_client'].channel != ctx.author.voice.channel:
                await state['voice_client'].move_to(ctx.author.voice.channel)

            # Buscar música
            with yt_dlp.YoutubeDL(self.YTDL_OPTIONS) as ydl:
                info = await self.bot.loop.run_in_executor(None, 
                    lambda: ydl.extract_info(search, download=False))
                
                if not info:
                    return await ctx.send("Nenhum resultado encontrado!")
                
                song = info['entries'][0] if 'entries' in info else info
                
                song_data = {
                    'url': song['url'],
                    'title': song.get('title', 'Sem título'),
                    'duration': song.get('duration', 0)
                }

                await state['queue'].put(song_data)
                await ctx.send(f"🎵 Adicionado à fila: **{song_data['title']}**")

                if not state['playing_task'] or state['playing_task'].done():
                    state['playing_task'] = self.bot.loop.create_task(self.player_task(ctx))
                    
        except Exception as e:
            await ctx.send(f"❌ Erro: {str(e)}")

    @commands.command(name='skip', aliases=['s', 'pular'])
    async def skip(self, ctx):
        """Pula a música atual"""
        state = self.get_guild_state(ctx.guild)
        
        if not state['voice_client'] or not state['is_playing']:
            return await ctx.send("Nada tocando no momento!")
        
        state['voice_client'].stop()
        await ctx.send("⏭️ Música pulada!")

    @commands.command(name='stop', aliases=['parar'])
    async def stop(self, ctx):
        """Para o player e limpa a fila"""
        state = self.get_guild_state(ctx.guild)
        
        if state['voice_client']:
            state['voice_client'].stop()
            await self.cleanup_voice_state(ctx.guild)
            await ctx.send("⏹️ Player parado e desconectado!")
        else:
            await ctx.send("O bot não está conectado!")

    @commands.command(name='loop', aliases=['l', 'repetir'])
    async def loop(self, ctx):
        """Ativa/desativa o modo loop"""
        state = self.get_guild_state(ctx.guild)
        state['loop_mode'] = not state['loop_mode']
        await ctx.send(f"🔁 Loop {'ativado' if state['loop_mode'] else 'desativado'}!")

    @commands.command(name='queue', aliases=['q', 'fila'])
    async def queue(self, ctx):
        """Mostra a fila de reprodução"""
        state = self.get_guild_state(ctx.guild)
        
        if state['queue'].empty() and not state['current_song']:
            return await ctx.send("🎵 A fila está vazia!")
        
        embed = discord.Embed(title="📋 Fila de Reprodução")
        
        if state['current_song']:
            embed.add_field(name="🎶 Tocando agora", 
                          value=state['current_song']['title'], inline=False)
        
        queue_list = list(state['queue']._queue)
        if queue_list:
            embed.add_field(name="Próximas músicas",
                          value="\n".join(f"{i+1}. {song['title']}" 
                                        for i, song in enumerate(queue_list[:5])),
                          inline=False)
        
        if state['loop_mode']:
            embed.set_footer(text="🔁 Modo loop ativado")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))
