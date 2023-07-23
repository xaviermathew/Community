#!/usr/bin/env bash

VIRTUALENV_BIN=/home/ubuntu/virtual_env/community/bin
cd /home/ubuntu/Community
source $VIRTUALENV_BIN/activate && source $VIRTUALENV_BIN/postactivate

echo "${1-start}ing discord listener"
$VIRTUALENV_BIN/python -m community.commands.discord_listener $1
