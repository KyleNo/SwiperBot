from __future__ import unicode_literals
import os
import discord

from player import Player

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


@client.event
async def on_ready():
  print("test")
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
    if c == "{0}play".format(prefix) or c == "{0}p".format(prefix) or c == "{0}swipe".format(prefix):
      await p.play_song(message, command[1:])
    elif c == "{0}pause".format(prefix):
      await p.pause(message)
    elif c == "{0}resume".format(prefix):
      await p.resume(message)
    elif c == "{0}skip".format(prefix) or c == "{0}s".format(prefix):
      await p.skip(message)
    elif c == "{0}clear".format(prefix) or c == "{0}c".format(prefix) or c == "{0}noswiping".format(prefix) or c == "{0}swipernoswiping".format(prefix):
      await p.clear(message)
    elif c == "{0}queue".format(prefix) or c == "{0}q".format(prefix) or c == "{0}inventory".format(prefix) or c == "{0}swiped".format(prefix):
      await p.show_queue(message)
    elif c == "{0}nowplaying".format(prefix) or c == "{0}np".format(prefix) or c == "{0}youretoolate".format(prefix):
      await p.now_playing(message)
    elif c == "{0}remove".format(prefix) or c == "{0}r".format(prefix):
      await p.remove(message, command[1])
    elif c == "{0}disconnect".format(prefix) or c == "{0}dc".format(prefix):
      await p.disconnect_vc(message)
    elif c == "{0}shuffle".format(prefix) or c=="{0}sh".format(prefix):
      await p.shuffle(message, command[1:])
    #elif c == "{0}hardreset".format(prefix) and str(message.author.id) in admin_ids:
    #  print("entering reset")
    #  await hard_reset()

if __name__ == '__main__':
  client.run(token)
