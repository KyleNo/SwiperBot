# SwiperBot
A simple music bot written in Python.

# Installation

1. Clone this repository

2. Install ffmeg and opus

3. Install python3.8

4. Install poetry

5. Use poetry to install dependencies:
```poetry install```

6. Set SWIPER_TOKEN and YOUTUBE_KEY environment variables

# Running

To run in foreground, run swipe.sh. To run in background run back_swipe.sh.
To kill the previous background instance run no_swiping.sh.
To restart a background task, run reset.sh.

# Commands

This bot currently only supports minimal functionality:

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

# A note on secrets

The bot token should be stored as an environment variable with the name 'SWIPER_TOKEN'

This also now requires a Youtube API key as an environment variable with name 'YOUTUBE_KEY'