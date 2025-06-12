# Celery_Con/beat_scheduler.py

from celery.schedules import crontab

beat_schedule = {
    'say-hello-every-10-seconds': {
        'task': 'Practice_Celery.tasks.print_message',  # Full path to your task
        'schedule': 10.0,  # every 10 seconds
        'args': ()
    },
}
