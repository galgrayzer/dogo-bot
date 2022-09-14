import discord
from discord.ext import commands
from os import system as sys
from youtube_dl import YoutubeDL
from discord.utils import get
from youtubesearchpython import VideosSearch
from gtts import gTTS
from spotipy import Spotify
import spotipy.util as util


FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}


token = util.prompt_for_user_token('david.kim.9', 'user-read-currently-playing', client_id='02f03d97e6874a8ab9607ea1e987313c',
                                   client_secret='d433765cb3444c3d98abb248df2fcfb9', redirect_uri='http://localhost:8888/callback')
sp = Spotify(auth=token)


# Vars:

url_queue = []
song_queue = []

# Intents:

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True

# Client:

bot = commands.Bot(command_prefix='.', intents=intents)

# On Start:


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Your command | perfix: ."))
    await bot.tree.sync(guild=discord.Object(id=880926842603847680))
    await bot.tree.sync(guild=discord.Object(id=554699594420846616))

# Commands:


@bot.hybrid_command(name='ping', description='Returning the current ping time the bot takes to respond', help='Returning the current ping time the bot takes to respond')
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def ping(ctx):
    await ctx.send(f'Current ping is {round(bot.latency * 1000)}ms')


@bot.hybrid_command(name='join', help='Joining the voice channel')  # Join
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def join(ctx):
    channel = ctx.author.voice.channel
    if channel:
        await channel.connect()
    else:
        await ctx.send('You need to join a voice channel first!')


# Leave
@bot.hybrid_command(name='leave', description='Leaving the voice channel', help='Leaving the voice channel')
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def leave(ctx):
    player = get(bot.voice_clients, guild=ctx.guild)
    if player.is_playing():
        player.stop()
    channel = ctx.message.guild.voice_client
    if channel:
        await channel.disconnect()
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


# Play
@bot.hybrid_command(name='play', description='Playing a song from YouTube', help='Playing a song from YouTube', aliases=['p'])
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def play(ctx, *, song):
    if not song:
        ctx.send('You have to provide a song!')
    else:
        channel = ctx.author.voice.channel
        if channel:
            try:
                player = await channel.connect()
            except:
                player = get(bot.voice_clients, guild=ctx.guild)
            if 'https://open.spotify.com/playlist' in song:
                playlist_URI = song.split("/")[-1].split("?")[0]
                songs = [x["track"]["name"]
                         for x in sp.playlist_tracks(playlist_URI)["items"]]
                for song in songs:
                    await play(ctx, song)
            elif 'https://open.spotify.com/album' in song:
                album_URI = song.split("/")[-1].split("?")[0]
                songs = [f'{x["name"]} - {x["artists"][0]["name"]}'
                         for x in sp.album_tracks(album_URI)["items"]]
                for song in songs:
                    await play(ctx, song)
            else:
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    if 'https://www.youtube.com/' in song:
                        url = song
                    else:
                        videosSearch = VideosSearch(song, limit=1)
                        url = 'https://www.youtube.com/watch?v=' + \
                            videosSearch.result()['result'][0]['id']
                    info = ydl.extract_info(url, download=False)
                    URL = info['url']
                    song_queue.append(info['title'])
                    if not player.is_playing():
                        async with ctx.typing():
                            player.play(discord.FFmpegPCMAudio(
                                URL, **FFMPEG_OPTIONS),
                                after=lambda e: print('Player error: %s' % e) if e else play_next(player))
                            await ctx.send(f'Now playing: {info["title"]}')
                            await ctx.send(url)
                    else:
                        url_queue.append(URL)
                        await ctx.send(f'Added to queue: {info["title"]}')
        else:
            await ctx.send('You need to join a voice channel first!')


def play_next(player):
    if url_queue:
        player.play(discord.FFmpegPCMAudio(url_queue.pop(0), **
                                           FFMPEG_OPTIONS), after=lambda e: print(
            'Player error: %s' % e) if e else play_next(player))
    if song_queue:
        song_queue.pop(0)


# Stop
@bot.hybrid_command(name='stop', description='Stopping the song', help='Stopping the song')
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def stop(ctx, message=True):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_playing():
            player.stop()
            if message:
                await ctx.send('Stopped the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


# Skip
@bot.hybrid_command(name='skip', description='Skipping the song', help='Skipping the song', aliases=['s'])
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def skip(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_playing():
            await stop(ctx, False)
            await ctx.send('Skipped the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


# Pause
@bot.hybrid_command(name='pause', description='Pausing the song', help='Pausing the song')
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def pause(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_playing():
            player.pause()
            await ctx.send('Paused the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


# Resume
@bot.hybrid_command(name='resume', description='Resuming the song', help='Resuming the song', aliases=['h'])
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def resume(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_paused():
            player.resume()
            await ctx.send('Resumed the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


# Say
@bot.hybrid_command(name='say', description='Saying something', help='Saying something')
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def say(ctx, text=None):
    # join vc if not in one
    if text:
        channel = ctx.author.voice.channel
        lang = 'en'
        if channel:
            if not get(bot.voice_clients, guild=ctx.guild):
                await channel.connect()
            player = get(bot.voice_clients, guild=ctx.guild)
            if '=' in text:
                try:
                    text, lang = text.split(' = ')
                except:
                    await ctx.send('Invalid syntax! ("space = space")')
                    return
                if lang not in ['en', 'ru', 'it', 'fr', 'es', 'ja', 'de', 'pt', 'ar', 'ko']:
                    await ctx.send("""Language not supported!
                supported languages are:
                en - english
                ru - russian
                it - italian
                fr - french
                es - spanish
                ja - japanese
                de - german
                pt - portuguese
                ar - arabic
                ko - korean""")
                    return
            if not player.is_playing():
                player.play(create_voice_stream(text, lang),
                            after=lambda e: print('Player error: %s' % e) if e else play_next(player) if song_queue else None)
                await ctx.send(f'Saying {text}')
            else:
                await ctx.send('I am already playing somthing...')

        else:
            await ctx.send('You need to join a voice channel first!')
    else:
        await ctx.send("You must provide text!")


def create_voice_stream(text, lang):  # Create voice stream
    tts = gTTS(text=text, lang=lang)
    tts.save('voice_stream.mp3')
    return discord.FFmpegPCMAudio('voice_stream.mp3')


@bot.hybrid_command(name='queue', description='Showing player queue', help='Showing player queue', aliases=['q'])
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def queue(ctx):
    if song_queue:
        queue_str = f'*Now Playing: {song_queue[0]}*\n'
        for index in range(1, len(song_queue)):
            queue_str += f'{index}. {song_queue[index]}\n'
    else:
        queue_str = 'Nothing is playing right now.'
    await ctx.send(queue_str)


@bot.hybrid_command(name='clear', description="Clear's the queue", help="Clear's the queue")
@discord.app_commands.guilds(discord.Object(880926842603847680), discord.Object(554699594420846616))
async def clear(ctx):
    global song_queue, url_queue
    song_queue = []
    url_queue = []
    await stop(ctx, False)


def main():
    sys('cls')
    bot.run('ODgwOTMzMTk1Njk5MzQzNDQw.GyGRaF.GTGLivPyJe2I66Sm99Sxhl7pEXnXQ_-USwH_j4')


if __name__ == '__main__':
    main()
