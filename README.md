# SwiperBot
A simple music bot written in Python.

This bot currently only supports minimal functionality:

The play command adds a song to the queue and begins playing.
alias: !p
usage: !play <Youtube video title or url>

The skip command stops the song that is currently playing and continues to next song in queue.
alias: !s
usage: !skip

The clear command ends the current song and removes all songs in the queue.
alias: !c
usage !clear

The bot token should be stored in .env witht the name 'SWIPER_TOKEN'
