from typing import Optional, List

from pydantic import BaseModel

from app.models.source_journal import SourceJournal


class SourceIssue(BaseModel):
    """
    Source Journal Issue API model
    """
    uid: Optional[str] = None

    source_identifier: str

    source: str

    titles: List[str] = []

    volume: Optional[str] = None

    number: List[str] = []

    rights: Optional[str] = None

    date: Optional[str] = None

    journal: SourceJournal
