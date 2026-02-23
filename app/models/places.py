"""
Place
"""
from typing import Optional

from pydantic import BaseModel


class Place(BaseModel):
    """
    CERIF-compliant structured physical address with multilingual support.
    """
    latitude: Optional[float] = None
    longitude: Optional[float] = None
