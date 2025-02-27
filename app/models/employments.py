from datetime import date
from typing import Optional

from loguru import logger
from pydantic import BaseModel, model_validator

from app.models.institution import Institution
from app.models.positions import Position
from app.services.identifiers.identifier_service import AgentIdentifierService


class Employment(BaseModel):
    """
    Membership API model
    """
    entity_uid: str

    institution: Optional[Institution] = None

    position: Optional[Position] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    past: bool = False
    future: bool = False

    @model_validator(mode="before")
    @classmethod
    def _validate_position(cls, values):
        """Validate and hydrate position from code."""
        if "position" in values and isinstance(values["position"], dict):
            position_data = values["position"]
            if "code" in position_data:
                try:
                    values["position"] = Position.from_code(position_data["code"])
                except ValueError as e:
                    logger.error(f"Invalid position code: {position_data['code']} - {e}")
                    values["position"] = None
        return values

    @model_validator(mode='after')
    def _set_institution(self) -> 'Employment':
        if self.institution is None:
            self.institution = Institution(
                names=[],
                identifiers=[AgentIdentifierService.compute_identifier_from_uid(
                    Institution, self.entity_uid)]
            )
        return self
