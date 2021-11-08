#!/bin/bash
nohup poetry run python3.8 $SWIPER_HOME/src/main.py &
echo $! > $SWIPER_HOME/scripts/save_pid.txt
