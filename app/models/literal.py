"""
Person model
"""
from typing import Optional

from pydantic import BaseModel


class Literal(BaseModel):
    """
    Literal API model (equivalent to RDF literal)
    """

    value: str
    language: Optional[str] = None
