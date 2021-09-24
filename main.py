from __future__ import unicode_literals
import os
import discord
import validators
import asyncio
import glob
from youtube_search import YoutubeSearch
from urllib.parse import urlparse, parse_qs
from music_queue import Music_Queue, Node

import youtube_dl

import ctypes
import ctypes.util

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

# initial version: http://stackoverflow.com/a/7936523/617185 \
#    by Mikhail Kashkin(http://stackoverflow.com/users/85739/mikhail-kashkin)

def get_yt_video_url(id: str) -> str:
  return 'https://www.youtube.com/watch?v={0}'.format(id)

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

async def play_song(message, args):
  id = ""
  title = ""
  guild = message.guild
  if message.author.voice is None:
    await message.channel.send("Must be in a voice call to use !play")
    return
  channel = message.author.voice.channel
  perm = channel.permissions_for(guild.me)
  if not (perm.connect and perm.speak):
    await message.channel.send("I do not have permission to speak in this channel.")
    return
  if len(args) == 0:
    await message.channel.send("Error: play command requires YouTube link or search terms")
    return
  if len(args) == 1 and validators.url(args[0]):
    id = get_yt_video_id(args[0])
    url = get_yt_video_url(id)
    opts = {}
    with youtube_dl.YoutubeDL(opts) as ydl:
      info_dict = ydl.extract_info(url, download=False)
      title = info_dict.get('title', None)

  else:
    results = YoutubeSearch(' '.join(args), max_results=1).to_dict()
    id = results[0]['id']
    title = results[0]['title']
  
  url = get_yt_video_url(id)

  await message.channel.send("Swiped " + title + " into queue.")

  if guild.id in mq_dict:
    mq = mq_dict[guild.id]
    mq.add(Node(url, title, channel))
  else:
    mq = Music_Queue()
    mq.add(Node(url, title, channel))
    mq_dict[guild.id] = mq
    vc = await channel.connect(timeout=60.0, reconnect=True)
    await play_next(mq, None, message, vc)

async def play_next(mq: Music_Queue, prev_id, message, vc):
  guild = message.guild
  if prev_id is not None:
    os.remove('{0}.mp3'.format(prev_id))
  if not mq.hasNext():
    del mq_dict[guild.id]
    await vc.disconnect()
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
  if not os.path.exists('{0}.mp3'.format(id)):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
      ydl.download([song.url])
  if not vc.is_connected():
    await vc.connect(reconnect=True, timeout=60.0)
  vc.play(discord.FFmpegPCMAudio(source='{0}.mp3'.format(id)))
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
      ydl.download([nextSong.url])
  while vc.is_playing():
    await asyncio.sleep(1)
  if guild.id not in mq_dict:
    return await vc.disconnect()
  await play_next(mq, id, message, vc)


async def skip(message):
  guild = message.guild
  vc = guild.voice_client
  if vc is None:
    return await message.channel.send("I'm not currently in a voice channel!")
  elif not (vc.is_playing() or vc.is_paused()):
    return await message.channel.send("There is nothing to skip!")
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
  else:
    #await message.channel.send("Queue cleared!")
    await message.channel.send("Aw man!")
    del mq_dict[guild.id]
    vc.stop()

@client.event
async def on_ready():
  print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return
  if message.content.startswith('!'):
    #await message.channel.send('Hello!')
    command = message.content.split(' ')
    c = command[0].lower()
    if c == "{0}play".format(prefix) or c == "{0}p".format(prefix) or c == "{0}swipe".format(prefix):
      await play_song(message, command[1:])
    elif c == "{0}skip".format(prefix) or c == "{0}s".format(prefix):
      await skip(message)
    elif c == "{0}clear".format(prefix) or c == "{0}c".format(prefix) or c == "{0}noswiping".format(prefix) or c == "{0}swipernoswiping".format(prefix):
      await clear(message)


token = os.environ['SWIPER_TOKEN']
client.run(token)
