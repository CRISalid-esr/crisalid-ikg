from pydantic import BaseModel

from app.models.publication_channel import PublicationChannel


class DocumentPublicationChannel(BaseModel):
    """
    Model for the relationship between a document and its publication channel (typically a journal).
    """
    pages: str = ""
    volume: str = ""
    issue: str = ""
    publication_channel: PublicationChannel
