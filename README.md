# SwiperBot
A simple music bot written in Python.

# Installation

1. Clone this repository

2. Install ffmeg and opus

3. Install python3.8

4. Install poetry

5. Run:

```
poetry install 
```

# Commands

This bot currently only supports minimal functionality:

## !play

The play command adds a song to the queue and begins playing.

alias: !p, !swipe

usage: !play <Youtube video title or url>
  
## !skip

The skip command stops the song that is currently playing and continues to next song in queue.

alias: !s

usage: !skip

## !clear

The clear command ends the current song and removes all songs in the queue.

alias: !c, !swipernoswiping

usage !clear

The bot token should be stored as an environment variable with the name 'SWIPER_TOKEN'
