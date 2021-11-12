# SwiperBot
A simple Discord music bot written in Python.

# Installation

1. Clone this repository

2. Install ffmeg and opus

3. Install python3.8

4. Install poetry

5. Use poetry to install dependencies:
```poetry install```

6. Set environment variables (details below).

# Running

To run in foreground, run swipe.sh. To run in background run back_swipe.sh.
To kill the previous background instance run no_swiping.sh.
To restart a background task, run reset.sh.

# Music Commands

Below are the commands for the music features.

## !play

The play command adds a song to the queue and begins playing.

alias: !p, !swipe

usage: !play <Youtube video title or url\>

## !pause

The pause command pauses the playback of the current song. After 10 minutes of pausing, the bot will auto disconnect and delete the queue.

alias: None

usage: !pause

## !resume

The resume command resumes playback after pausing.

alias: None

usage: !resume
  
## !skip

The skip command stops the song that is currently playing and continues to next song in queue.

alias: !s

usage: !skip

## !clear

The clear command ends the current song and removes all songs in the queue.

alias: !c, !swipernoswiping, !noswiping

usage: !clear


## !queue

The queue command displays the next 10 songs in the queue and their indices (1-indexed).

alias: !q, !swiped

usage: !queue

## !nowplaying

The nowplaying command displays the song that is currently being played.

alias: !np

usage: !nowplaying

## !remove

The remove command removes a song at a specified index (1-indexed).

alias: !r

usage: !remove <index\>

## !disconnect

The disconnect command forces the bot to disconnect and deletes the queue.

alias: !dc

usage: !disconnect

## !shuffle

The shuffle command randomizes either the whole queue or a part of the queue. To shuffle only part of the queue you can optionally enter only the starting index or both the starting and ending indices of the section you want to shuffle. The ending index is non-inclusive.

alias: !sh

usage: !shuffle [starting index [ending index]]

# A note on secrets and environment variables

There are several APIs that this bot can utilize. If you do not want to use certain features you can remove the imports to the Python files that call them and remove the functions from the command dictionary.

The bot token should be stored as an environment variable with the name 'SWIPER_TOKEN'

The scripts rely on having an environment variable 'SWIPER_HOME' that is the path to the main directory of this repository.

This also now requires a Youtube API key as an environment variable with name 'YOUTUBE_KEY'. I will rework this later so the youtube api key is not required.

The Google Vision features require credentials. I chose to store the credentials in ```~/.gcp/xxx.json```, and then set the environment variable 'GOOGLE_APPLICATION_CREDENTIALS' to that path. You can create this credential file [here](https://console.cloud.google.com/apis/credentials).

The AWS Polly text to speech feature requires a config file and a credentials file. It will search for these as ```~/.aws/config``` and ```~/.aws/credentials```. For more information see [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).
