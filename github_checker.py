# Practice_Celery/github_checker.py
import os
import subprocess
from celery import shared_task

REPO_DIR = "/home/balaji/Project_Celery/Practice_Celery_Repo/Test_folder"  # change to your target dir
REPO_URL = "https://github.com/sq1balaji/Practice_Celery.git"

@shared_task
def check_for_new_commit():
    if not os.path.exists(REPO_DIR):
        # Clone the repo if it doesn't exist
        subprocess.run(["git", "clone", REPO_URL, REPO_DIR], check=True)
        print("✅ Repository cloned")
    else:
        # Pull the latest changes
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)
        print("🔁 Repository updated")
