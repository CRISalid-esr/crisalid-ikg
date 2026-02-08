import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from app.amqp.amqp_harvesting_events_message_processor import AMQPHarvestingEventsMessageProcessor
from app.config import get_app_settings
from app.crisalid_ikg import CrisalidIKG


@pytest.mark.asyncio
async def test_amqp_harvesting_state_event_is_forwarded(test_app: CrisalidIKG):
    """
    Test that a harvesting state event is processed and forwarded via AMQP publisher.
    """
    person_uid = "carin-e"
    name = "CARIN Emmanuel"
    identifiers = [
        {"type": "idref", "value": "068825511"},
        {"type": "local", "value": person_uid},
        {"type": "eppn", "value": f"{person_uid}@univ-example.fr"},
        {"type": "scopus_eid", "value": "2213765400"},
    ]

    harvesting_state_message = {
        "entity": {
            "identifiers": identifiers,
            "name": name,
        },
        "error": [],
        "harvester": "idref",
        "state": "running",
    }

    expected_payload = {
        "type": "harvesting_state_event",
        "fields": harvesting_state_message,
    }

    routing_key_expected = "event.harvestings.state.running"

    payload_bytes = json.dumps(harvesting_state_message).encode("utf-8")
    queue = asyncio.Queue()
    settings = get_app_settings()
    processor = AMQPHarvestingEventsMessageProcessor(queue, settings)

    # Mock the exchange used by the publisher
    mock_exchange = AsyncMock()
    test_app.amqp_interface.pika_exchanges[settings.amqp_graph_exchange_name] = mock_exchange

    # pylint: disable=protected-access
    await processor._process_message("event.harvesting.state", payload_bytes)

    mock_exchange.publish.assert_awaited_once()

    message_arg = mock_exchange.publish.call_args.kwargs["message"]
    routing_key_arg = mock_exchange.publish.call_args.kwargs["routing_key"]

    decoded_body = json.loads(message_arg.body.decode("utf-8"))

    assert decoded_body == expected_payload
    assert routing_key_arg == routing_key_expected


@pytest.mark.asyncio
async def test_amqp_harvesting_result_event_is_forwarded(test_app: CrisalidIKG):
    """
    Test that a harvesting result event is processed and forwarded via AMQP publisher.
    """
    # Simulated minimal and anonymized input message (already received)
    harvesting_result_message = {
        "entity": {
            "identifiers": [
                {"type": "local", "value": "user-123"}
            ],
            "name": "Anonymous User"
        },
        "reference_event": {
            "enhanced": False,
            "reference": {
                "titles": [
                    {
                        "language": "fr",
                        "value": "Effets d'une stimulation nerveuse sur la barrière intestinale"
                    }
                ],
                "subtitles": [
                    {
                        "language": "fr",
                        "value": "Étude expérimentale chez l'animal"
                    }
                ],
                "abstracts": [
                    {
                        "language": "fr",
                        "value": "Cette étude explore les effets de la stimulation nerveuse..."
                    },
                    {
                        "language": "en",
                        "value": "This study investigates the effects of nerve stimulation..."
                    }
                ],
                "contributions": [
                    {
                        "contributor": {
                            "name": "A. Researcher"
                        },
                        "role": "author"
                    },
                    {
                        "contributor": {
                            "name": "B. Scientist"
                        },
                        "role": "thesis_advisor"
                    }
                ],
                "document_type": [{"label": "Work"}],
                "issued": "2013-01-01",
                "harvester": "hal",
                "harvester_version": "0.1.0",
                "identifiers": [
                    {"type": "uri", "value": "http://example.org/doc/123"}
                ]
            },
            "type": "created"
        }
    }

    expected_payload = {
        "type": "harvesting_result_event",
        "fields": harvesting_result_message
    }

    routing_key_expected = "event.harvestings.result.created"

    payload_bytes = json.dumps(harvesting_result_message).encode("utf-8")
    queue = asyncio.Queue()
    settings = get_app_settings()
    processor = AMQPHarvestingEventsMessageProcessor(queue, settings)

    mock_exchange = AsyncMock()
    test_app.amqp_interface.pika_exchanges[settings.amqp_graph_exchange_name] = mock_exchange

    # pylint: disable=protected-access
    await processor._process_message("event.harvestings.result.created", payload_bytes)

    mock_exchange.publish.assert_awaited_once()

    message_arg = mock_exchange.publish.call_args.kwargs["message"]
    routing_key_arg = mock_exchange.publish.call_args.kwargs["routing_key"]
    decoded_body = json.loads(message_arg.body.decode("utf-8"))

    assert decoded_body == expected_payload
    assert routing_key_arg == routing_key_expected
    