from typing import Optional, List

from pydantic import BaseModel


class PublicationChannel(BaseModel):
    """
    Publication Channel API model
    """
    uid: Optional[str] = None

    titles: List[str] = []

    acronym: List[str] = []
