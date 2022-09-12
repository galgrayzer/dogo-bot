import discord
from discord.ext import commands
from os import system as sys
from youtube_dl import YoutubeDL
from discord.utils import get
from youtubesearchpython import VideosSearch
from Lyrics import get_lyrics
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
current = None
url_queue = []
song_queue = []
bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Your command | perfix: ."))
    print('Bot is up and running!')


@bot.command(name='ping', help='Returning the current ping time the bot takes to respond')  # Ping
async def ping(ctx):
    await ctx.send(f'Current ping is {round(bot.latency * 1000)}ms')


@bot.command(name='join', help='Joining the voice channel')  # Join
async def join(ctx):
    channel = ctx.author.voice.channel
    if channel:
        await channel.connect()
    else:
        await ctx.send('You need to join a voice channel first!')


@bot.command(name='leave', help='Leaving the voice channel')  # Leave
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
@bot.command(name='play', help='Playing a song from YouTube', aliases=['p'])
async def play(ctx, *url):
    song = ' '.join(url)
    global current
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
                current = info['title']
                if not player.is_playing():
                    async with ctx.typing():
                        player.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS),
                                    after=lambda e: play(play_next(player) if url_queue else None))
                        await ctx.send(f'Now playing: {info["title"]}')
                        await ctx.send(url)
                else:
                    url_queue.append(URL)
                    song_queue.append(info["title"])
                    await ctx.send(f'Added to queue: {info["title"]}')
    else:
        await ctx.send('You need to join a voice channel first!')


def play_next(player):
    if url_queue:
        player.play(discord.FFmpegPCMAudio(url_queue.pop(0), **
                    FFMPEG_OPTIONS), after=lambda e: play_next(player))
        song_queue.pop(0)


@bot.command(name='stop', help='Stopping the song')  # Stop
async def stop(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_playing():
            player.stop()
            await ctx.send('Stopped the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


@bot.command(name='skip', help='Skipping the song', aliases=['s'])  # Skip
async def skip(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_playing():
            player.stop()
            await ctx.send('Skipped the song')
            # Add current
            play_next(player)
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


@bot.command(name='pause', help='Pausing the song')  # Pause
async def pause(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_playing():
            player.pause()
            await ctx.send('Paused the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


@bot.command(name='resume', help='Resuming the song', aliases=['h'])  # Resume
async def resume(ctx):
    channel = ctx.author.voice.channel
    if channel:
        player = get(bot.voice_clients, guild=ctx.guild)
        if player.is_paused():
            player.resume()
            await ctx.send('Resumed the song')
    else:
        await ctx.send('You need to be in a voice channel for this command to work')


# Lyrics
@bot.command(name='lyrics', help='Getting the lyrics of a song', aliases=['l'])
async def lyrics(ctx, *name):
    if name:
        name = ' '.join(name)
        lyrics = get_lyrics(name).replace('Embed', '')
        if len(lyrics) > 1900:
            await ctx.send(lyrics[:1900] + '...')
            await ctx.send(lyrics[1900:])
        await ctx.send(lyrics)
    elif current != None:
        lyrics = get_lyrics(current).replace('Embed', '')
        if len(lyrics) > 1900:
            await ctx.send(lyrics[:1900] + '...')
            await ctx.send(lyrics[1900:])
        await ctx.send(lyrics)
    else:
        await ctx.send('You need to play a song first!')


@bot.command(name='say', help='Saying something')  # Say
async def say(ctx):
    # join vc if not in one
    channel = ctx.author.voice.channel
    lang = 'en'
    if channel:
        if not get(bot.voice_clients, guild=ctx.guild):
            await channel.connect()
        player = get(bot.voice_clients, guild=ctx.guild)
        message = ctx.message.content[4:]
        if '=' in message:
            try:
                message, lang = message.split(' = ')
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
            player.play(create_voice_stream(message, lang),
                        after=lambda e: play_next(player))
        else:
            await ctx.send('I am already playing somthing...')

    else:
        await ctx.send('You need to join a voice channel first!')


# Queue
@bot.command(name='queue', help='Showing currntly queue', aliases=['q'])
async def queue(ctx):
    str = ''
    count = 1
    for song in song_queue:
        str += f'{count}. {song}\n'
        count += 1
    await ctx.send(f"Now playing - {current}\n" + str)


def create_voice_stream(text, lang):  # Create voice stream
    tts = gTTS(text=text, lang=lang)
    tts.save('voice_stream.mp3')
    return discord.FFmpegPCMAudio('voice_stream.mp3')


def main():
    sys('cls')
    bot.run('ODgwOTMzMTk1Njk5MzQzNDQw.GyGRaF.GTGLivPyJe2I66Sm99Sxhl7pEXnXQ_-USwH_j4')


if __name__ == '__main__':
    main()
