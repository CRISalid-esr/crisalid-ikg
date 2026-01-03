"""
Literal model
"""
from typing import ClassVar

from pydantic import BaseModel, field_validator


class Literal(BaseModel):
    """
    A literal value with a language tag (mimic RDF literals).
    """
    UNDETERMINED_LANGUAGE: ClassVar[str] = "ul"

    value: str
    language: str = UNDETERMINED_LANGUAGE

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, v):
        if v is None:
            return cls.UNDETERMINED_LANGUAGE
        v = str(v).strip()
        return v if v else cls.UNDETERMINED_LANGUAGE
