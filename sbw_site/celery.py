import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sbw_site.settings')

app = Celery('sbw_site')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'run-user-movement-every-hour': {
        'task': 'socket_app.tasks.run_user_movement_periodically',
        'schedule': crontab(minute=0, hour='*'),
    },
}
