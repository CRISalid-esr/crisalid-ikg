from typing import Optional

from pydantic import BaseModel

from app.models.source_contributors import SourceContributor


class SourceContribution(BaseModel):
    """
    Source Contribution model
    """
    rank: Optional[int] = None
    contributor: SourceContributor
