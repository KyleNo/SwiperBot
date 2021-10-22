from __future__ import unicode_literals

from music_queue import Music_Queue, Node
from url_id import get_yt_video_url, get_yt_video_id

import os
import discord
import asyncio
import glob
from youtube_search import YoutubeSearch
from timeout import Timer
import youtube_dl
from youtube_dl import YoutubeDL
import validators

import googleapiclient.discovery

import re

import ctypes
import ctypes.util

TIMEOUT = 60.0

prefix = '!'

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

class Player:
  def __init__(self, guild, client):
    self.guild = guild
    self.client = client
    self.gid = guild.id
    self.mq = None
    self.curr_song = None
    self.dc_timer = None
    self.pause_timer = None
    self.token = os.environ['SWIPER_TOKEN']
    self.yt_key = os.environ['YOUTUBE_KEY']
  
  async def auto_dc(self, message):
    #print("Auto disconnecting")
    await message.channel.send("Disconnecting due inactivity")
    vc = self.guild.voice_client
    if vc is None:
      return
    await vc.disconnect()

  async def pause_dc(self, message):
    vc = self.guild.voice_client
    if vc and vc.is_playing():
      return
    if self.mq:
      self.mq = None
    if self.curr_song:
      self.curr_song = None
    #if guild.id in timer:
    #  t = timer[guild.id]
    #  t.cancel()
    #  del timer[guild.id]
    if vc:
      if vc.is_playing() or vc.is_paused():
        vc.stop()
      await vc.disconnect()
  
  async def play_list(self, message, pl_id, index):
    channel = message.author.voice.channel
    id = ""
    title = ""
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=self.yt_key)

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

    if self.mq:
      for video in playlist_items[index:]:
        id = video['snippet']['resourceId']['videoId']
        url = get_yt_video_url(id)
        title = video['snippet']['title']
        self.mq.add(Node(url, title, channel))
    else:
      self.mq = Music_Queue()
      for video in playlist_items[index:]:
        id = video['snippet']['resourceId']['videoId']
        url = get_yt_video_url(id)
        title = video['snippet']['title']
        self.mq.add(Node(url, title, channel))
      vc = await channel.connect(timeout=TIMEOUT, reconnect=True)
      await self.play_next(mq, None, message, vc)
    #for video in playlist_items:
    #  #print(video['snippet']['title'])


  async def play_song(self, message, args):
    id = ""
    title = ""
    g = self.guild
    if message.author.voice is None:
      await message.channel.send("Must be in a voice call to use !play.")
      return
    elif g.voice_client and \
          message.author.voice.channel != g.voice_client.channel and \
          (g.voice_client.is_playing() or g.voice_client.is_paused()):
      return await message.channel.send("I am currently playing in a different voice channel!")
    channel = message.author.voice.channel
    perm = channel.permissions_for(self.guild.me)
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
        return await self.play_list(message, pl_id, index)

    else:
      results = YoutubeSearch(' '.join(args), max_results=1).to_dict()
      id = results[0]['id']
      title = results[0]['title']
    
    if self.dc_timer:
      self.dc_timer.cancel()
      self.dc_timer = None

    url = get_yt_video_url(id)

    await message.channel.send("Swiped " + title + " into queue.")

    if self.mq:
      self.mq.add(Node(url, title, channel))
      if not self.guild.voice_client:
        vc = await channel.connect(timeout=TIMEOUT, reconnect=True)
        await self.play_next(None, message, vc)
    else:
      self.mq = Music_Queue()
      self.mq.add(Node(url, title, channel))
      vc = self.guild.voice_client
      if vc is None:
        vc = await channel.connect(timeout=TIMEOUT, reconnect=True)
      await self.play_next(None, message, vc)

  async def play_next(self, prev_id, message, vc):
    if not self.mq.hasNext():
      self.mq = None
      self.curr_song = None
      # set auto disconnect timer
      self.dc_timer = Timer(300.0, self.auto_dc, args=[message])
      return
    song = self.mq.getNext()
    id = get_yt_video_id(song.url)
    await message.channel.send("Now playing: " + song.title, delete_after=60.0)
    self.curr_song = song
    try:
      data = ytdl.extract_info(url=song.url, download=False)
    except:
      await message.channel.send("Error playing {0}!".format(song.title))
      return await self.play_next(id, message, vc)

    #source = ytdl.prepare_filename(data)

    if not vc.is_connected():
      try:
        await vc.connect(reconnect=True, timeout=TIMEOUT)
      except asyncio.TimeoutError:
        await message.channel.send("Error")
        await message.channel.send("Aborting...")
        self.mq = None
        self.curr_song = None
    try:
      vc.play(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options))
      #vc.play(discord.FFmpegPCMAudio(song.url, **ffmpeg_options))
      while vc.is_playing():
        await asyncio.sleep(1)
    except:
      await message.channel.send("Error playing {0}".format(song.title))
    if not self.mq:
      return await vc.disconnect()
    await self.play_next(id, message, vc)

  async def pause(self, message):
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
      #if self.pause_timer:
      #  self.pause_timer.cancel()
      guild.pause_timer = Timer(30.0, self.pause_dc, args=[message])

  async def resume(self, message):
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
      if self.pause_timer:
        self.pause_timer.cancel()
        self.pause_timer = None


  async def skip(self, message):
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

  async def clear(self, message):
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
      self.mq.clear()
      vc.stop()

  async def show_queue(self, message):
    if not self.mq:
      return await message.channel.send("There are no songs in the queue")
    songs = self.mq.getQueue()

    v = ""

    for i, song in enumerate(songs[:min(len(songs), 10)]):
      v += str(i+1) + ":\t" + song.title + "\n"
    v = v[:-1]

    embed=discord.Embed()
    embed.add_field(name="Queue", value=v, inline=False)
    await message.channel.send(embed=embed)

  async def now_playing(self, message):
    if not self.curr_song:
      return await message.channel.send("Nothing is being played right now!")
    return await message.channel.send("Now playing: " + self.curr_song.title)

  async def remove(self, message, index_str: str):
    if len(index_str) == 0:
      return await message.channel.send("You must provide the number in the queue to remove")
    index_str = index_str[0]
    if not self.mq:
      return await message.channel.send("There are no songs to remove")
    try:
      idx = int(index_str)
    except ValueError:
      return await message.channel.send("You must provide the number in the queue to remove")
    
    if idx > self.mq.length or idx < 1:
      return await message.channel.send("Position must be between 1 and " + self.mq.length)
    removed_song = self.mq.remove(idx - 1)
    return await message.channel.send("Removed " + removed_song.title)

  async def disconnect_vc(self, message):
    #print("dc")
    guild = message.guild
    vc = guild.voice_client
    if vc is None:
      return await message.channel.send("I am not in a voice channel")
    if self.mq:
      self.mq = None
    if self.curr_song:
      self.curr_song = None
    if self.dc_timer:
      self.dc_timer.cancel()
      self.dc_timer = None
    if self.pause_timer:
      self.pause_timer.cancel()
      self.pause_timer = None
    if vc.is_playing() or vc.is_paused():
      vc.stop()
    await vc.disconnect()

  # Shuffles songs in the music queue.
  # no arguments: shuffle entire queue
  # one argument: shuffle from given index to end
  # two arguments: shuffle from smaller to larger index
  async def shuffle(self, message, args):
    #guild = self.guild
    #vc = guild.voice_client
    if not self.mq or self.mq.length==0:
      return await message.channel.send("There is nothing to shuffle!")
    if len(args) == 0:
      await message.channel.send("Shuffling!")
      return self.mq.shuffle()
    elif len(args) == 1:
      try:
        start = int(args[0])
      except ValueError:
        return await message.channel.send("Indices must be integers!")
      if start < 1 or start > self.mq.length:
        return await message.channel.send("Index out of range!")
      else:
        await message.channel.send("Shuffling!")
        return self.mq.shuffle(start=start-1)
    else:
      try:
        start = int(args[0])
        end = int(args[1])
      except ValueError:
        return await message.channel.send("Indices must be integers!")
      if start > end:
        start, end = end, start
      if start < 1 or start > self.mq.length or end < 1 or end > self.mq.length:
        return await message.channel.send("Index out of range!")
      else:
        await message.channel.send("Shuffling!")
        return self.mq.shuffle(start=start-1, end=end-1)