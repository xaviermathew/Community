import logging
import os
import warnings

from dotenv import load_dotenv
from kombu import Exchange, Queue

# env
# assumes that local has both files but prod only has prod.env
if os.path.exists('.env'):
    load_dotenv('.env')
else:
    load_dotenv('prod.env')


# misc
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s:%(levelname)s:%(filename)s:%(lineno)d:%(funcName)s():%(message)s'


# community
INSTALLED_APPS = (
    'community.app',
    'community.ingest',
    'community.platform',
)
PID_DIR = 'pids/'


# infra
DATABASE_URL = os.getenv('DATABASE_URL')
DJANGO_DATABASE_URL = os.getenv('DJANGO_DATABASE_URL')
RAINMAN_DATABASE_URL = os.getenv('RAINMAN_DATABASE_URL')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_DB = int(os.getenv('REDIS_DB', 0))

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')

AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# 3rd party credentials
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_SECRET_KEY = os.getenv('TWITTER_SECRET_KEY')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

DISCORD_BEARER_TOKEN = os.getenv('DISCORD_BEARER_TOKEN')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')


# celery
# https://www.cloudamqp.com/docs/celery.html
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_BROKER_POOL_LIMIT = 1  # Will decrease connection usage
CELERY_BROKER_HEARTBEAT = None  # We're using TCP keep-alive instead
CELERY_BROKER_CONNECTION_TIMEOUT = 30  # May require a long timeout due to Linux DNS timeouts etc
CELERY_RESULT_BACKEND = None  # AMQP is not recommended as result backend as it creates thousands of queues
CELERY_EVENT_QUEUE_EXPIRES = 60  # Will delete all celeryev. queues without consumers after 1 minute.
# CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Disable prefetching, it's causes problems and doesn't help performance
CELERY_IGNORE_RESULT = True

CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle']

CELERY_TASK_QUEUE_SAVE_DISCORD_EVENT = 'save_discord_event'
CELERY_TASK_ROUTING_KEY_SAVE_DISCORD_EVENT = 'save_discord_event'

CELERY_TASK_QUEUES = (
    Queue(name=CELERY_TASK_QUEUE_SAVE_DISCORD_EVENT,
          exchange=Exchange(CELERY_TASK_QUEUE_SAVE_DISCORD_EVENT),
          routing_key=CELERY_TASK_ROUTING_KEY_SAVE_DISCORD_EVENT),
)


# django
ALLOWED_HOSTS = []


# assumes that local has both files but prod only has production.py
try:
    from . import local
except ImportError:
    try:
        from . import production
    except ImportError:
        warnings.warn('local.py/production.py is missing')
    else:
        from .production import *
else:
    from .local import *


logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
