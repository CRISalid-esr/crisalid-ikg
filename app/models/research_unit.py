from typing import List, Optional

from app.models.unit import Unit


class ResearchUnit(Unit):
    """
    Research unit model
    """
    web: Optional[str]
    signature: Optional[str]
    hceres_research_areas: Optional[List[str]]
    erc_research_fields: Optional[List[str]]
