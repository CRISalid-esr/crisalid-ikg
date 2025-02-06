import re
from datetime import datetime
from typing import Optional

from loguru import logger


def parse_partial_iso8601(date_str: str) -> Optional[str]:
    """
    Parses a raw_issued string and returns a valid date in one of three formats:
    - YYYY
    - YYYY-MM
    - YYYY-MM-DD
    Trailing dashed are removed (YYYY- -> YYYY, YYYY-MM- -> YYYY-MM)
    @param date_str: a string representing a date in one of the above formats
    @return: a string representing a valid date in one of the above formats or
    None if the input string is not a valid date
    """
    if not isinstance(date_str, str) or not date_str.strip():
        return None

    date_str = date_str.strip().rstrip("-")

    # YYYY, YYYY-MM, YYYY-MM-DD
    match = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$", date_str)
    if match:
        year, month, day = match.groups()
        try:
            if year and month and day:
                dt = datetime(int(year), int(month), int(day))
                return dt.strftime("%Y-%m-%d")
            if year and month:
                dt = datetime(int(year), int(month), 1)  # Check if valid month
                return dt.strftime("%Y-%m")
            if year:
                return year
        except ValueError:  # 32nd of December, 13th month or fantasy date
            logger.error(f"Could not parse date: {date_str}")
            return None

    return None
