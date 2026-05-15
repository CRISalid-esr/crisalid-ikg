from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.services.organizations.organization_unit_service import OrganizationUnitService


class AMQPResearchUnitEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to research structures events."""

    @staticmethod
    async def _build_research_unit_message_payload(research_unit_uid: str) -> dict[
        str, Any] or None:
        if research_unit_uid is None:
            logger.error("Research structure UID is None while building AMQP message payload")
            return
        service = OrganizationUnitService()
        try:
            research_unit = await service.get_structure_by_uid(research_unit_uid)
        except DatabaseError as e:
            logger.error(f"Error fetching research structure {research_unit_uid}: {e} "
                         "while building AMQP message payload")
            return
        return {
            "uid": research_unit.uid,
            "identifiers": [
                {
                    "type": identifier.type.value,
                    "value": identifier.value
                } for identifier in research_unit.identifiers
            ],
            "long_labels": [
                {
                    "value": label.value,
                    "language": label.language
                } for label in research_unit.long_labels
            ],
            "short_labels": [
                {
                    "value": label.value,
                    "language": label.language
                } for label in research_unit.short_labels
            ],
            "descriptions": [
                {
                    "value": description.value,
                    "language": description.language
                } for description in research_unit.descriptions
            ]
        }
