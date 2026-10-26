import unittest
from datetime import date, datetime, time

from task_utils import (
    calculate_end_time,
    calculate_progress,
    find_conflicting_task,
    update_task,
)


class CalculateEndTimeTests(unittest.TestCase):
    def test_same_day_calculation(self):
        end = calculate_end_time(date(2026, 10, 24), time(16, 0), 30)

        self.assertEqual(end, datetime(2026, 10, 24, 16, 30))

    def test_midnight_rollover(self):
        end = calculate_end_time(date(2026, 10, 24), time(23, 30), 90)

        self.assertEqual(end, datetime(2026, 10, 25, 1, 0))


class TaskEditStatusTests(unittest.TestCase):
    def setUp(self):
        self.task = {
            "id": "existing-task-id",
            "name": "Original name",
            "start": datetime(2026, 10, 24, 16, 0),
            "end": datetime(2026, 10, 24, 16, 30),
            "duration": 30,
            "status": "Completed",
        }

    def test_name_only_edit_preserves_completed_status(self):
        update_task(
            self.task,
            "Updated name",
            date(2026, 10, 24),
            time(16, 0),
            30,
        )

        self.assertEqual(self.task["name"], "Updated name")
        self.assertEqual(self.task["status"], "Completed")

    def test_schedule_change_resets_completed_status(self):
        update_task(
            self.task,
            "Original name",
            date(2026, 10, 24),
            time(17, 0),
            30,
        )

        self.assertEqual(self.task["status"], "Pending")
        self.assertEqual(self.task["start"], datetime(2026, 10, 24, 17, 0))
        self.assertEqual(self.task["end"], datetime(2026, 10, 24, 17, 30))

    def test_date_change_resets_completed_and_recalculates_dates(self):
        update_task(
            self.task,
            "Original name",
            date(2026, 10, 25),
            time(16, 0),
            30,
        )

        self.assertEqual(self.task["status"], "Pending")
        self.assertEqual(self.task["start"], datetime(2026, 10, 25, 16, 0))
        self.assertEqual(self.task["end"], datetime(2026, 10, 25, 16, 30))

    def test_duration_change_resets_completed_and_updates_end_time(self):
        update_task(
            self.task,
            "Original name",
            date(2026, 10, 24),
            time(16, 0),
            45,
        )

        self.assertEqual(self.task["status"], "Pending")
        self.assertEqual(self.task["start"], datetime(2026, 10, 24, 16, 0))
        self.assertEqual(self.task["end"], datetime(2026, 10, 24, 16, 45))

    def test_editing_pending_task_keeps_it_pending(self):
        self.task["status"] = "Pending"

        update_task(
            self.task,
            "Updated name",
            date(2026, 10, 25),
            time(17, 0),
            45,
        )

        self.assertEqual(self.task["status"], "Pending")

    def test_edit_does_not_change_task_id(self):
        task_id = self.task["id"]
        update_task(
            self.task,
            "Updated name",
            date(2026, 10, 24),
            time(17, 0),
            45,
        )

        self.assertEqual(self.task["id"], task_id)


class FindConflictingTaskTests(unittest.TestCase):
    def setUp(self):
        self.task = {
            "id": "existing-task-id",
            "name": "Existing task",
            "start": datetime(2026, 10, 24, 16, 0),
            "end": datetime(2026, 10, 24, 16, 30),
            "duration": 30,
            "status": "Completed",
        }

    def test_overlapping_schedule_returns_conflicting_task(self):
        conflict = find_conflicting_task(
            [self.task],
            datetime(2026, 10, 24, 16, 15),
            datetime(2026, 10, 24, 16, 45),
        )

        self.assertIs(conflict, self.task)

    def test_back_to_back_schedule_is_allowed(self):
        conflict = find_conflicting_task(
            [self.task],
            datetime(2026, 10, 24, 16, 30),
            datetime(2026, 10, 24, 17, 0),
        )

        self.assertIsNone(conflict)

    def test_overnight_overlap_is_detected(self):
        overnight_task = {
            "id": "overnight-task-id",
            "name": "Overnight task",
            "start": datetime(2026, 10, 24, 23, 30),
            "end": datetime(2026, 10, 25, 1, 0),
            "duration": 90,
            "status": "Pending",
        }

        conflict = find_conflicting_task(
            [overnight_task],
            datetime(2026, 10, 25, 0, 30),
            datetime(2026, 10, 25, 1, 30),
        )

        self.assertIs(conflict, overnight_task)

    def test_non_overlapping_dates_do_not_conflict(self):
        conflict = find_conflicting_task(
            [self.task],
            datetime(2026, 10, 25, 16, 0),
            datetime(2026, 10, 25, 16, 30),
        )

        self.assertIsNone(conflict)

    def test_can_exclude_task_being_edited(self):
        conflict = find_conflicting_task(
            [self.task],
            self.task["start"],
            self.task["end"],
            exclude_task_id=self.task["id"],
        )

        self.assertIsNone(conflict)

    def test_completed_task_still_conflicts(self):
        conflict = find_conflicting_task(
            [self.task],
            datetime(2026, 10, 24, 16, 10),
            datetime(2026, 10, 24, 16, 20),
        )

        self.assertIs(conflict, self.task)


class CalculateProgressTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 25, 12, 0)
        self.tasks = [
            {
                "id": "pending-overdue",
                "name": "Overdue pending task",
                "start": datetime(2026, 10, 25, 9, 0),
                "end": datetime(2026, 10, 25, 10, 0),
                "duration": 60,
                "status": "Pending",
            },
            {
                "id": "pending-current",
                "name": "Current pending task",
                "start": datetime(2026, 10, 25, 12, 0),
                "end": datetime(2026, 10, 25, 13, 0),
                "duration": 60,
                "status": "Pending",
            },
            {
                "id": "completed-past",
                "name": "Completed task",
                "start": datetime(2026, 10, 24, 9, 0),
                "end": datetime(2026, 10, 24, 10, 0),
                "duration": 60,
                "status": "Completed",
            },
        ]

    def test_empty_task_list_returns_zero_counts_and_percentage(self):
        progress = calculate_progress([], self.now)

        self.assertEqual(
            progress,
            {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "overdue": 0,
                "completion_percentage": 0,
            },
        )

    def test_total_completed_and_pending_counts(self):
        progress = calculate_progress(self.tasks, self.now)

        self.assertEqual(progress["total"], 3)
        self.assertEqual(progress["completed"], 1)
        self.assertEqual(progress["pending"], 2)

    def test_overdue_counts_only_pending_tasks_ending_before_now(self):
        progress = calculate_progress(self.tasks, self.now)

        self.assertEqual(progress["overdue"], 1)

    def test_completed_task_with_past_end_is_not_overdue(self):
        completed_task = self.tasks[2]

        progress = calculate_progress([completed_task], self.now)

        self.assertEqual(progress["overdue"], 0)

    def test_task_ending_exactly_now_is_not_overdue(self):
        task_ending_now = {
            "id": "ends-now",
            "name": "Task ending now",
            "start": datetime(2026, 10, 25, 11, 0),
            "end": self.now,
            "duration": 60,
            "status": "Pending",
        }

        progress = calculate_progress([task_ending_now], self.now)

        self.assertEqual(progress["overdue"], 0)

    def test_completion_percentage(self):
        progress = calculate_progress(self.tasks, self.now)

        self.assertAlmostEqual(progress["completion_percentage"], 100 / 3)


if __name__ == "__main__":
    unittest.main()
