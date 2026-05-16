from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.services.organizations.organization_unit_service import OrganizationUnitService


class AMQPStructureEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to structure events."""

    @staticmethod
    async def _build_structure_message_payload(structure_uid: str) -> dict[str, Any] | None:
        if structure_uid is None:
            logger.error("Structure UID is None while building AMQP message payload")
            return None
        service = OrganizationUnitService()
        try:
            structure = await service.get_structure_by_uid(structure_uid)
        except DatabaseError as e:
            logger.error("Error fetching structure %s: %s while building AMQP message payload",
                         structure_uid, e)
            return None
        return {
            "generic_type": structure.generic_type.value,
            "uid": structure.uid,
            "identifiers": [
                {"type": i.type.value, "value": i.value}
                for i in structure.identifiers
            ],
            "long_labels": [
                {"value": label.value, "language": label.language}
                for label in structure.long_labels
            ],
            "short_labels": [
                {"value": label.value, "language": label.language}
                for label in structure.short_labels
            ],
            "descriptions": [
                {"value": d.value, "language": d.language}
                for d in structure.descriptions
            ],
        }
