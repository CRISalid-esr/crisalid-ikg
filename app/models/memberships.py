from datetime import date
from typing import Optional

from pydantic import BaseModel, model_validator

from app.models.research_structures import ResearchStructure
from app.services.identifiers.identifier_service import AgentIdentifierService


class Membership(BaseModel):
    """
    Membership API model
    """
    entity_id: str
    research_structure: Optional[ResearchStructure] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    past: bool = False
    future: bool = False

    @model_validator(mode='after')
    def _set_research_structure(self) -> 'Membership':
        if self.research_structure is None:
            self.research_structure = ResearchStructure(
                names=[],
                identifiers=[AgentIdentifierService.compute_identifier_from_uid(
                    ResearchStructure, self.entity_id)]
            )
        return self
