from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.person_dao import PersonDAO
from app.graph.neo4j.source_person_dao import SourcePersonDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.people import Person
from app.models.source_people import SourcePerson
from app.models.source_person_identifiers import SourcePersonIdentifier
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_source_records_with_shared_contributors(
        # pylint: disable=too-many-arguments
        test_app,  # pylint: disable=unused-argument
        persisted_person_d_pydantic_model: Person,
        persisted_person_e_pydantic_model: Person,
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        hal_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_article_a_source_record_pydantic_model: SourceRecord
) -> None:
    """
    Given 3 source records with common hal identifier and created for different persons,
    When the source records are added to the graph
    Then the source records can be read and should be related to each other with a relationship.
    """
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=hal_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_e_pydantic_model)

    await source_record_service.create_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_d_pydantic_model)

    await source_record_service.create_source_record(
        source_record=open_alex_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_d_pydantic_model)
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document = await document_dao.get_textual_document_by_source_record_uid(
        hal_article_a_source_record_pydantic_model.uid)
    assert document is not None
    assert len(document.contributions) == 10
    contribution = next(
        (contribution for contribution in document.contributions if
         contribution.contributor.uid == persisted_person_d_pydantic_model.uid),
        None)
    assert contribution is not None
    assert contribution.roles is not None
    assert len(contribution.roles) == 1
    assert contribution.roles[0].value == "http://id.loc.gov/vocabulary/relators/aut"
    assert contribution.contributor.uid == persisted_person_d_pydantic_model.uid
    assert contribution.contributor.display_name == "Garcia, Raymond"
    assert contribution.contributor.external is False
    # we take P.G. Martin, contributor with uid hal-48765589 in
    # and we add im an identifier of type open_alex and value https://openalex.org/A5088876922
    # it will be merged with r.garcia
    for contribution in hal_article_a_source_record_pydantic_model.contributions:
        if contribution.contributor.uid == 'hal-4876589':
            contribution.contributor.identifiers.append(
                SourcePersonIdentifier(
                    type="open_alex",
                    value="https://openalex.org/A5019602694"
                )
            )
    await source_record_service.update_source_record(
        source_record=hal_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_e_pydantic_model)
    document = await document_dao.get_textual_document_by_source_record_uid(
        hal_article_a_source_record_pydantic_model.uid)
    assert document is not None
    print("pause")


