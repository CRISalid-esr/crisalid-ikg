from app.models.people import Person


def test_create_person_with_two_employements(person_a_with_two_employments_json_data):
    """
    Given a valid person model with two employments
    When asked for different field values
    Then the values should be returned correctly
    :param person_a_with_two_employments_json_data:
    :return:
    """
    person = Person(**person_a_with_two_employments_json_data)
    assert person.employments is not None
    assert len(person.employments) == 2
    # pylint: disable=unsubscriptable-object
    assert person.employments[0].entity_uid == "uai-0751717J"
    assert person.employments[0].position.code == "PAST"
    assert person.employments[0].position.title == (
        "Enseignant-chercheur associé "
        "(MC, PR à temps partiel ou temps plein)")
    assert person.employments[1].entity_uid == "uai-1234567A"
    assert person.employments[1].position.code == "ATER"
    assert person.employments[
               1].position.title == "Attaché temporaire d'enseignement et de recherche"


def test_create_person_with_invalid_employment_position(
        person_a_with_invalid_employment_position_json_data):
    """
    Given json person data with invalid employment position
    When creating a person object
    Then the person should have an employment without position

    :param person_a_with_invalid_employment_position_json_data:
    :return:
    """
    person = Person(**person_a_with_invalid_employment_position_json_data)
    assert len(person.employments) == 1
    # pylint: disable=unsubscriptable-object
    assert person.employments[0].entity_uid == "uai-0751717J"
    assert not person.employments[0].position


def test_create_person_with_employment_without_position(
        person_a_with_employment_without_position_json_data):
    """
    Given json person data with employment without position
    When creating a person object
    Then the person should have an employment without position

    :param person_a_with_employment_without_position_json_data:
    :return:
    """
    person = Person(**person_a_with_employment_without_position_json_data)
    assert len(person.employments) == 1
    # pylint: disable=unsubscriptable-object
    assert person.employments[0].entity_uid == "uai-0751717J"
    assert not person.employments[0].position
