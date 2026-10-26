import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from task_utils import Task

TASKS_FILE = Path(__file__).with_name("tasks.json")
REQUIRED_FIELDS = {"id", "name", "start", "end", "duration", "status"}


def _validate_task(task: Any) -> dict[str, Any]:
    if not isinstance(task, dict) or not REQUIRED_FIELDS.issubset(task):
        raise ValueError("Each task must contain all required task fields.")
    if not isinstance(task["id"], str) or not isinstance(task["name"], str):
        raise ValueError("Task IDs and names must be text.")
    if not task["id"].strip() or not task["name"].strip():
        raise ValueError("Task IDs and names must not be blank.")
    if not isinstance(task["start"], datetime) or not isinstance(
        task["end"], datetime
    ):
        raise ValueError("Task start and end values must be datetimes.")
    if type(task["duration"]) is not int or task["duration"] <= 0:
        raise ValueError("Task duration must be a positive integer.")
    if task["end"] != task["start"] + timedelta(minutes=task["duration"]):
        raise ValueError(
            "Task end datetime must match its start datetime and duration."
        )
    if not isinstance(task["status"], str) or task["status"] not in {
        "Pending",
        "Completed",
    }:
        raise ValueError("Task status must be Pending or Completed.")
    return task


def _task_to_json(task: Task) -> dict[str, Any]:
    saved_task = dict(_validate_task(task))
    saved_task["start"] = task["start"].isoformat()
    saved_task["end"] = task["end"].isoformat()
    return saved_task


def _task_from_json(task: Any) -> Task:
    if not isinstance(task, dict) or not REQUIRED_FIELDS.issubset(task):
        raise ValueError("Each saved task must contain all required task fields.")
    restored_task = dict(task)
    try:
        if not isinstance(restored_task["start"], str) or not isinstance(
            restored_task["end"], str
        ):
            raise ValueError("Task start and end values must be ISO datetime text.")
        restored_task["start"] = datetime.fromisoformat(restored_task["start"])
        restored_task["end"] = datetime.fromisoformat(restored_task["end"])
    except ValueError as error:
        raise ValueError(f"Invalid task datetime: {error}") from error
    return _validate_task(restored_task)


def save_tasks(tasks: list[Task], path: Path = TASKS_FILE) -> None:
    saved_tasks = [_task_to_json(task) for task in tasks]
    task_ids = [task["id"] for task in saved_tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Task IDs must be unique.")
    try:
        contents = json.dumps(saved_tasks, indent=2, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Tasks cannot be saved as JSON: {error}") from error

    temporary_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f"{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(contents)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def load_tasks(path: Path = TASKS_FILE) -> list[Task]:
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    if not contents.strip():
        return []
    try:
        data = json.loads(contents)
    except json.JSONDecodeError as error:
        raise ValueError(f"Tasks file contains malformed JSON: {error}") from error

    if not isinstance(data, list):
        raise ValueError("Tasks file must contain a JSON list.")
    tasks = [_task_from_json(task) for task in data]
    task_ids = [task["id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Saved task IDs must be unique.")
    return tasks
