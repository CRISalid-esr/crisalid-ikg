import pytest

from app.utils.date.partial_iso_8601 import parse_partial_iso8601


@pytest.mark.current
@pytest.mark.parametrize("raw_issued, expected", [
    ("2024", "2024"),
    ("2024-12", "2024-12"),
    ("2024-12-25", "2024-12-25"),
    ("2024-16-12", None),  # Invalid month
    ("2024-12-32", None),  # Invalid day
    ("2024-12-", "2024-12"),  # Edge case with trailing dash
    ("2024-", "2024"),  # Edge case with trailing dash
    ("abcd", None),  # Invalid input
    ("", None),  # Empty string
    (None, None)  # None input
])
def test_parse_partial_iso8601(raw_issued, expected):
    """
    Test that parse_partial_iso8601 correctly processes different date formats.
    """
    assert parse_partial_iso8601(raw_issued) == expected
