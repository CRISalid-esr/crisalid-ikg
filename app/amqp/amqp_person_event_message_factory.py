from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.services.people.people_service import PeopleService


class AMQPPersonEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to people events."""

    @staticmethod
    async def _build_person_message_payload(person_uid: str) -> dict[str, Any]:
        if person_uid is None:
            logger.error("Person UID is None while building AMQP message payload")
            return
        people_service = PeopleService()
        try:
            person = await people_service.get_person(person_uid)
        except DatabaseError as e:
            logger.error(f"Error fetching person {person_uid}: {e} "
                         "while building AMQP message payload")
            return
        return {
            "display_name": person.display_name,
            "first_name": person.get_first_name(),
            "last_name": person.get_last_name(),
            "external": person.external,
            "uid": person.uid,
            "identifiers": [
                {
                    "type": identifier.type.value,
                    "value": identifier.value
                }
                for identifier in person.identifiers
            ],
            "memberships": [
                {
                    "entity_uid": membership.entity_uid,
                    "research_structure": {
                        "names": [
                            {
                                "value": name.value
                            }
                            for name in membership.research_structure.names
                        ],
                        "identifiers": [
                            {
                                "type": identifier.type.value,
                                "value": identifier.value
                            }
                            for identifier in membership.research_structure.identifiers
                        ]
                    },
                    "start_date": membership.start_date,
                    "end_date": membership.end_date,
                }
                for membership in person.memberships
            ]
        }
