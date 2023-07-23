#!/usr/bin/env bash

VIRTUALENV_BIN=/home/ubuntu/virtual_env/community/bin
cd /home/ubuntu/Community
source $VIRTUALENV_BIN/activate && source $VIRTUALENV_BIN/postactivate

echo "${1-start}ing celery"
$VIRTUALENV_BIN/celery multi ${1} \
    1 \
	-A community.app \
    --pidfile=pids/celery/%N.pid \
    --hostname=celery_%i@%h \
	-l INFO \
	--logfile=logs/celery/%N.log \
    --without-gossip --without-mingle --without-heartbeat \
    -Q:1 save_discord_event \
    -c:1 1
