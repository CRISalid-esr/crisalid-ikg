import hashlib
from typing import List, ClassVar, Optional

from loguru import logger
from pydantic import BaseModel, model_validator

from app.models.source_person_identifiers import SourcePersonIdentifier


class SourcePerson(BaseModel):
    """
    Source Contributor model
    """

    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: str
    source: str
    source_identifier: Optional[str] = None
    name: str

    identifiers: List[SourcePersonIdentifier] = []

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        """
        Build the uid from the source and source_identifier
        In case source_identifier is missing, use the name to compute it as a hash

        :param values:
        :return:
        """
        if values.get("uid"):
            return values
        source = values.get("source")
        uid_suffix = values.get("source_identifier")
        name = values.get("name")
        if not source:
            logger.warning(
                f"Source person {values} must have "
                "a source to have its uid computed")
            return values
        if not uid_suffix:
            uid_suffix = hashlib.md5(name.encode('utf-8')).hexdigest()
        assert isinstance(uid_suffix, str)
        values["uid"] = f"{source.lower()}{cls.IDENTIFIER_SEPARATOR}{uid_suffix}"
        return values
