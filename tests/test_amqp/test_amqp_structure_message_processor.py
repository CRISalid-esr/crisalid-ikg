import asyncio
import json

from app.amqp.amqp_structure_message_processor import AMQPStructureMessageProcessor
from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.organization_unit import OrganizationBase


async def test_structure_message_carries_hal_collection(
        test_app,  # pylint: disable=unused-argument
        research_unit_a_json_data: dict,
):
    """
    A created then updated structure message with hal_collection
    stores and overwrites the value in the graph.
    """
    processor = AMQPStructureMessageProcessor(asyncio.Queue(), get_app_settings())
    dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(OrganizationBase)

    created = {"structures_event": {
        "type": "created",
        "data": {**research_unit_a_json_data, "hal_collection": "https://hal.science/A"},
    }}
    # pylint: disable=protected-access
    await processor._process_message("event.structures.structure.created",
                                     json.dumps(created).encode("utf-8"))
    retrieved = await dao.get("local-U123")
    assert retrieved.hal_collection == "https://hal.science/A"

    updated = {"structures_event": {
        "type": "updated",
        "data": {**research_unit_a_json_data, "hal_collection": "https://hal.science/B"},
    }}
    await processor._process_message("event.structures.structure.updated",
                                     json.dumps(updated).encode("utf-8"))
    retrieved = await dao.get("local-U123")
    assert retrieved.hal_collection == "https://hal.science/B"
