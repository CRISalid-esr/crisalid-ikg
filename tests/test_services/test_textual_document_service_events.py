import json


from app.config import get_app_settings
from app.models.textual_document import TextualDocument
from app.services.documents.textual_document_service import TextualDocumentService


async def test_signal_textual_document_created(
        test_app,  # pylint: disable=unused-argument
        mocked_exchange,
        textual_document_hal_article_a_persisted_model: TextualDocument
) -> None:
    """
    Test dispatch_event command for a single person.
    """
    test_app.amqp_interface.pika_exchanges[
        get_app_settings().amqp_graph_exchange_name] = mocked_exchange
    service = TextualDocumentService()
    await service.signal_textual_document_created(
        textual_document_hal_article_a_persisted_model.uid)
    expected_sent_message_routing_key = "event.documents.document.created"
    expected_sent_message_payload_fields = {'abstracts': [], 'contributions': [{'contributor': {
        'display_name': 'Jérôme Février', 'external': True, 'identifiers': [], 'memberships': [],
        'names': [], 'uid': 'hal-863912'}, 'rank': None, 'roles': ['LocContributionRole.AUTHOR']}, {
        'contributor': {
            'display_name': 'N. Mahajan',
            'external': True,
            'identifiers': [],
            'memberships': [],
            'names': [],
            'uid': 'hal-87564'},
        'rank': None, 'roles': [
            'LocContributionRole.AUTHOR']}, {'contributor': {
        'display_name': 'M.-A. Miville-Deschênes', 'external': True, 'identifiers': [],
        'memberships': [], 'names': [], 'uid': 'hal-578950'}, 'rank': None,
        'roles': ['LocContributionRole.AUTHOR']}, {
        'contributor': {
            'display_name': 'B. M. Gaensler',
            'external': True,
            'identifiers': [],
            'memberships': [],
            'names': [],
            'uid': 'hal-467432'},
        'rank': None, 'roles': [
            'LocContributionRole.AUTHOR']}, {'contributor': {'display_name': 'L F J',
                                                             'external': True, 'identifiers': [],
                                                             'memberships': [], 'names': [],
                                                             'uid': 'hal-4876589'}, 'rank': None,
                                             'roles': ['LocContributionRole.AUTHOR']}, {
        'contributor': {
            'display_name': 'F. Boulanger',
            'external': True,
            'identifiers': [],
            'memberships': [],
            'names': [],
            'uid': 'hal-7543789'},
        'rank': None, 'roles': [
            'LocContributionRole.AUTHOR']}, {'contributor': {'display_name': 'Garcia, Raymond',
                                                             'external': False, 'identifiers': [],
                                                             'memberships': [], 'names': [
            {
                'first_names': [...], 'last_names': [...],
                'other_names': []}],
                'uid': 'local-rgarcia@univ-domain.edu'},
                'rank': None, 'roles': ['LocContributionRole.AUTHOR']},
        {'contributor': {
            'display_name': 'A. Smith',
            'external': True,
            'identifiers': [],
            'memberships': [],
            'names': [],
            'uid': 'hal-43b38a7c4e694812ba4a2fe8c40ab09d'},
            'rank': None, 'roles': [
            'LocContributionRole.AUTHOR']}],
                                            'subjects': [], 'titles': [
            {'language': 'en',
             'value':
                 'All We Are Is Dust in the WIM: Constraints on Dust Properties '
                 'in the Milky Way’s Warm Ionized Medium'}],
                                            'uid': '9ad8e958-d8fd-4e9f-b1b1-f400a6d28c2f'}

    mocked_exchange.publish.assert_called_once()
    message = mocked_exchange.publish.call_args[1]["message"]
    assert mocked_exchange.publish.call_args[1]["routing_key"] == expected_sent_message_routing_key
    message_payload = json.loads(message.body.decode())
    assert message_payload['event'] == "created"
    assert message_payload['type'] == 'document'
    assert sorted(message_payload['fields']['titles']) == sorted(
        expected_sent_message_payload_fields['titles'])
    assert sorted(message_payload['fields']['abstracts']) == sorted(
        expected_sent_message_payload_fields['abstracts'])
    assert sorted(message_payload['fields']['subjects']) == sorted(
        expected_sent_message_payload_fields['subjects'])
    # compare contribution length
    assert len(message_payload['fields']['contributions']) == len(
        expected_sent_message_payload_fields['contributions'])
    local_contributor = [contrib for contrib in message_payload['fields']['contributions'] if
                         contrib['contributor']['uid'] == 'local-rgarcia@univ-domain.edu'][0]
    assert local_contributor['contributor']['names'][0]['last_names'][0]['value'] == 'Garcia'
    assert local_contributor['contributor']['names'][0]['last_names'][0]['language'] == 'fr'
    assert local_contributor['contributor']['names'][0]['first_names'][0]['value'] == 'Raymond'
    assert local_contributor['contributor']['names'][0]['first_names'][0]['language'] == 'fr'
    assert local_contributor['roles'] == ['LocContributionRole.AUTHOR']
