# pylint: disable=duplicate-code
from datetime import date
from typing import Optional

from pydantic import BaseModel, model_validator

from app.services.identifiers.identifier_service import AgentIdentifierService


class Membership(BaseModel):
    """
    Membership API model — links a Person to a research unit by uid.
    """
    entity_uid: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    past: bool = False
    future: bool = False

    @model_validator(mode='before')
    @classmethod
    def _set_entity_uid(cls, values) -> dict:
        if AgentIdentifierService.IDENTIFIER_SEPARATOR not in values.get('entity_uid', ''):
            values['entity_uid'] = f"local{AgentIdentifierService.IDENTIFIER_SEPARATOR}" \
                                   f"{values['entity_uid']}"
        return values
