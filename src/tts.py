from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
from tempfile import gettempdir
from discord import FFmpegPCMAudio
import asyncio
import json
from timeout import Timer

# on import, generate a dictionary of voices

sess = Session(profile_name="default")
ply = sess.client("polly")

try:
    resp = ply.describe_voices()
except (BotoCoreError, ClientError) as e:
    print(e)

voices = {}
for voice in resp["Voices"]:
    voices[voice["Id"]] = voice



"""
aws Polly example code
https://docs.aws.amazon.com/polly/latest/dg/get-started-what-next.html
"""
def generate_speech(text: str, voice: str, engine: str):
    session = Session(profile_name="default")
    polly = session.client("polly")

    try:
        response = polly.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice, Engine=engine)
    except (BotoCoreError, ClientError) as e:
        print(e)
        return None

    if "AudioStream" in response:
        """
        with closing(response["AudioStream"]) as stream:
            output = os.path.join(gettempdir(), "speech.mp3")
        """
        stream = response["AudioStream"]
        output = os.path.join(gettempdir(), "speech.mp3")
       
        try:
            with open(output, "wb") as file:
                file.write(stream.read())
                stream.close()
        except IOError as e:
            print(e)
            return None
        
        return (output, file)

    else:
        print("Could not stream audio")

async def tts(player, message, args):
    vc = player.guild.voice_client
    if message.author.voice is None:
        return await message.channel.send("Must be in a voice channel to use tts")
    elif len(args) == 0:
        return await message.channel.send("You didn't give me something to say")
    elif vc is None:
        channel = message.author.voice.channel
        perm = channel.permissions_for(player.guild.me)
        if not (perm.connect and perm.speak):
            return await message.channel.send("I do not have permission to speak in this channel.")
        try:
            vc = await message.author.voice.channel.connect(timeout=60.0, reconnect=True)
        except:
            return await message.channel.send("Error joining voice channel")
    else:
        if vc.is_playing() or vc.is_paused():
            return await message.channel.send("I'm busy playing music and cannot speak")

    # Done checking validity of request
    # Try to get tts audio file
    text = ' '.join(args)
    res = generate_speech(text, 'Kevin', 'neural')
    if res is None:
        return await message.channel.send("Error generating speech")
    output, f = res

    try:
        vc.play(FFmpegPCMAudio(source=output))
    except:
        return await message.channel.send("Error speaking")
    if player.dc_timer is not None:
        player.dc_timer.cancel()
    player.dc_timer = Timer(300.0, player.auto_dc, args=[message])
    f.close()

async def tts_chinese(player, message, args):
    vc = player.guild.voice_client
    if message.author.voice is None:
        return await message.channel.send("Must be in a voice channel to use tts")
    elif len(args) == 0:
        return await message.channel.send("You didn't give me something to say")
    elif vc is None:
        channel = message.author.voice.channel
        perm = channel.permissions_for(player.guild.me)
        if not (perm.connect and perm.speak):
            return await message.channel.send("I do not have permission to speak in this channel.")
        try:
            vc = await message.author.voice.channel.connect(timeout=60.0, reconnect=True)
        except:
            return await message.channel.send("Error joining voice channel")
    else:
        if vc.is_playing() or vc.is_paused():
            return await message.channel.send("I'm busy playing music and cannot speak")

    # Done checking validity of request
    # Try to get tts audio file
    text = ' '.join(args)
    res = generate_speech(text, 'Zhiyu', 'standard')
    if res is None:
        return await message.channel.send("Error generating speech")
    output, f = res

    try:
        vc.play(FFmpegPCMAudio(source=output))
    except:
        return await message.channel.send("Error speaking")

    if player.dc_timer is not None:
        player.dc_timer.cancel()
    player.dc_timer = Timer(300.0, player.auto_dc, args=[message])
    f.close()

async def tts_general(player, message, args):
    vc = player.guild.voice_client
    if message.author.voice is None:
        return await message.channel.send("Must be in a voice channel to use tts")
    elif len(args) == 0:
        return await message.channel.send("You didn't give me something to say")
    elif len(args) == 1:
        return await message.channel.send("Provide a voice id and something for me to say")
    elif vc is None:
        channel = message.author.voice.channel
        perm = channel.permissions_for(player.guild.me)
        if not (perm.connect and perm.speak):
            return await message.channel.send("I do not have permission to speak in this channel.")
        try:
            vc = await message.author.voice.channel.connect(timeout=60.0, reconnect=True)
        except:
            return await message.channel.send("Error joining voice channel")
    else:
        if vc.is_playing() or vc.is_paused():
            return await message.channel.send("I'm busy playing music and cannot speak")

    # Done checking validity of request
    # Try to get tts audio file
    voiceid = args[0]
    text=' '.join(args)
    if len(voiceid) > 1:
        voiceid = voiceid[0].upper() + voiceid[1:].lower()
        if voiceid in voices:
            text = ' '.join(args[1:])
    engine = 'neural'
    if voiceid not in voices:
        #default voice
        voiceid = 'Kevin'
    else:
        supported = voices[voiceid]["SupportedEngines"]
        if 'neural' not in supported:
            engine = 'standard'
    res = generate_speech(text, voiceid, engine)
    if res is None:
        return await message.channel.send("Error generating speech")
    output, f = res

    try:
        vc.play(FFmpegPCMAudio(source=output))
    except:
        return await message.channel.send("Error speaking")
    if player.dc_timer is not None:
        player.dc_timer.cancel()
    player.dc_timer = Timer(300.0, player.auto_dc, args=[message])
    f.close()

async def show_voices(message):
    #lst = [voice['Id'] + ": " + voice['LanguageName'] for voice in resp['Voices']]
    lst = [(voice['Id'], voice['LanguageName']) for voice in resp['Voices']]
    lst.sort(key=lambda tp: tp[1] + tp[0])
    lst = [tp[1] + ": " + tp[0] for tp in lst]
    s = 'Voices:\n' + '\n'.join(lst)
    return await message.channel.send(s)

async def voice_info(message, args):
    if len(args) == 0:
        return await message.channel.send("Provide a voice id to get info about. Use voices command to list all voices.")
    voiceid = args[0]
    if len(voiceid) < 2:
        return await message.channel.send("Invalid voice id")
    voiceid = voiceid[0].upper() + voiceid[1:].lower()
    if voiceid not in voices:
        return await message.channel.send("Invalid voice id")
    engine = 'neural'
    if 'neural' not in voices[voiceid]["SupportedEngines"]:
        engine = 'standard'
    s = "Name: " + voiceid + '\n' \
            + "Language: " + voices[voiceid]["LanguageName"] + '\n' \
            + "Gender: " + voices[voiceid]["Gender"] + '\n' \
            + "Engine: " + engine

    return await message.channel.send(s)
