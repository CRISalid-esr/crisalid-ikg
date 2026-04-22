from app.models.research_unit import ResearchUnit


def test_create_valid_organization(research_unit_a_json_data):
    """
    Given a valid organization model
    When asked for different field values
    Then the values should be returned correctly
    :param research_unit_a_json_data:
    :return:
    """
    structure = ResearchUnit(**research_unit_a_json_data)
    assert len(research_unit_a_json_data["names"]) == 2
    assert len(structure.names) == len(research_unit_a_json_data["names"])
    assert any(
        literal.value == "Laboratoire toto" and literal.language == "fr"
        for literal in structure.names
    )
    assert any(
        literal.value == "Foobar Laboratory" and literal.language == "en"
        for literal in structure.names
    )
    assert structure.acronym == research_unit_a_json_data["acronym"]
    assert len(structure.descriptions) == len(research_unit_a_json_data["descriptions"])
