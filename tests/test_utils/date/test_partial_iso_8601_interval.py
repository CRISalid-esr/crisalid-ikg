from datetime import datetime

import pytest

from app.utils.date.partial_iso_8601 import partial_iso8601_interval


@pytest.mark.parametrize("date, expected_start, expected_end", [
    ("2024", datetime(2024, 1, 1), datetime(2024, 12, 31, 23, 59, 59)),
    ("2024-12", datetime(2024, 12, 1), datetime(2024, 12, 31, 23, 59, 59)),
    ("2024-12-25", datetime(2024, 12, 25), datetime(2024, 12, 25, 23, 59, 59)),
    ("2024-12-16 00:00:00", datetime(2024, 12, 16), datetime(2024, 12, 16, 23, 59, 59)),
    ("2024-16-12", None, None),  # Invalid month
    ("2024-12-32", None, None),  # Invalid day
    ("abcd", None, None),  # Invalid input
    ("", None, None),  # Empty string
    (None, None, None)  # None input
])
def test_partial_iso8601_interval(date, expected_start, expected_end):
    """
    Test that partial_iso8601_interval correctly processes different date formats.
    """
    start, end = partial_iso8601_interval(date)
    assert start == expected_start
    assert end == expected_end
