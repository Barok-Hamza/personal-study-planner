from datetime import date, datetime, time, timedelta


def calculate_end_time(
    scheduled_date: date, start_time: time, duration_minutes: int
) -> datetime:
    start = datetime.combine(scheduled_date, start_time)
    return start + timedelta(minutes=duration_minutes)
