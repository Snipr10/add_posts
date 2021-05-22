import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'add_posts.settings')

import django

django.setup()

app = Celery('add_posts', include=['add_posts.tasks'])
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'start_parsing_url': {
    #     'task': 'add_posts.tasks.start_parsing_url',
    #     'schedule': crontab(
    #         minute='*/3')
    # },
    # 'update_proxy': {
    #     'task': 'add_posts.tasks.update_proxy',
    #     'schedule': crontab(
    #         minute='*/2')
    # },
    # 'delete_bad_worker_credentials': {
    #     'task': 'add_posts.tasks.delete_bad_worker_credentials',
    #     'schedule': crontab(
    #         minute='*/1')
    # },
    'check_not_available_accounts': {
        'task': 'add_posts.tasks.check_not_available_accounts',
        'schedule': crontab(
            minute='*/2')
    }


}
