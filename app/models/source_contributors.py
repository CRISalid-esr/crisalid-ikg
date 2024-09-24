from typing import Optional

from pydantic import BaseModel


class SourceContributor(BaseModel):
    """
    Source Contributor model
    """
    name: str
    affiliation: Optional[str] = None
