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
