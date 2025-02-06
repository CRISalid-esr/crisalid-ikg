import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, model_validator

from app.models.concepts import Concept
from app.models.contributions import Contribution
from app.models.literal import Literal
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

    publicationDate: Optional[str] = None
    publicationDateStart: Optional[datetime] = None
    publicationDateEnd: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        """
        Automatically generate a UID for the Document if it is not provided
        """
        if "uid" not in values or not values["uid"]:
            values["uid"] = str(uuid.uuid4())
        return values

    @model_validator(mode="before")
    @classmethod
    def _compute_publication_dates(cls, values):
        """
        Compute publicationDateStart and publicationDateEnd from publicationDate
        """
        publication_date = values.get("publicationDate")
        if publication_date:
            start, end = partial_iso8601_interval(publication_date)
            values["publicationDateStart"] = start
            values["publicationDateEnd"] = end
        return values
