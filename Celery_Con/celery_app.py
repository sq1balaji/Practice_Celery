from celery import Celery
from celery.schedules import crontab

app = Celery(
    "github_tasks",
    broker="redis://localhost:6380/0",
    backend="redis://localhost:6380/0",
    include=["Practice_Celery.tasks"],
)

app.conf.beat_schedule = {
    "git-pull-every-minute": {
        "task": "Practice_Celery.tasks.pull_repo",
        "schedule": crontab(minute="*/1"),  # every minute
    },
}

app.conf.timezone = "Asia/Kolkata"
