import json
from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.agent_identifiers import PersonIdentifier
from app.models.document import Document
from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person
from app.services.documents.document_service import DocumentService
from app.services.source_records.source_record_service import SourceRecordService
from tests.fixtures.common import _source_record_from_json_data

CTB = LocContributionRole.CONTRIBUTOR
AUT = LocContributionRole.AUTHOR


def _strip_roles(source_record_json_data: dict) -> dict:
    for contribution in source_record_json_data["contributions"]:
        contribution.pop("role", None)
    return source_record_json_data


def _set_roles(source_record_json_data: dict, role_url: str) -> dict:
    for contribution in source_record_json_data["contributions"]:
        contribution["role"] = role_url
    return source_record_json_data


def _document_dao() -> DocumentDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(DocumentDAO, factory.get_dao(Document))


async def _stored_source_roles(source_record_uid: str) -> list:
    query = (
        "MATCH (:SourceRecord {uid: $uid})-[:HAS_CONTRIBUTION]->(sc:SourceContribution) "
        "RETURN collect(sc.role) AS roles"
    )
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, uid=source_record_uid)
            record = await result.single()
            return record["roles"]


async def test_source_record_without_roles_stores_contributor(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_json_data: dict,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given a source record whose contributions carry no role
    When the source record is persisted and read back
    Then every source contribution has the generic Contributor role,
    stored as the 'CONTRIBUTOR' property on the SourceContribution node
    """
    record = _source_record_from_json_data(
        _strip_roles(article_exoplanet_from_oa_source_record_json_data))
    service = SourceRecordService()
    await service.create_source_record(
        source_record=record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    fetched = await service.get_source_record(record.uid)
    assert fetched is not None
    assert len(fetched.contributions) == 3
    assert all(contribution.role == CTB for contribution in fetched.contributions)
    assert await _stored_source_roles(record.uid) == ["CONTRIBUTOR"] * 3


async def test_source_contribution_without_role_property_hydrates_as_contributor(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_json_data: dict,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given a persisted SourceContribution node whose role property has been removed
    When the source record is read back
    Then the contribution hydrates with the generic Contributor role (defensive case)
    """
    record = _source_record_from_json_data(article_exoplanet_from_oa_source_record_json_data)
    service = SourceRecordService()
    await service.create_source_record(
        source_record=record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    query = (
        "MATCH (:SourceRecord {uid: $uid})-[:HAS_CONTRIBUTION]->(sc:SourceContribution) "
        "REMOVE sc.role"
    )
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            await session.run(query, uid=record.uid)
    fetched = await service.get_source_record(record.uid)
    assert fetched is not None
    assert len(fetched.contributions) == 3
    assert all(contribution.role == CTB for contribution in fetched.contributions)


async def test_document_contributions_default_to_contributor(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_json_data: dict,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given a document built from a single source record whose contributions carry no role
    When the document is read back
    Then every contribution has exactly the generic Contributor role
    """
    record = _source_record_from_json_data(
        _strip_roles(article_exoplanet_from_oa_source_record_json_data))
    await SourceRecordService().create_source_record(
        source_record=record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    document = await _document_dao().get_document_by_source_record_uid(record.uid)
    assert document is not None
    assert len(document.contributions) == 3
    assert all(contribution.roles == [CTB] for contribution in document.contributions)


async def test_generic_role_dropped_when_specific_role_present(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_json_data: dict,
        article_exoplanet_from_scanr_source_record_json_data: dict,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given two equivalent source records, one with Author roles
    and one whose contributions carry no role (defaulting to Contributor)
    When the document is built from both
    Then every contribution keeps only the Author role
    """
    service = SourceRecordService()
    oa_record = _source_record_from_json_data(article_exoplanet_from_oa_source_record_json_data)
    await service.create_source_record(
        source_record=oa_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    scanr_record = _source_record_from_json_data(
        _strip_roles(article_exoplanet_from_scanr_source_record_json_data))
    await service.create_source_record(
        source_record=scanr_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    document = await _document_dao().get_document_by_source_record_uid(oa_record.uid)
    assert document is not None
    assert len(document.contributions) == 3
    assert all(contribution.roles == [AUT] for contribution in document.contributions)


async def test_genuine_contributor_role_dropped_when_specific_role_present(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_json_data: dict,
        article_exoplanet_from_scanr_source_record_json_data: dict,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given two equivalent source records, one with Author roles
    and one with genuine harvested Contributor roles
    When the document is built from both
    Then every contribution keeps only the Author role
    """
    service = SourceRecordService()
    oa_record = _source_record_from_json_data(article_exoplanet_from_oa_source_record_json_data)
    await service.create_source_record(
        source_record=oa_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    scanr_record = _source_record_from_json_data(
        _set_roles(article_exoplanet_from_scanr_source_record_json_data,
                   "https://id.loc.gov/vocabulary/relators/ctb.html"))
    await service.create_source_record(
        source_record=scanr_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    document = await _document_dao().get_document_by_source_record_uid(oa_record.uid)
    assert document is not None
    assert len(document.contributions) == 3
    assert all(contribution.roles == [AUT] for contribution in document.contributions)


async def test_document_event_payload_carries_contributor_role(
        test_app,
        mocked_exchange,
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_json_data: dict,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given a document built from a source record whose contributions carry no role
    When the document created event is published
    Then the payload contributions carry the Contributor role (never an empty roles list)
    """
    record = _source_record_from_json_data(
        _strip_roles(article_exoplanet_from_oa_source_record_json_data))
    await SourceRecordService().create_source_record(
        source_record=record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    document = await _document_dao().get_document_by_source_record_uid(record.uid)
    assert document is not None
    test_app.amqp_interface.pika_exchanges[
        get_app_settings().amqp_graph_exchange_name] = mocked_exchange
    await DocumentService().signal_document_created(document.uid)
    mocked_exchange.publish.assert_called_once()
    message = mocked_exchange.publish.call_args[1]["message"]
    message_payload = json.loads(message.body.decode())
    contributions = message_payload["fields"]["contributions"]
    assert len(contributions) == 3
    assert all(
        contribution["roles"] == ["LocContributionRole.CONTRIBUTOR"]
        for contribution in contributions)
