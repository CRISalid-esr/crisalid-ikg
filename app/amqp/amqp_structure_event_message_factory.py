from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.models.organization_unit import UnitBase
from app.services.organizations.organization_unit_service import OrganizationUnitService


class AMQPStructureEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to structure events."""

    @staticmethod
    def _serialize_literal(lit) -> dict:
        return {"value": lit.value, "language": lit.language}

    @classmethod
    def _serialize_address(cls, addr) -> dict:
        result = {}
        for field in ("street", "city", "zip_code", "state_or_province", "country"):
            literals = getattr(addr, field, [])
            if literals:
                result[field] = [cls._serialize_literal(lit) for lit in literals]
        return result

    @classmethod
    async def _build_structure_message_payload(cls, structure_uid: str) -> dict[str, Any] | None:
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

        payload: dict[str, Any] = {
            "generic_type": structure.generic_type.value,
            "uid": structure.uid,
            "national_type": structure.national_type.value if structure.national_type else None,
            "local_types": [cls._serialize_literal(lt) for lt in structure.local_types],
            "identifiers": [
                {"type": i.type.value, "value": i.value} for i in structure.identifiers
            ],
            "long_labels": [cls._serialize_literal(label) for label in structure.long_labels],
            "short_labels": [cls._serialize_literal(label) for label in structure.short_labels],
            "descriptions": [cls._serialize_literal(d) for d in structure.descriptions],
            "memberships": [
                {
                    "target": m.target,
                    "position": m.position.value if m.position else None,
                    "start_date": m.start_date.isoformat() if m.start_date else None,
                    "end_date": m.end_date.isoformat() if m.end_date else None,
                }
                for m in structure.memberships
            ],
            "parents": [
                {
                    "target": p.target,
                    "start_date": p.start_date.isoformat() if p.start_date else None,
                    "end_date": p.end_date.isoformat() if p.end_date else None,
                }
                for p in structure.parents
            ],
            "addresses": [cls._serialize_address(addr) for addr in structure.addresses],
            "electronical_addresses": [
                {"uri": ea.uri} for ea in structure.electronical_addresses
            ],
        }

        if isinstance(structure, UnitBase):
            payload["main_mission"] = structure.main_mission.value
            payload["secondary_missions"] = [m.value for m in structure.secondary_missions]

        return payload
