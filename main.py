# main.py
from fastapi import FastAPI
from Practice_Celery.tasks import pull_repo

app = FastAPI()

@app.get("/")
def root():
    return {"message": "GitHub repo monitor is running"}

@app.get("/trigger-pull/")
def trigger_git_pull():
    pull_repo()
    return {"status": "Git pull task triggered"}
