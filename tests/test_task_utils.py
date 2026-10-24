import unittest
from datetime import date, datetime, time

from task_utils import calculate_end_time


class CalculateEndTimeTests(unittest.TestCase):
    def test_same_day_calculation(self):
        end = calculate_end_time(date(2026, 10, 24), time(16, 0), 30)

        self.assertEqual(end, datetime(2026, 10, 24, 16, 30))

    def test_midnight_rollover(self):
        end = calculate_end_time(date(2026, 10, 24), time(23, 30), 90)

        self.assertEqual(end, datetime(2026, 10, 25, 1, 0))


if __name__ == "__main__":
    unittest.main()
