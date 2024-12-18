from typing import ClassVar

from pydantic import BaseModel, model_validator


class SourceOrganizationIdentifier(BaseModel):
    """
    Source Organization Identifier API model
    """
    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    type: str
    value: str

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        type_ = values.get("type")
        value = values.get("value")
        if not type_ or not value:
            return values
        values["uid"] = (f"{str(type_).lower()}"
                         f"{SourceOrganizationIdentifier.IDENTIFIER_SEPARATOR}"
                         f"{value}")
        return values
