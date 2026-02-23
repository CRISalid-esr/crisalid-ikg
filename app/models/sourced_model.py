from loguru import logger
from pydantic import BaseModel, field_validator

from app.models.harvesting_sources import HarvestingSource


class SourcedModel(BaseModel):
    """
    Common supertype for models that have a source and source_identifier
     (e.g. SourcePerson, SourceOrganization, SourceJournal)
    """
    source: HarvestingSource

    @field_validator("source", mode="before")
    @classmethod
    def _validate_source(cls, value):
        try:
            return HarvestingSource(value)
        except ValueError:
            logger.warning(f"Invalid source {value} for {cls.__name__}")
            return value
