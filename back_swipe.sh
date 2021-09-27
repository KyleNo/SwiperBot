#!/bin/bash
nohup poetry run python3.8 main.py &
echo $! > save_pid.txt
