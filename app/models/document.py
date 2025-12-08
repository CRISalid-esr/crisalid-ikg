import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, model_validator

from app.models.concepts import Concept
from app.models.contributions import Contribution
from app.models.document_publication_channel import DocumentPublicationChannel
from app.models.literal import Literal
from app.models.open_access_status import OpenAccessStatus
from app.utils.date.partial_iso_8601 import partial_iso8601_interval


class Document(BaseModel):
    """
    Document model
    """

    uid: Optional[str] = None
    titles: List[Literal] = []
    abstracts: List[Literal] = []
    subjects: List[Concept] = []
    to_be_recomputed: bool = False
    to_be_deleted: bool = False
    to_be_merged_into_uid: Optional[str] = None
    source_record_uids: Optional[List[str]] = None
    contributions: Optional[List[Contribution]] = []
    publication_channels: List[DocumentPublicationChannel] = []
    open_access_status: OpenAccessStatus = OpenAccessStatus()
    type: str = "Document"

    _publication_date: Optional[str] = None
    _publication_date_start: Optional[datetime] = None
    _publication_date_end: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        """
        Automatically generate a UID for the Document if it is not provided
        """
        if "uid" not in values or not values["uid"]:
            values["uid"] = str(uuid.uuid4())
        return values

    @property
    def publication_date(self) -> Optional[str]:
        """
        Get the publication date as a string
        :return:  publication_date as a string
        """
        return self._publication_date

    @publication_date.setter
    def publication_date(self, value: Optional[str]):
        """
        When setting publication_date, store values internally but do not directly
        set publication_date_start and publication_date_end.
        """
        self._publication_date = value
        self._publication_date_start = None
        self._publication_date_end = None

    def compute_publication_dates(self):
        """
        Compute publication_date_start and publication_date_end from publication_date when needed.
        """
        if self._publication_date:
            self._publication_date_start, self._publication_date_end = partial_iso8601_interval(
                self._publication_date)

    @property
    def publication_date_start(self) -> Optional[datetime]:
        """
        Get the start of the publication date interval
        :return:  publication_date_start
        """
        if self._publication_date_start is None:
            self.compute_publication_dates()
        return self._publication_date_start

    @property
    def publication_date_end(self) -> Optional[datetime]:
        """
        Get the end of the publication date interval
        :return:  publication_date_end
        """
        if self._publication_date_end is None:
            self.compute_publication_dates()
        return self._publication_date_end
