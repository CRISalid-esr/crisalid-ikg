from typing import Optional, List

from pydantic import BaseModel

from app.models.literal import Literal
from app.models.source_journal import SourceJournal


class SourceIssue(BaseModel):
    """
    Source Review Issue API model
    """
    uid: Optional[str] = None

    source_identifier: str

    source: str

    titles: List[Literal] = []

    volume: Optional[str] = None

    number: List[str] = []

    rights: Optional[str] = None

    date: Optional[str] = None

    journal: SourceJournal
