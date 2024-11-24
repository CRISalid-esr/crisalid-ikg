import uuid
from typing import List, Optional

from pydantic import BaseModel, model_validator

from app.models.literal import Literal


class Document(BaseModel):
    """
    Document model
    """

    uid: Optional[str] = None
    titles: Optional[List[Literal]] = None
    to_be_recomputed: bool = False
    to_be_deleted: bool = False
    to_be_merged_into_uid: Optional[str] = None
    source_record_uids: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        """
        Automatically generate a UID for the Document if it is not provided
        """
        if "uid" not in values or not values["uid"]:
            values["uid"] = str(uuid.uuid4())
        return values
