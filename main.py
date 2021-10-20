from __future__ import unicode_literals
import os
import discord
import validators
import asyncio
import glob
from youtube_search import YoutubeSearch
from urllib.parse import urlparse, parse_qs
from music_queue import Music_Queue, Node
from timeout import Timer
import youtube_dl
from youtube_dl import YoutubeDL

import googleapiclient.discovery

import re

import ctypes
import ctypes.util


if __name__ == '__main__':

    yt_key = os.environ['YOUTUBE_KEY']

    TIMEOUT = 60.0

    print("ctypes - Find opus:")
    a = ctypes.util.find_library('opus')
    print(a)
     
    print("Discord - Load Opus:")
    b = discord.opus.load_opus(a)
    print(b)
     
    print("Discord - Is loaded:")
    c = discord.opus.is_loaded()
    print(c)

    # on start up remove previously downloaded songs
    mp3s = glob.glob("./*.mp3")
    for mp3 in mp3s:
      os.remove(mp3)

    prefix = '!'

    client = discord.Client()

mq_dict = {}
curr_song = {}

# https://stackoverflow.com/questions/66610012/discord-py-streaming-youtube-live-into-voice
ytdlopts_stream = {
  'format': 'bestaudio/best',
  'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
  'restrictfilenames': True,
  'noplaylist': True,
  'nocheckcertificate': True,
  'ignoreerrors': False,
  'logtostderr': False,
  'quiet': True,
  'no_warnings': True,
  'default_search': 'auto',
  'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}
ytdl = YoutubeDL(ytdlopts_stream)
ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}

admin_ids = [os.environ['ADMIN_0'], os.environ['ADMIN_1'], os.environ['ADMIN_2']]
token = os.environ['SWIPER_TOKEN']

timer = {}




def get_yt_video_url(id: str) -> str:
  return 'https://www.youtube.com/watch?v={0}'.format(id)


# initial version: http://stackoverflow.com/a/7936523/617185 \
#    by Mikhail Kashkin(http://stackoverflow.com/users/85739/mikhail-kashkin)
def get_yt_video_id(url: str) -> str:
    """Returns Video_ID extracting from the given url of Youtube
    
    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
      
      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """


    if url.startswith(('youtu', 'www')):
        url = 'http://' + url
        
    query = urlparse(url)
    
    if 'youtube' in query.hostname:
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        raise ValueError

async def auto_dc(message, guild):
  #print("Auto disconnecting")
  await message.channel.send("Disconnecting due inactivity")
  vc = guild.voice_client
  if vc is None:
    return
  await vc.disconnect()

async def pause_dc(message, guild):
  vc = guild.voice_client
  if vc and vc.is_playing():
    return
  if guild.id in mq_dict:
    del mq_dict[guild.id]
  if guild.id in curr_song:
    del curr_song[guild.id]
  #if guild.id in timer:
  #  t = timer[guild.id]
  #  t.cancel()
  #  del timer[guild.id]
  if vc:
    if vc.is_playing() or vc.is_paused():
      vc.stop()
    await vc.disconnect()



def _auto_dc(guild):
  print("_auto_dc")
  vc = guild.voice_client
  if vc is None:
    return
  asyncio.run(vc.disconnect())
  #asyncio.run(auto_dc(guild))

async def play_list(message, pl_id, index):
  guild = message.guild
  channel = message.author.voice.channel
  id = ""
  title = ""
  youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=yt_key)

  request = youtube.playlistItems().list(
      part = "snippet",
      playlistId = pl_id,
      maxResults = 500
  )
  response = request.execute()

  playlist_items = []
  while request is not None:
      response = request.execute()
      playlist_items += response["items"]
      request = youtube.playlistItems().list_next(request, response)

  print(f"Enqueuing {len(playlist_items)} playlist items")
  title = playlist_items[index]['snippet']['title']
  await message.channel.send("Swiped " + title + " and " + str(len(playlist_items)-1-index) + " more")
  #print(playlist_items[0])

  if guild.id in mq_dict:
    mq = mq_dict[guild.id]
    for video in playlist_items[index:]:
      id = video['snippet']['resourceId']['videoId']
      url = get_yt_video_url(id)
      title = video['snippet']['title']
      mq.add(Node(url, title, channel))
  else:
    mq = Music_Queue()
    for video in playlist_items[index:]:
      id = video['snippet']['resourceId']['videoId']
      url = get_yt_video_url(id)
      title = video['snippet']['title']
      mq.add(Node(url, title, channel))
    mq_dict[guild.id] = mq
    vc = await channel.connect(timeout=TIMEOUT, reconnect=True)
    await play_next(mq, None, message, vc)
  #for video in playlist_items:
  #  #print(video['snippet']['title'])


