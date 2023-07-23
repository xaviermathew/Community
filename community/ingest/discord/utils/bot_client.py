import datetime
import logging
import os
import psutil
import signal

import discord

from community.app import settings

_LOG = logging.getLogger(__name__)


class BotClient(discord.Client):
    PID_FILE = settings.PID_DIR + 'discord_listener/current.pid'

    @classmethod
    def save_event(cls, event_name, d):
        from community.ingest.discord.models import DiscordEvent
        from community.ingest.discord.utils.scraper.module.utils import parse_timestamp

        user_id = d.get('user_id') or d.get('user', {}).get('id') or d.get('author', {}).get('id')
        timestamp = parse_timestamp(d['timestamp']) if 'timestamp' in d else datetime.datetime.now()
        DiscordEvent.get_or_create(event=event_name,
                                   timestamp=timestamp,
                                   user_id=user_id,
                                   data=d)

    async def on_socket_response(self, data):
        from community.ingest.discord.tasks import save_discord_event

        event_name = data['t']
        d = data['d']
        _LOG.debug('-' * 30)
        _LOG.debug('%s - %s', event_name, d)
        if event_name and d:
            save_discord_event.apply_async(kwargs={'event_name': event_name, 'd': d},
                                           queue=settings.CELERY_TASK_QUEUE_SAVE_DISCORD_EVENT,
                                           routing_key=settings.CELERY_TASK_ROUTING_KEY_SAVE_DISCORD_EVENT)

    @classmethod
    def kill_previous(cls):
        if os.path.exists(cls.PID_FILE):
            _LOG.info('current.pid file exists')
            pid = open(cls.PID_FILE).read()
            if not pid:
                _LOG.info('current.pid is empty. nothing to do')
                return

            pid = int(pid)
            try:
                old = psutil.Process(pid)
            except psutil.NoSuchProcess:
                _LOG.info('current.pid has invalid pid. removing...')
                os.remove(cls.PID_FILE)
            else:
                if old.name() == 'Python':
                    _LOG.info('current.pid belongs to previous run. killing...')
                    old.kill()
                    old.wait()
                    _LOG.info('current.pid killed')

    async def on_ready(self):
        _LOG.info('Connected as Username:%s (ID:%s)', self.user.name, self.user.id)
        self.kill_previous()
        pid = str(os.getpid())
        _LOG.info('write pid:[%s] to current.pid', pid)
        open(self.PID_FILE, 'w').write(pid)
        signal.signal(signal.SIGINT, BotClient.shutdown)

    @classmethod
    def shutdown(cls, signum, frame):
        _LOG.info('killing self...')
        if int(open(cls.PID_FILE).read()) == os.getpid():
            _LOG.info('cleaning up current.pid')
            os.remove(cls.PID_FILE)
        psutil.Process().kill()
