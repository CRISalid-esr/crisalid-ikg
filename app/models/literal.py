"""
A short natural language literal with an optional language tag.
"""
from typing import ClassVar

from loguru import logger
from pydantic import BaseModel, field_validator


class Literal(BaseModel):
    """
    A short natural language literal with an optional language tag.
    """
    UNDETERMINED_LANGUAGE: ClassVar[str] = "ul"
    MAX_VALUE_LENGTH: ClassVar[int] = 4000

    value: str
    language: str = UNDETERMINED_LANGUAGE

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, v):
        if v is None:
            return cls.UNDETERMINED_LANGUAGE
        v = str(v).strip()
        return v if v else cls.UNDETERMINED_LANGUAGE

    @field_validator("value", mode="before")
    @classmethod
    def _truncate_value(cls, v):
        if v is None:
            return v
        v = str(v)
        if len(v) > cls.MAX_VALUE_LENGTH:
            logger.warning(
                "Literal value truncated from %d to %d characters",
                len(v),
                cls.MAX_VALUE_LENGTH,
            )
        return v[: cls.MAX_VALUE_LENGTH]
