import calendar
import re
from datetime import datetime
from typing import Optional, Tuple

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

    date_str = re.split(r"[ T]", date_str.strip())[0]  # Remove time component if present
    date_str = date_str.rstrip("-")  # Remove trailing dashes

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


def partial_iso8601_interval(date: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parses a partial ISO 8601 date string and returns a start and end date.
    :param date: a string representing a date in one of the following formats:
    :return: a tuple of two datetime objects representing the start and end date of the interval
    """
    parsed_date = parse_partial_iso8601(date)
    if not parsed_date:
        return None, None

    try:
        if len(parsed_date) == 4:  # YYYY
            start_date = datetime(int(parsed_date), 1, 1)
            end_date = datetime(int(parsed_date), 12, 31, 23, 59, 59)
        elif len(parsed_date) == 7:  # YYYY-MM
            year, month = map(int, parsed_date.split("-"))
            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day, 23, 59, 59)

        elif len(parsed_date) == 10:  # YYYY-MM-DD
            start_date = datetime.strptime(parsed_date, "%Y-%m-%d")
            end_date = start_date.replace(hour=23, minute=59, second=59)
        else:
            return None, None

        return start_date, end_date
    except ValueError:
        logger.error(f"Invalid parsed date: {parsed_date}")
        return None, None
