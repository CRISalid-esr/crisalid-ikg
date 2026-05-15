from datetime import date
from typing import Optional

from loguru import logger
from pydantic import BaseModel, model_validator

from app.models.positions import Position
from app.services.identifiers.identifier_service import AgentIdentifierService


class Employment(BaseModel):
    """
    Employment API model — links a Person to an institution by uid.
    """
    entity_uid: str
    position: Optional[Position] = None
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

    @model_validator(mode="before")
    @classmethod
    def _validate_position(cls, values):
        if "position" in values and isinstance(values["position"], dict):
            position_data = values["position"]
            if "code" in position_data:
                try:
                    values["position"] = Position.from_code(position_data["code"])
                except ValueError as e:
                    logger.error(f"Invalid position code: {position_data['code']} - {e}")
                    values["position"] = None
        return values
