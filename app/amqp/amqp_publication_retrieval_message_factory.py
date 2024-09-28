import os
from typing import Any

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.models.identifier_types import PersonIdentifierType
from app.services.people.people_service import PeopleService


class AMQPPublicationRetrievalMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to harvesting states."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_publication_retrieval_routing_key

    async def _build_payload(self) -> dict[str, Any]:
        harvesters = os.getenv("HARVESTERS", "idref,scanr,hal,openalex,scopus").split(",")
        person_id = self.content.get("person_id")
        print(f"Fetching publications for {person_id}")
        people_service = PeopleService()
        person = await people_service.get_person(person_id)
        return {
            "type": "person",
            "reply": True,
            "identifiers_safe_mode": False,
            "events": ["created", "updated", "deleted", "unchanged"],
            "harvesters": harvesters,
            "fields": {
                "name": "temporary name",
                "identifiers": [
                    {"type": id.type.value, "value": id.value}
                    for id in person.identifiers
                    if id.type is not PersonIdentifierType.LOCAL
                ],
            },
        }
