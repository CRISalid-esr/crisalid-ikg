"""
Person model
"""
from typing import List, Optional

from app.models.literal import Literal
from app.models.organizations import Organization


class ResearchStructure(Organization):
    """
    Research structure API model
    """

    acronym : Optional[str] = None
    descriptions : List[Literal] = []