async def play_song(message, args):
  id = ""
  title = ""
  guild = message.guild
  if message.author.voice is None:
    await message.channel.send("Must be in a voice call to use !play.")
    return
  elif guild.voice_client and \
        message.author.voice.channel != guild.voice_client.channel and \
        (guild.voice_client.is_playing() or guild.voice_client.is_paused()):
    return await message.channel.send("I am currently playing in a different voice channel!")
  channel = message.author.voice.channel
  perm = channel.permissions_for(guild.me)
  if not (perm.connect and perm.speak):
    await message.channel.send("I do not have permission to speak in this channel.")
    return
  if len(args) == 0:
    await message.channel.send("Error: play command requires YouTube link or search terms.")
    return
  if len(args) == 1 and validators.url(args[0]):
    try:
      id = get_yt_video_id(args[0])
    except ValueError:
      return await message.channel.send("Currently only accepting Youtube links.")

    url = get_yt_video_url(id)
    opts = {}
    with youtube_dl.YoutubeDL(opts) as ydl:
      info_dict = ydl.extract_info(url, download=False)
      title = info_dict.get('title', None)
    
    pl_re = re.search("[?&]list=([^#\&\?\n]+)", args[0])
    if pl_re:
      pl_id = pl_re.group(1)
      in_re = re.search("[?&]index=([^#\&\?\n]+)", args[0])
      index = 0
      if in_re:
        index = int(in_re.group(1)) - 1
      return await play_list(message, pl_id, index)

  else:
    results = YoutubeSearch(' '.join(args), max_results=1).to_dict()
    id = results[0]['id']
    title = results[0]['title']
  
  if guild.id in timer:
    t = timer[guild.id]
    t.cancel()
    del timer[guild.id]

  url = get_yt_video_url(id)

  await message.channel.send("Swiped " + title + " into queue.")

  if guild.id in mq_dict:
    mq = mq_dict[guild.id]
    mq.add(Node(url, title, channel))
    if not guild.voice_client:
      vc = await channel.connect(timeout=TIMEOUT, reconnect=True)
      await play_next(mq, None, message, vc)
  else:
    mq = Music_Queue()
    mq.add(Node(url, title, channel))
    mq_dict[guild.id] = mq
    vc = guild.voice_client
    if vc is None:
      vc = await channel.connect(timeout=TIMEOUT, reconnect=True)
    await play_next(mq, None, message, vc)



# Old play_next function which relies on downloading
"""async def play_next(mq: Music_Queue, prev_id, message, vc):
  guild = message.guild
  if prev_id is not None:
    os.remove('{0}.mp3'.format(prev_id))
  if not mq.hasNext():
    del mq_dict[guild.id]
    del curr_song[guild.id]
    # set auto disconnect timer
    timer[guild.id] = Timer(300.0, auto_dc, args=[message, guild])
    return
  ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': './%(id)s.mp3',
    'postprocessors': [{
      'key': 'FFmpegExtractAudio',
      'preferredcodec': 'mp3',
      'preferredquality': '192'
    }]
  }
  song = mq.getNext()
  id = get_yt_video_id(song.url)
  await message.channel.send("Now playing: " + song.title)
  curr_song[guild.id] = song
  if not os.path.exists('{0}.mp3'.format(id)):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download([song.url])
  if not vc.is_connected():
    try:
      await vc.connect(reconnect=True, timeout=TIMEOUT)
    except asyncio.TimeoutError:
      await message.channel.send("Error: ")
      await message.channel.send("Aborting...")
      del mq_dict[guild.id]
      del curr_song[guild.id]
  try:
    vc.play(discord.FFmpegPCMAudio(source='{0}.mp3'.format(id)))
  except Exception as error:
    await message.channel.send("Error: " + error)
    await message.channel.send("Aborting...")
    del mq_dict[guild.id]
    vc.stop()
  if mq.hasNext():
    nextSong = mq.peek()
    nextid = get_yt_video_id(nextSong.url)
    ydl_opts = {
      'format': 'bestaudio/best',
      'outtmpl': './%(nextid)s.mp3',
      'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
      }]
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      try:
        ydl.download([nextSong.url])
      except Exception as error:
        await message.channel.send("Error: " + error)
        await message.channel.send("Aborting...")
        del mq_dict[guild.id]
        del curr_song[guild.id]
        vc.stop()
  while vc.is_playing():
    await asyncio.sleep(1)
  if guild.id not in mq_dict:
    return await vc.disconnect()
  await play_next(mq, id, message, vc)"""

