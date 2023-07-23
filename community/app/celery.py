from __future__ import absolute_import

from celery import Celery

from community.app import settings

app = Celery('community')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
#
# but getting "RecursionError: maximum recursion depth exceeded while calling a Python object"
# when i do that, so use the object directly
app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
