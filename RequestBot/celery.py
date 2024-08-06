import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RequestBot.settings')

app = Celery('RequestBot')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'check-message': {
        'task': 'bot.tasks.send_scheduled_messages',
        'schedule': 30.0,
    },
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
app.conf.enable_utc = False
