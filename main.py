from __future__ import unicode_literals
import os
import discord

from player import Player

from functools import partial
from typing import List

import ctypes
import ctypes.util


if __name__ == '__main__':
  print("ctypes - Find opus:")
  a = ctypes.util.find_library('opus')
  print(a)
     
  print("Discord - Load Opus:")
  b = discord.opus.load_opus(a)
  print(b)
     
  print("Discord - Is loaded:")
  c = discord.opus.is_loaded()
  print(c)

  client = discord.Client()

players = {}
prefix = '!'
token = os.environ['SWIPER_TOKEN']

def command_dispatch(s: str, p: Player, m: discord.Message, args: List[str]):
  return {
    "play":             partial(p.play_song, m, args),
    "p":                partial(p.play_song, m, args),
    "swipe":            partial(p.play_song, m, args),
    "pause":            partial(p.pause, m),
    "resume":           partial(p.resume, m),
    "skip":             partial(p.skip, m),
    "s":                partial(p.skip, m),
    "clear":            partial(p.clear, m),
    "c":                partial(p.clear, m),
    "noswiping":        partial(p.clear, m),
    "swipernoswiping":  partial(p.clear, m),
    "queue":            partial(p.show_queue, m),
    "q":                partial(p.show_queue, m),
    "swiped":           partial(p.show_queue, m),
    "nowplaying":       partial(p.now_playing, m),
    "np":               partial(p.now_playing, m),
    "remove":           partial(p.remove, m, args),
    "r":                partial(p.remove, m, args),
    "disconnect":       partial(p.disconnect_vc, m),
    "dc":               partial(p.disconnect_vc, m),
    "shuffle":          partial(p.shuffle, m, args),
    "sh":               partial(p.shuffle, m, args) 
  }.get(s)


@client.event
async def on_ready():
  await client.change_presence(status=discord.Status.online, activity=discord.Game("You're too late! You'll never find it now!"))
  print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  gid = message.guild.id
  if message.author == client.user:
    return
  if message.content.startswith(prefix):
    if gid in players:
      p = players[gid]
    else:
      p = Player(message.guild, client)
      players[gid] = p
    command = message.content.split(' ')
    c = command[0].lower()
    com_name = c[len(prefix):]
    args = command[1:]
    command_fn = command_dispatch(com_name, p, message, args)
    return await command_fn()


if __name__ == '__main__':
  client.run(token)
