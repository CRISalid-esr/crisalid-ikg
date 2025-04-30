from dataclasses import dataclass
from typing import Optional, List


@dataclass
class IssnInfo:
    """
    Simple data container for ISSN-related information.
    """
    checked_issn: str
    issn_l: Optional[str] = None
    related_issns: Optional[List[str]] = None
    title: Optional[str] = None
    publisher: Optional[str] = None
    urls: Optional[List[str]] = None
    errors: Optional[List[str]] = None
