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
    'start_update_content': {
        'task': 'add_posts.tasks.start_update_content',
        'schedule': crontab(
            hour='*/10')
    },
    'update_proxy': {
        'task': 'add_posts.tasks.update_proxy',
        'schedule': crontab(
            minute='*/10')
    },
    'delete_bad_worker_credentials': {
        'task': 'add_posts.tasks.delete_bad_worker_credentials',
        'schedule': crontab(
            minute='*/10')
    },
    'check_not_available_accounts': {
        'task': 'add_posts.tasks.check_not_available_accounts',
        'schedule': crontab(
            minute='*/50')
    },
    'start_parsing_url_new': {
        'task': 'add_posts.tasks.start_parsing_url_new',
        'schedule': crontab(
            hour='*/5')
    },
    # 'delete_old_proxy': {
    #     'task': 'add_posts.tasks.delete_old_proxy',
    #     'schedule': crontab(
    #         minute='*/10')
    # }


}