async def play_next(mq: Music_Queue, prev_id, message, vc):
  guild = message.guild
  if not mq.hasNext():
    del mq_dict[guild.id]
    del curr_song[guild.id]
    # set auto disconnect timer
    timer[guild.id] = Timer(300.0, auto_dc, args=[message, guild])
    return
  song = mq.getNext()
  id = get_yt_video_id(song.url)
  await message.channel.send("Now playing: " + song.title, delete_after=60.0)
  curr_song[guild.id] = song
  try:
    data = ytdl.extract_info(url=song.url, download=False)
  except:
    await message.channel.send("Error playing {0}!".format(song.title))
    return await play_next(mq, id, message, vc)

  #source = ytdl.prepare_filename(data)

  if not vc.is_connected():
    try:
      await vc.connect(reconnect=True, timeout=TIMEOUT)
    except asyncio.TimeoutError:
      await message.channel.send("Error")
      await message.channel.send("Aborting...")
      del mq_dict[guild.id]
      del curr_song[guild.id]
  try:
    vc.play(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options))
    #vc.play(discord.FFmpegPCMAudio(song.url, **ffmpeg_options))
    while vc.is_playing():
      await asyncio.sleep(1)
  except:
    await message.channel.send("Error playing {0}".format(song.title))
  if guild.id not in mq_dict:
    return await vc.disconnect()
  await play_next(mq, id, message, vc)

async def pause(message):
  guild = message.guild
  vc = guild.voice_client
  if vc is None:
    return await message.channel.send("I'm not currently in a voice channel!")
  elif not message.author.voice or message.author.voice.channel != vc.channel:
    return await message.channel.send("We are not in the same voice channel!")
  elif not vc.is_playing():
    return await message.channel.send("There is nothing to playing!")
  else:
    vc.pause()
    await message.channel.send(("Playback is paused. Use {0}resume to continue."
    "I will automatically leave in 10 minutes.").format(prefix), delete_after=600.0)
    if guild.id in timer:
      t = timer[guild.id]
      t.cancel()
    timer[guild.id] = Timer(30.0, pause_dc, args=[message, guild])

async def resume(message):
  guild = message.guild
  vc = guild.voice_client
  if vc is None:
    return await message.channel.send("I'm not currently in a voice channel!")
  elif not message.author.voice or message.author.voice.channel != vc.channel:
    return await message.channel.send("We are not in the same voice channel!")
  elif not vc.is_paused():
    return await message.channel.send("There is nothing to resume!")
  else:
    vc.resume()
    if guild.id in timer:
      t = timer[guild.id]
      t.cancel()
      del timer[guild.id]
      print("timer canceled")


async def skip(message):
  guild = message.guild
  vc = guild.voice_client
  if vc is None:
    return await message.channel.send("I'm not currently in a voice channel!")
  elif not (vc.is_playing() or vc.is_paused()):
    return await message.channel.send("There is nothing to skip!")
  elif not message.author.voice or message.author.voice.channel != vc.channel:
    return await message.channel.send("We are not in the same voice channel!")
  else:
    await message.channel.send("Skipped!")
    vc.stop()

async def clear(message):
  guild = message.guild
  vc = guild.voice_client
  if vc is None:
    return await message.channel.send("I'm not currently in a voice channel!")
  elif not (vc.is_playing() or vc.is_paused()):
    return await message.channel.send("There is nothing to clear!")
  elif not message.author.voice or message.author.voice.channel != vc.channel:
    return await message.channel.send("We are not in the same voice channel!")
  else:
    #await message.channel.send("Queue cleared!")
    await message.channel.send("Oh, man!")
    #mq_dict[guild.id] = Music_Queue()
    #del mq_dict[guild.id]
    mq_dict[guild.id].clear()
    vc.stop()

async def show_queue(message):
  if message.guild.id not in mq_dict:
    return await message.channel.send("There are no songs in the queue")
  songs = mq_dict[message.guild.id].getQueue()

  v = ""

  for i, song in enumerate(songs[:min(len(songs), 10)]):
    v += str(i+1) + ":\t" + song.title + "\n"
  v = v[:-1]

  embed=discord.Embed()
  embed.add_field(name="Queue", value=v, inline=False)
  await message.channel.send(embed=embed)

async def now_playing(message):
  if message.guild.id not in curr_song:
    return await message.channel.send("Nothing is being played right now!")
  return await message.channel.send("Now playing: " + curr_song[message.guild.id].title)

