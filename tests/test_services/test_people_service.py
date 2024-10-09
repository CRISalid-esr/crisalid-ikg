from app.models.people import Person
from app.services.people.people_service import PeopleService


async def test_create_person(
        person_pydantic_model: Person,
        persisted_research_structure_pydantic_model  # pylint: disable=unused-argument
) -> None:
    """
    Given a basic person pydantic model
    When the person is added to the graph
    Then the person can be read from the graph
    :param person_pydantic_model:
    :return:
    """
    service = PeopleService()
    await service.create_person(person_pydantic_model)
    fetched_person = await service.get_person(person_pydantic_model.uid)
    assert fetched_person.uid == person_pydantic_model.uid
    assert len(fetched_person.identifiers) == len(person_pydantic_model.identifiers)
    for identifier in person_pydantic_model.identifiers:
        assert any(
            fetched_identifier.type == identifier.type
            and fetched_identifier.value == identifier.value
            for fetched_identifier in fetched_person.identifiers
        )
    assert len(fetched_person.names) == len(person_pydantic_model.names)
    assert len(person_pydantic_model.memberships) == 1
    assert len(fetched_person.memberships) == len(person_pydantic_model.memberships)
    assert len(person_pydantic_model.memberships[0].research_structure.identifiers) == 1
    assert len(fetched_person.memberships[0].research_structure.identifiers) == len(
        person_pydantic_model.memberships[0].research_structure.identifiers
    )
    for fetched_membership in fetched_person.memberships:
        for fetched_identifier in fetched_membership.research_structure.identifiers:
            assert any(
                identifier.type == fetched_identifier.type
                and identifier.value == fetched_identifier.value
                for membership in person_pydantic_model.memberships
                for identifier in membership.research_structure.identifiers
            )


async def test_create_person_without_name(
        person_without_name_pydantic_model: Person,
) -> None:
    """
    Given a person without name pydantic model
    When the person is added to the graph
    Then the person can be read from the graph
    :param person_without_name_pydantic_model:
    :return:
    """
    service = PeopleService()
    await service.create_person(person_without_name_pydantic_model)
    fetched_person = await service.get_person(person_without_name_pydantic_model.uid)
    assert fetched_person.uid == person_without_name_pydantic_model.uid
    assert len(person_without_name_pydantic_model.names) == 0
    assert all(
        not name.first_names and not name.last_names and not name.other_names
        for name in fetched_person.names
    )
