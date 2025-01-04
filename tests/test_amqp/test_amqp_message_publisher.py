import json

from aio_pika import Exchange

from app.amqp.amqp_message_publisher import AMQPMessagePublisher
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


async def test_publish_fetch_publications_taks(
        mocked_exchange: Exchange,
        persisted_person_a_pydantic_model: Person,
):
    """
    Test that a task message to fetch publication is published to the AMQP queue when the publish
    method is called.
    :param mocked_exchange:
    :param person_a_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Person)
    local_identifier = persisted_person_a_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    persisted_person_a_pydantic_model = await dao.find_by_identifier(local_identifier.type,
                                                                     local_identifier.value)
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
                            {"person_uid": persisted_person_a_pydantic_model.uid})
    mocked_exchange.publish.assert_called_once()
    message = mocked_exchange.publish.call_args[1]["message"]
    assert mocked_exchange.publish.call_args[1]["routing_key"] == expected_sent_message_routing_key
    assert message.body == json.dumps(expected_sent_message_payload).encode()


async def test_publish_person_event(
        mocked_exchange: Exchange,
        persisted_person_a_pydantic_model: Person,
):
    """
    Test that an event message for a creted person is published to the AMQP queue when the publish
    method is called.
    :param mocked_exchange:
    :param person_a_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    publisher = AMQPMessagePublisher(mocked_exchange)
    expected_sent_message_routing_key = "event.people.person.created"
    await publisher.publish(AMQPMessagePublisher.MessageType.EVENT,
                            AMQPMessagePublisher.EventMessageSubtype.PERSON_CREATED,
                            {"person_uid": persisted_person_a_pydantic_model.uid})
    mocked_exchange.publish.assert_called_once()
    message = mocked_exchange.publish.call_args[1]["message"]
    assert mocked_exchange.publish.call_args[1]["routing_key"] == expected_sent_message_routing_key
    message_body = json.loads(message.body)
    assert message_body['event'] == 'created'
    assert message_body['type'] == 'person'
    assert message_body['fields']['display_name'] == 'Doe, John'
    assert message_body['fields']['external'] is False
    assert message_body['fields']['first_name'] == 'John'
    assert message_body['fields']['last_name'] == 'Doe'
    assert message_body['fields']['uid'] == 'local-jdoe@univ-domain.edu'

    expected_identifiers = [
        {'type': 'orcid', 'value': '0000-0001-2345-6789'},
        {'type': 'local', 'value': 'jdoe@univ-domain.edu'}
    ]
    assert all(
        any(identifier == expected for identifier in message_body['fields']['identifiers']) for
        expected in expected_identifiers)