async def remove(message, index_str: str):
  if message.guild.id not in mq_dict:
    return await message.channel.send("There are no songs to remove")
  guild = message.guild
  try:
    idx = int(index_str)
  except ValueError:
    return await message.channel.send("You must provide the number in the queue to remove")
  mq = mq_dict[guild.id]
  if idx > mq.length or idx < 1:
    return await message.channel.send("Position must be between 1 and " + mq.length)
  removed_song = mq.remove(idx - 1)
  return await message.channel.send("Removed " + removed_song.title)

async def disconnect_vc(message):
  print("dc")
  guild = message.guild
  vc = guild.voice_client
  if vc is None:
    return await message.channel.send("I am not in a voice channel")
  if guild.id in mq_dict:
    del mq_dict[guild.id]
  if guild.id in curr_song:
    del curr_song[guild.id]
  if guild.id in timer:
    t = timer[guild.id]
    t.cancel()
    del timer[guild.id]
  if vc.is_playing() or vc.is_paused():
    vc.stop()
  await vc.disconnect()

# Shuffles songs in the music queue.
# no arguments: shuffle entire queue
# one argument: shuffle from given index to end
# two arguments: shuffle from smaller to larger index
async def shuffle(message, args):
  guild = message.guild
  vc = guild.voice_client
  if guild.id not in mq_dict or mq_dict[guild.id].length==0:
    return await message.channel.send("There is nothing to shuffle!")
  mq = mq_dict[guild.id]
  if len(args) == 0:
    await message.channel.send("Shuffling!")
    return mq.shuffle()
  elif len(args) == 1:
    try:
      start = int(args[0])
    except ValueError:
      return await message.channel.send("Indices must be integers!")
    if start < 1 or start > mq.length:
      return await message.channel.send("Index out of range!")
    else:
      await message.channel.send("Shuffling!")
      return mq.shuffle(start=start-1)
  else:
    try:
      start = int(args[0])
      end = int(args[1])
    except ValueError:
      return await message.channel.send("Indices must be integers!")
    if start > end:
      start, end = end, start
    if start < 1 or start > mq.length or end < 1 or end > mq.length:
      return await message.channel.send("Index out of range!")
    else:
      await message.channel.send("Shuffling!")
      return mq.shuffle(start=start-1, end=end-1)

async def hard_reset():
  print("hr...")
  for key in mq_dict:
    guild = client.get_guild(key)
    vc = guild.voice_client
    if vc:
      await vc.disconnect(force=True)
  print("Hard reset")
  #os.spawnl(os.P_NOWAIT, "reset.sh", "")
  os.execl("nohup", "poetry", "run", "python3.8", "main.py", "&")

@client.event
async def on_ready():
  print("test")
  await client.change_presence(status=discord.Status.online, activity=discord.Game("You're too late! You'll never find it now!"))
  print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return
  if message.content.startswith(prefix):
    #await message.channel.send('Hello!')
    command = message.content.split(' ')
    c = command[0].lower()
    if c == "{0}play".format(prefix) or c == "{0}p".format(prefix) or c == "{0}swipe".format(prefix):
      await play_song(message, command[1:])
    elif c == "{0}pause".format(prefix):
      await pause(message)
    elif c == "{0}resume".format(prefix):
      await resume(message)
    elif c == "{0}skip".format(prefix) or c == "{0}s".format(prefix):
      await skip(message)
    elif c == "{0}clear".format(prefix) or c == "{0}c".format(prefix) or c == "{0}noswiping".format(prefix) or c == "{0}swipernoswiping".format(prefix):
      await clear(message)
    elif c == "{0}queue".format(prefix) or c == "{0}q".format(prefix) or c == "{0}inventory".format(prefix) or c == "{0}swiped".format(prefix):
      await show_queue(message)
    elif c == "{0}nowplaying".format(prefix) or c == "{0}np".format(prefix) or c == "{0}youretoolate".format(prefix):
      await now_playing(message)
    elif c == "{0}remove".format(prefix) or c == "{0}r".format(prefix):
      await remove(message, command[1])
    elif c == "{0}disconnect".format(prefix) or c == "{0}dc".format(prefix):
      await disconnect_vc(message)
    elif c == "{0}shuffle".format(prefix) or c=="{0}sh".format(prefix):
      await shuffle(message, command[1:])
    #elif c == "{0}hardreset".format(prefix) and str(message.author.id) in admin_ids:
    #  print("entering reset")
    #  await hard_reset()

if __name__ == '__main__':
  client.run(token)
