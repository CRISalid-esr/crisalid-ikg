from datetime import date
from typing import Optional

from pydantic import BaseModel, model_validator

from app.models.research_structures import ResearchStructure
from app.services.identifiers.identifier_service import AgentIdentifierService


class Membership(BaseModel):
    """
    Membership API model
    """
    entity_uid: str
    research_structure: Optional[ResearchStructure] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    past: bool = False
    future: bool = False

    # If entity_uid is not pefixed, treat it as a local identifier by default
    @model_validator(mode='before')
    @classmethod
    def _set_entity_uid(cls, values) -> dict:
        if AgentIdentifierService.IDENTIFIER_SEPARATOR not in values['entity_uid']:
            values['entity_uid'] = f"local{AgentIdentifierService.IDENTIFIER_SEPARATOR}" \
                                   f"{values['entity_uid']}"
        return values

    @model_validator(mode='after')
    def _set_research_structure(self) -> 'Membership':
        if self.research_structure is None:
            self.research_structure = ResearchStructure(
                names=[],
                identifiers=[AgentIdentifierService.compute_identifier_from_uid(
                    ResearchStructure, self.entity_uid)]
            )
        return self
