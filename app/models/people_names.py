"""
Person model
"""
from typing import List

from pydantic import BaseModel


class PersonName(BaseModel):
    """
    Person name API object
    """

    first_names: List[str] = []
    family_names: List[str] = []

    other_names: List[str] = []
