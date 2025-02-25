from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.services.organizations.research_structure_service import ResearchStructureService


class AMQPResearchStructureEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to research structures events."""

    @staticmethod
    async def _build_research_structure_message_payload(research_structure_uid: str) -> dict[
        str, Any] or None:
        if research_structure_uid is None:
            logger.error("Research structure UID is None while building AMQP message payload")
            return
        research_structure_service = ResearchStructureService()
        try:
            research_structure = await research_structure_service.get_structure_by_uid(
                research_structure_uid)
        except DatabaseError as e:
            logger.error(f"Error fetching research structure {research_structure_uid}: {e} "
                         "while building AMQP message payload")
            return
        return {
            "uid": research_structure.uid,
            "identifiers": [
                {
                    "type": identifier.type.value,
                    "value": identifier.value
                } for identifier in research_structure.identifiers
            ],
            "names": [
                {
                    "value": name.value,
                    "language": name.language
                } for name in research_structure.names
            ],
            "acronym": research_structure.acronym,
            "descriptions": [
                {
                    "value": description.value,
                    "language": description.language
                } for description in research_structure.descriptions
            ]
        }
