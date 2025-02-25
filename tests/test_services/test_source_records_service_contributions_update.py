
from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person
from app.models.source_organizations import SourceOrganization
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService

async def test_create_source_record_with_contributions(
        # test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        hal_persisted_chapter_a_source_record_pydantic_model: SourceRecord,
        hal_chapter_a_v2_source_record_pydantic_model: SourceRecord
) -> None:
    """
    Given a persisted person pydantic model and a persisted source record pydantic model
    When the source record is updated with new contributions
    Then the source record can be read from the graph with the new contributions

    :param persisted_person_a_pydantic_model:
    :param hal_chapter_a_source_record_persisted_pydantic_model:
    :param hal_chapter_a_v2_source_record_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    fetched_source_record = await service.get_source_record(
        hal_persisted_chapter_a_source_record_pydantic_model.uid)
    assert fetched_source_record
    await service.update_source_record(
        source_record=hal_chapter_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_source_record_v2 = await service.get_source_record(
        hal_chapter_a_v2_source_record_pydantic_model.uid)
    assert fetched_source_record_v2
    assert fetched_source_record_v2.contributions
    assert len(fetched_source_record_v2.contributions) == 3
    contribution_0 = next(
        (c for c in fetched_source_record_v2.contributions if c.contributor.uid == 'hal-100001'),
        None
    )
    assert contribution_0
    assert contribution_0.rank == 1
    assert contribution_0.role == LocContributionRole.EDITOR
    assert contribution_0.contributor.name == 'Alice Dupont'
    assert len(contribution_0.affiliations) == 1
    assert contribution_0.affiliations[0].source == 'hal'
    assert contribution_0.affiliations[0].source_identifier == '2001'
    assert contribution_0.affiliations[0].name == 'Université Anonyme'
    assert contribution_0.affiliations[
               0].type == SourceOrganization.SourceOrganisationType.INSTITUTION
    assert len(contribution_0.affiliations[0].identifiers) == 4
    assert any(
        i.type == 'hal' and i.value == '2001'
        for i in contribution_0.affiliations[0].identifiers
    )
    assert any(
        i.type == 'idref' and i.value == '123456789'
        for i in contribution_0.affiliations[0].identifiers
    )
    assert any(
        i.type == 'isni' and i.value == '000000012345678X'
        for i in contribution_0.affiliations[0].identifiers
    )
    assert any(
        i.type == 'ror' and i.value == 'https://ror.org/111111111'
        for i in contribution_0.affiliations[0].identifiers
    )
    contribution_1 = next(
        (c for c in fetched_source_record_v2.contributions if c.contributor.uid == 'hal-100002'),
        None
    )
    assert contribution_1
    assert contribution_1.rank == 2
    assert contribution_1.role == LocContributionRole.TRANSLATOR
    assert contribution_1.contributor.name == 'Jean-Pierre Martin'
    assert len(contribution_1.affiliations) == 0
    contribution_2 = next(
        (c for c in fetched_source_record_v2.contributions if c.contributor.uid == 'hal-100003'),
        None
    )
    assert contribution_2
    assert contribution_2.rank == 3
    assert contribution_2.role == LocContributionRole.CREATOR
    assert contribution_2.contributor.name == 'Charlie Bernard'
    assert len(contribution_2.affiliations) == 3
    assert any(
        a.source == 'hal' and a.source_identifier == '3002'
        and a.name == 'Laboratoire Interdisciplinaire'
        for a in contribution_2.affiliations
    )
    assert any(
        a.source == 'hal' and a.source_identifier == '3003'
        and a.name == 'Groupe de Recherche Anonyme'
        for a in contribution_2.affiliations
    )
    assert any(
        a.source == 'hal' and a.source_identifier == '4001'
        and a.name == 'Centre de Recherche Avancée'
        for a in contribution_2.affiliations
    )
    contribution_3 = next(
        (c for c in fetched_source_record_v2.contributions if c.contributor.uid == 'hal-100004'),
        None
    )
    assert not contribution_3
