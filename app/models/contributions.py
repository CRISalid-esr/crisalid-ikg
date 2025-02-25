from typing import Optional, List

from pydantic import BaseModel

from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person


class Contribution(BaseModel):
    """
    Source Contribution model
    """
    rank: Optional[int] = None
    roles: Optional[List[LocContributionRole]] = []
    contributor: Person
