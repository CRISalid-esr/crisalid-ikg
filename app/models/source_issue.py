from typing import Optional, List

from app.models.source_journal import SourceJournal
from app.models.sourced_model import SourcedModel


class SourceIssue(SourcedModel):
    """
    Source Journal Issue API model
    """
    uid: Optional[str] = None

    source_identifier: str

    titles: List[str] = []

    volume: Optional[str] = None

    number: Optional[List[str]] = []

    rights: Optional[str] = None

    date: Optional[str] = None

    journal: SourceJournal
