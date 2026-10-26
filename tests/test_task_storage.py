import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from task_storage import load_tasks, save_tasks


class TaskStorageTests(unittest.TestCase):
    def setUp(self):
        self.task = {
            "id": "task-123",
            "name": "Study Python",
            "start": datetime(2026, 10, 25, 23, 30),
            "end": datetime(2026, 10, 26, 1, 0),
            "duration": 90,
            "status": "Completed",
        }
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "tasks.json"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_serialization_and_restoration_preserve_all_fields(self):
        save_tasks([self.task], self.path)

        saved_data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved_data[0]["start"], "2026-10-25T23:30:00")
        self.assertEqual(saved_data[0]["end"], "2026-10-26T01:00:00")
        self.assertEqual(load_tasks(self.path), [self.task])

    def test_save_and_load_use_the_given_file(self):
        save_tasks([self.task], self.path)

        self.assertTrue(self.path.exists())
        self.assertEqual(load_tasks(self.path), [self.task])

    def test_missing_file_loads_empty_list(self):
        self.assertEqual(load_tasks(self.path), [])

    def test_empty_file_loads_empty_list(self):
        self.path.write_text(" \n", encoding="utf-8")

        self.assertEqual(load_tasks(self.path), [])

    def test_malformed_json_raises_clear_error(self):
        self.path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "malformed JSON"):
            load_tasks(self.path)

    def test_invalid_task_data_raises_clear_error(self):
        self.path.write_text(
            json.dumps(
                [
                    {
                        "id": "task-123",
                        "name": "Study Python",
                        "start": "not-a-datetime",
                        "end": "2026-10-26T01:00:00",
                        "duration": 90,
                        "status": "Completed",
                    }
                ]
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Invalid task datetime"):
            load_tasks(self.path)

    def test_task_missing_required_fields_raises_clear_error(self):
        self.path.write_text(json.dumps([{"id": "task-123"}]), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "required task fields"):
            load_tasks(self.path)

    def test_inconsistent_duration_is_rejected_when_loading(self):
        inconsistent_task = dict(self.task, end=datetime(2026, 10, 26, 1, 1))
        self.path.write_text(
            json.dumps(
                [
                    {
                        **inconsistent_task,
                        "start": inconsistent_task["start"].isoformat(),
                        "end": inconsistent_task["end"].isoformat(),
                    }
                ]
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "end datetime must match"):
            load_tasks(self.path)

    def test_inconsistent_duration_is_rejected_when_saving(self):
        inconsistent_task = dict(self.task, end=datetime(2026, 10, 26, 1, 1))

        with self.assertRaisesRegex(ValueError, "end datetime must match"):
            save_tasks([inconsistent_task], self.path)

        self.assertFalse(self.path.exists())

    def test_duplicate_task_ids_are_rejected_when_loading(self):
        saveable_task = dict(self.task)
        duplicate_task = dict(self.task, name="Second task")
        task_data = [
            {
                **task,
                "start": task["start"].isoformat(),
                "end": task["end"].isoformat(),
            }
            for task in (saveable_task, duplicate_task)
        ]
        self.path.write_text(json.dumps(task_data), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "IDs must be unique"):
            load_tasks(self.path)

    def test_duplicate_task_ids_are_rejected_when_saving(self):
        duplicate_task = dict(self.task, name="Second task")

        with self.assertRaisesRegex(ValueError, "IDs must be unique"):
            save_tasks([self.task, duplicate_task], self.path)

        self.assertFalse(self.path.exists())

    def test_failed_atomic_replace_preserves_existing_file(self):
        save_tasks([self.task], self.path)
        original_contents = self.path.read_text(encoding="utf-8")
        changed_task = dict(self.task, name="Changed")

        with patch("task_storage.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaisesRegex(OSError, "replace failed"):
                save_tasks([changed_task], self.path)

        self.assertEqual(
            self.path.read_text(encoding="utf-8"), original_contents
        )

    def test_non_json_task_field_fails_before_replacing_existing_file(self):
        save_tasks([self.task], self.path)
        original_contents = self.path.read_text(encoding="utf-8")
        task_with_extra_field = dict(self.task, extra_field=object())

        with self.assertRaisesRegex(ValueError, "cannot be saved as JSON"):
            save_tasks([task_with_extra_field], self.path)

        self.assertEqual(
            self.path.read_text(encoding="utf-8"), original_contents
        )


if __name__ == "__main__":
    unittest.main()
