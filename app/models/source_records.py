from typing import Optional, List

from pydantic import BaseModel

from app.models.document_type import DocumentType
from app.models.literal import Literal
from app.models.publication_identifiers import PublicationIdentifier
from app.models.source_contributions import SourceContribution
from app.models.subjects import Subject


class SourceRecord(BaseModel):
    """
    Source Bibliographic Record API model
    (store raw references received from external sources before deduplication)
    """

    id: Optional[str] = None  # id from the database if exists

    source_identifier: str

    harvester: str

    titles: List[Literal]

    identifiers: List[PublicationIdentifier] = []

    abstracts: List[Literal] = []

    subjects: List[Subject] = []

    document_type: List[DocumentType] = []

    contributions: List[SourceContribution] = []
