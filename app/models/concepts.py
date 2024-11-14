import hashlib
from typing import List, Optional, ClassVar

from pydantic import BaseModel, model_validator

from app.models.literal import Literal


class Concept(BaseModel):
    """
    Subject model (follows RDF Skos concept schema)
    """
    uid: Optional[str] = None
    uri: Optional[str] = None
    pref_labels: List[Literal] = []
    alt_labels: List[Literal] = []

    GENERATED_UID_PREFIX: ClassVar[str] = "generated-"

    # validators are likely to be executed in the order they are defined
    # see https://github.com/pydantic/pydantic/discussions/7434
    @model_validator(mode="after")
    def _check_labels(self):
        if self.uri is None:
            if len(self.pref_labels) != 1:
                raise ValueError("When uri is None, there must be exactly one pref_label.")
            if self.alt_labels:
                raise ValueError("When uri is None, alt_labels must be empty.")
        return self

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        if not values.get("uid"):
            if values.get("uri"):
                values["uid"] = values["uri"]
            else:
                values["uid"] = cls._uid_from_preflabel(dict(values["pref_labels"][0])["value"])
        return values

    @classmethod
    def _uid_from_preflabel(cls, pref_label: str) -> str:
        uid = hashlib.md5(pref_label.encode('utf-8')).hexdigest()
        return f"{cls.GENERATED_UID_PREFIX}{uid}"
