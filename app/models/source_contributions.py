import re
from typing import Optional, List

from loguru import logger
from pydantic import BaseModel, field_validator

from app.models.loc_contribution_role import LocContributionRole
from app.models.source_organizations import SourceOrganization
from app.models.source_people import SourcePerson


class SourceContribution(BaseModel):
    """
    Source Contribution model
    """
    rank: Optional[int] = None
    role: Optional[LocContributionRole] = None
    contributor: SourcePerson
    affiliations: List[SourceOrganization] = []

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, value):
        """
        Convert a role URI to the corresponding LocContributionRole Enum entry.
        """
        if isinstance(value, LocContributionRole):
            return value
        if value is None or not isinstance(value, str):
            return None
        value = cls.url_to_uri(value)
        try:
            return LocContributionRole(value)
        except ValueError:
            logger.error(f"Invalid contribution role: {value}")
            return None

    @staticmethod
    def url_to_uri(url: str) -> str:
        """
        Convert a URL to a URI by removing the trailing .html and replacing https with http.
        Example: https://id.loc.gov/vocabulary/relators/aut.html
        -> https://id.loc.gov/vocabulary/relators/aut

        :param url: URL to convert
        :return: Converted URI
        """
        return re.sub(r"^https", "http", re.sub(r"\.html$", "", url))
