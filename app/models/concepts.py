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
    definition: Optional[Literal] = None
    broader: Optional[str] = None

    GENERATED_UID_PREFIX: ClassVar[str] = "generated-"


    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        if values.get("uid"):
            return values
        if values.get("uri"):
            return values | {"uid": values["uri"]}
        if len(values.get("pref_labels", [])) != 1:
            raise ValueError("When uri is None, there must be exactly one pref_label to "
                             "build an uid.")
        if values.get("alt_labels", []):
            raise ValueError("When uri is None, there cannot be any alt_label.")
        unique_label = dict(values["pref_labels"][0])["value"]
        assert isinstance(unique_label, str)
        return values | {"uid": cls._uid_from_preflabel(unique_label)}

    @classmethod
    def _uid_from_preflabel(cls, pref_label: str) -> str:
        uid = hashlib.md5(pref_label.encode('utf-8')).hexdigest()
        return f"{cls.GENERATED_UID_PREFIX}{uid}"


class Domain(Concept):
    """OpenAlex Domain — top-level SKOS concept"""


class Field(Concept):
    """OpenAlex Field — child of a Domain"""


class SubField(Concept):
    """OpenAlex SubField — child of a Field"""


class Topic(Concept):
    """OpenAlex Topic — child of a SubField"""
