from datetime import date, datetime, time, timedelta
from typing import TypedDict


class Task(TypedDict):
    id: str
    name: str
    start: datetime
    end: datetime
    duration: int
    status: str


def calculate_end_time(
    scheduled_date: date, start_time: time, duration_minutes: int
) -> datetime:
    start = datetime.combine(scheduled_date, start_time)
    return start + timedelta(minutes=duration_minutes)


def find_conflicting_task(
    tasks: list[Task],
    candidate_start: datetime,
    candidate_end: datetime,
    exclude_task_id: str | None = None,
) -> Task | None:
    for task in tasks:
        if task["id"] == exclude_task_id:
            continue
        if candidate_start < task["end"] and task["start"] < candidate_end:
            return task
    return None


def update_task(
    task: Task,
    name: str,
    scheduled_date: date,
    start_time: time,
    duration_minutes: int,
) -> None:
    new_start = datetime.combine(scheduled_date, start_time)
    schedule_changed = (
        task["start"] != new_start or task["duration"] != duration_minutes
    )
    if task["status"] == "Completed" and schedule_changed:
        task["status"] = "Pending"

    task["name"] = name
    task["start"] = new_start
    task["end"] = calculate_end_time(
        scheduled_date, start_time, duration_minutes
    )
    task["duration"] = duration_minutes


def calculate_progress(
    tasks: list[Task], now: datetime | None = None
) -> dict[str, int | float]:
    if now is None:
        now = datetime.now()

    total_tasks = len(tasks)
    completed_tasks = sum(task["status"] == "Completed" for task in tasks)
    pending_tasks = sum(task["status"] == "Pending" for task in tasks)
    overdue_tasks = sum(
        task["status"] == "Pending" and task["end"] < now for task in tasks
    )
    completion_percentage = (
        completed_tasks / total_tasks * 100 if total_tasks else 0
    )

    return {
        "total": total_tasks,
        "completed": completed_tasks,
        "pending": pending_tasks,
        "overdue": overdue_tasks,
        "completion_percentage": completion_percentage,
    }
