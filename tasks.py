import logging
import subprocess
from celery import shared_task
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)
REPO_PATH = "/home/balaji/Project_Celery/Test_folder/Practice_Celery"
TRAGET_JSON_PATH = "/home/balaji/Project_Celery/"
JSON_LOG_PATH = os.path.join(TRAGET_JSON_PATH, "pull_log.json")

@shared_task
def pull_repo():
    logger.info("Starting git pull task")

    # Get old HEAD before pull
    try:
        old_head = subprocess.check_output(
            ["git", "-C", REPO_PATH, "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting old HEAD: {e}")
        return

    # Run git pull
    try:
        result = subprocess.run(
            ["git", "-C", REPO_PATH, "pull"],
            capture_output=True, text=True, check=True
        )
        pull_output = result.stdout.strip()
        logger.info(f"Git pull output: {pull_output}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git pull failed: {e}")
        return

    # Skip logging if repo is up to date
    if "Already up to date." in pull_output or "Already up-to-date." in pull_output:
        logger.info("Repo already up to date. Skipping log.")
        return

    # Get new HEAD after pull
    try:
        new_head = subprocess.check_output(
            ["git", "-C", REPO_PATH, "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting new HEAD: {e}")
        return

    # Get commits between old and new HEAD
    try:
        commit_list = subprocess.check_output(
            ["git", "-C", REPO_PATH, "rev-list", f"{old_head}..{new_head}"],
            text=True
        ).strip().splitlines()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting commit list: {e}")
        return

    logs = []

    for commit_hash in commit_list:
        try:
            # Get basic commit info
            raw_info = subprocess.check_output(
                ["git", "-C", REPO_PATH, "show", "--no-patch", "--format=%H%n%an%n%ae%n%aI%n%s", commit_hash],
                text=True
            ).strip().splitlines()

            commit_info = {
                "commit_hash": raw_info[0],
                "author": raw_info[1],
                "email": raw_info[2],
                "date": raw_info[3],
                "message": raw_info[4],
                "added_files": [],
                "deleted_files": [],
                "modified_files": [],
                "file_changes": {}
            }

            # Get diff details with line numbers
            diff_output = subprocess.check_output(
            ["git", "-C", REPO_PATH, "show", "--format=", "--unified=0", commit_hash],
            text=True
            )

            current_file = None
            change_type = None
            inserted = []
            deleted = []
            new_line_num = None
            old_line_num = None

            for line in diff_output.splitlines():
                if line.startswith("diff --git"):
                    if current_file:
                        commit_info["file_changes"][current_file] = {
                            "change_type": change_type,
                            "inserted_lines": inserted,
                            "deleted_lines": deleted
                        }
                        if change_type == "added":
                            commit_info["added_files"].append(current_file)
                        elif change_type == "deleted":
                            commit_info["deleted_files"].append(current_file)
                        elif change_type == "modified":
                            commit_info["modified_files"].append(current_file)

                # Reset state
                    current_file = None
                    inserted = []
                    deleted = []
                    change_type = None
                elif line.startswith("+++ b/"):
                    current_file = line[6:]
                elif line.startswith("--- a/"):
                    pass
                elif line.startswith("new file mode"):
                    change_type = "added"
                elif line.startswith("deleted file mode"):
                    change_type = "deleted"
                elif line.startswith("@@"):
                    # Example: @@ -1,2 +1,3 @@
                    import re
                    match = re.match(r"@@ -(\d+),?\d* \+(\d+),?\d* @@", line)
                    if match:
                        old_line_num = int(match.group(1))
                        new_line_num = int(match.group(2))
                elif line.startswith("+") and not line.startswith("+++"):
                    inserted.append({
                        "line_number": new_line_num,
                        "content": line[1:]
                    })
                    new_line_num += 1
                    if change_type != "added":
                        change_type = "modified"
                elif line.startswith("-") and not line.startswith("---"):
                    deleted.append({
                        "line_number": old_line_num,
                        "content": line[1:]
                    })
                    old_line_num += 1
                    if change_type != "deleted":
                        change_type = "modified"

            # Handle last file
            if current_file:
                commit_info["file_changes"][current_file] = {
                    "change_type": change_type,
                    "inserted_lines": inserted,
                    "deleted_lines": deleted
            }
            if change_type == "added":
                commit_info["added_files"].append(current_file)
            elif change_type == "deleted":
                commit_info["deleted_files"].append(current_file)
            elif change_type == "modified":
                commit_info["modified_files"].append(current_file)


                commit_info["file_changes"][current_file] = {
                    "change_type": change_type,
                    "inserted_lines": inserted,
                    "deleted_lines": deleted
                }

            logs.append(commit_info)

        except subprocess.CalledProcessError as e:
            logger.error(f"Error processing commit {commit_hash}: {e}")
            continue

    # Append to JSON log
    if os.path.exists(JSON_LOG_PATH):
        try:
            with open(JSON_LOG_PATH, "r") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    else:
        existing = []

    all_logs = existing + logs

    try:
        with open(JSON_LOG_PATH, "w") as f:
            json.dump(all_logs, f, indent=4)
        logger.info(f"Saved detailed log to {JSON_LOG_PATH}")
    except Exception as e:
        logger.error(f"Failed to write log file: {e}")