# pylint: disable=too-many-locals, too-many-statements
async def test_two_equivalent_records_with_the_same_contributors(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        article_exoplanet_from_oa_source_record_pydantic_model: SourceRecord,
        article_exoplanet_from_scanr_source_record_pydantic_model: SourceRecord,
) -> None:
    """
    Given two source records with the same 3 contributors from 2 different source platforms,
    When the source records are added to the graph
    Then a new Textual document is created,
    the source authors are related two by two with an equivalence relationship,
    two of the pairs are related to 2 newly created external Person nodes with :RECORDED_BY
    relationships
    and the last one is related to the Person for which the source records were harvested
    :param test_app:
    :param persisted_person_a_pydantic_model:
    :param article_exoplanet_from_oa_source_record_pydantic_model:
    :param article_exoplanet_from_scanr_source_record_pydantic_model:
    :return:
    """
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=article_exoplanet_from_oa_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)

    await source_record_service.create_source_record(
        source_record=article_exoplanet_from_scanr_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)

    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
    source_person_dao: SourcePersonDAO = cast(SourcePersonDAO, factory.get_dao(SourcePerson))
    person_dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
    assert (article_exoplanet_from_scanr_source_record_pydantic_model.uid in
            await source_record_dao.get_source_records_equivalent_uids(
                article_exoplanet_from_oa_source_record_pydantic_model.uid,
                SourceRecordDAO.EquivalenceType.INFERRED))
    document = await document_dao.get_textual_document_by_source_record_uid(
        article_exoplanet_from_oa_source_record_pydantic_model.uid)
    assert document is not None
    assert len(document.contributions) == 3
    # On of the contributions is from the person for which the source records were harvested
    internal_contribution = next(
        (contribution for contribution in document.contributions if
         contribution.contributor.uid == persisted_person_a_pydantic_model.uid),
        None)
    assert internal_contribution is not None
    assert internal_contribution.roles is not None
    assert len(internal_contribution.roles) == 1
    assert internal_contribution.roles[0].value == "http://id.loc.gov/vocabulary/relators/aut"
    assert internal_contribution.contributor.uid == persisted_person_a_pydantic_model.uid
    assert internal_contribution.contributor.display_name == "Doe, John"
    assert internal_contribution.contributor.external is False
    assert ((await person_dao.get_person_uid_by_source_person_uid(
        'open_alex-https://openalex.org/A5065084602', external=False)) ==
            persisted_person_a_pydantic_model.uid)
    assert ((await person_dao.get_person_uid_by_source_person_uid(
        'scanr-idref888888888', external=False)) ==
            persisted_person_a_pydantic_model.uid)
    # The other two contributions are from external persons
    external_contributions = [contribution for contribution in document.contributions if
                              contribution.contributor.external]
    assert len(external_contributions) == 2
    external_contribution_1 = next(
        (contribution for contribution in external_contributions if
         contribution.contributor.uid == 'open_alex-https://openalex.org/A5088876922'),
        None)
    assert external_contribution_1 is not None
    assert external_contribution_1.roles is not None
    assert len(external_contribution_1.roles) == 1
    assert external_contribution_1.roles[0].value == "http://id.loc.gov/vocabulary/relators/aut"
    assert external_contribution_1.contributor.uid == 'open_alex-https://openalex.org/A5088876922'
    assert external_contribution_1.contributor.display_name == "Jane Smith"
    assert external_contribution_1.contributor.external is True
    external_contribution_2 = next(
        (contribution for contribution in external_contributions if
         contribution.contributor.uid == 'open_alex-https://openalex.org/A5019602694'),
        None)
    assert external_contribution_2 is not None
    assert external_contribution_2.roles is not None
    assert len(external_contribution_2.roles) == 1
    assert external_contribution_2.roles[0].value == "http://id.loc.gov/vocabulary/relators/aut"
    assert external_contribution_2.contributor.uid == 'open_alex-https://openalex.org/A5019602694'
    assert external_contribution_2.contributor.display_name == "Michael Garcia"
    assert external_contribution_2.contributor.external is True

    assert (await source_person_dao.get_equivalents(
        'scanr-idref888888888')) == ['open_alex-https://openalex.org/A5065084602']
    assert (await source_person_dao.get_equivalents(
        'open_alex-https://openalex.org/A5065084602')) == ['scanr-idref888888888']
    assert (await source_person_dao.get_equivalents(
        'open_alex-https://openalex.org/A5019602694')) == ['scanr-idref999999999']
    assert (await source_person_dao.get_equivalents(
        'scanr-idref999999999')) == ['open_alex-https://openalex.org/A5019602694']
    # use person_dao.get_person_uid_by_source_person_uid
    # to check that the pairs of source people are related to same external person
    external_person_1_uid_1 = await person_dao.get_person_uid_by_source_person_uid(
        'open_alex-https://openalex.org/A5088876922', external=True)
    assert external_person_1_uid_1 is not None
    external_person_1_uid_2 = await person_dao.get_person_uid_by_source_person_uid(
        'scanr-Smith###J', external=True)
    assert external_person_1_uid_2 is not None
    assert external_person_1_uid_1 == external_person_1_uid_2
    external_person_2_uid_1 = await person_dao.get_person_uid_by_source_person_uid(
        'open_alex-https://openalex.org/A5019602694', external=True)
    assert external_person_2_uid_1 is not None
    external_person_2_uid_2 = await person_dao.get_person_uid_by_source_person_uid(
        'scanr-idref999999999', external=True)
    assert external_person_2_uid_2 is not None
    assert external_person_2_uid_1 == external_person_2_uid_2
