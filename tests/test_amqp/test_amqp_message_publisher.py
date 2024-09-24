import json

from aio_pika import Exchange

from app.amqp.amqp_message_publisher import AMQPMessagePublisher
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


async def test_publish_fetch_publications_taks(
        mocked_exchange: Exchange,
        person_pydantic_model: Person,
):
    """
    Test that a message is published to the AMQP queue when the publish method is called.
    :param mocked_exchange:
    :param person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_pydantic_model)
    local_identifier = person_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person = await dao.find_by_identifier(local_identifier.type, local_identifier.value)
    person_id = person.id
    publisher = AMQPMessagePublisher(mocked_exchange)
    expected_sent_message_payload = {'type': 'person', 'reply': True,
                                     'identifiers_safe_mode': False,
                                     'events': ['created', 'updated', 'deleted', 'unchanged'],
                                     'harvesters': ['idref', 'scanr', 'hal', 'openalex', 'scopus'],
                                     'fields': {'name': 'temporary name',
                                                'identifiers': [
                                                    {'type': 'orcid',
                                                     'value': '0000-0001-2345-6789'}]
                                                }
                                     }
    expected_sent_message_routing_key = "task.entity.references.retrieval"
    await publisher.publish(AMQPMessagePublisher.MessageType.TASK,
                            AMQPMessagePublisher.TaskMessageSubtype.PUBLICATION_RETRIEVAL,
                            {"person_id": person_id})
    mocked_exchange.publish.assert_called_once()
    message = mocked_exchange.publish.call_args[1]["message"]
    assert mocked_exchange.publish.call_args[1]["routing_key"] == expected_sent_message_routing_key
    assert message.body == json.dumps(expected_sent_message_payload).encode()
