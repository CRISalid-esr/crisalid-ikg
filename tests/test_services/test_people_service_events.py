import json

from app.config import get_app_settings
from app.models.people import Person
from app.services.people.people_service import PeopleService


async def test_signal_person_created(
        test_app,  # pylint: disable=unused-argument
        mocked_exchange,
        persisted_person_a_pydantic_model: Person, ):
    """
    Test dispatch_event command for a single person.
    """
    test_app.amqp_interface.pika_exchanges[
        get_app_settings().amqp_graph_exchange_name] = mocked_exchange
    service = PeopleService()
    await service.signal_person_created(persisted_person_a_pydantic_model.uid)
    expected_sent_message_routing_key = "event.people.person.created"
    expected_sent_message_payload = {'event': 'created',
                                     'fields': {'display_name': 'Doe, John', 'external': False,
                                                'first_name': 'John', 'identifiers': [
                                             {'type': 'local', 'value': 'jdoe@univ-domain.edu'},
                                             {'type': 'orcid', 'value': '0000-0001-2345-6789'}],
                                                'last_name': 'Doe', 'memberships': [],
                                                'uid': 'local-jdoe@univ-domain.edu'},
                                     'type': 'person'}

    mocked_exchange.publish.assert_called_once()
    message = mocked_exchange.publish.call_args[1]["message"]
    assert mocked_exchange.publish.call_args[1]["routing_key"] == expected_sent_message_routing_key
    assert json.loads(message.body.decode()) == expected_sent_message_payload
