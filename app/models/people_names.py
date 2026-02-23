"""
Person model
"""
from typing import List

from pydantic import BaseModel

from app.models.literal import Literal


class PersonName(BaseModel):
    """
    Person name API model
    """

    first_names: List[Literal] = []
    last_names: List[Literal] = []

    other_names: List[Literal] = []
