from app.models.concepts import Concept
from app.models.literal import Literal
from app.services.concepts.concept_service import ConceptService


async def test_create_concept_with_uri(concept_pydantic_model: Concept) -> None:
    """
    Given a concept pydantic model
    When the concept is created
    Then the concept should be returned correctly
    :return:
    """
    service = ConceptService()
    await service.create_or_update_concept(concept=concept_pydantic_model)
    fetched_concept = await service.get_concept(concept_pydantic_model.uri)
    assert fetched_concept
    assert fetched_concept.uri == concept_pydantic_model.uri
    assert len(fetched_concept.pref_labels) == 2
    assert len(fetched_concept.alt_labels) == 2
    for preflabel in concept_pydantic_model.pref_labels:
        assert any(
            preflabel.language == fetched_preflabel.language
            and preflabel.value == fetched_preflabel.value
            for fetched_preflabel in fetched_concept.pref_labels
        )
    for altlabel in concept_pydantic_model.alt_labels:
        assert any(
            altlabel.language == fetched_altlabel.language
            and altlabel.value == fetched_altlabel.value
            for fetched_altlabel in fetched_concept.alt_labels
        )


async def test_update_concept_with_uri(persisted_concept_pydantic_model: Concept,
                                       concept_pydantic_model: Concept
                                       ) -> None:
    """
    Given a persisted concept pydantic model
    When the concept is updated with a concept with the same uri, a modified preflabel,
    an additional preflabel in
    another language, a missing altlabel and an additional altlabel
    Then the concept should be returned with the modified labels
    :return:
    """
    assert persisted_concept_pydantic_model.uri == concept_pydantic_model.uri
    service = ConceptService()
    # modify the french preflabel of concept_pydantic_model
    concept_pydantic_model.pref_labels = [
        Literal(
            value='Physique Galactique',
            language='fr'
        ) if pref_label.language == 'fr' else pref_label for pref_label in
        concept_pydantic_model.pref_labels
    ]
    # add a russian preflabel
    concept_pydantic_model.pref_labels.append(
        Literal(
            value='Галактическая физика',
            language='ru'
        )
    )
    # remove the english altlabel
    concept_pydantic_model.alt_labels = [
        alt_label for alt_label in concept_pydantic_model.alt_labels if alt_label.language != 'en'
    ]
    # add a russian altlabel
    concept_pydantic_model.alt_labels.append(
        Literal(
            value='Галактическая астрофизика',
            language='ru'
        )
    )
    await service.create_or_update_concept(concept=concept_pydantic_model)
    fetched_concept = await service.get_concept(concept_pydantic_model.uri)
    assert fetched_concept
    assert fetched_concept.uri == concept_pydantic_model.uri
    assert len(fetched_concept.pref_labels) == 3
    assert len(fetched_concept.alt_labels) == 3
    for preflabel in concept_pydantic_model.pref_labels:
        assert any(
            preflabel.language == fetched_preflabel.language
            and preflabel.value == fetched_preflabel.value
            for fetched_preflabel in fetched_concept.pref_labels
        )
    # the fetched concept should have kept the english altlabel and added the russian altlabel
    for altlabel in concept_pydantic_model.alt_labels:
        assert any(
            altlabel.language == fetched_altlabel.language
            and altlabel.value == fetched_altlabel.value
            for fetched_altlabel in fetched_concept.alt_labels
        )
    # the fetched concept should have kept the english altlabel
    assert any(
        altlabel.language == 'en'
        and altlabel.value == 'Galactic Astrophysics'
        for altlabel in fetched_concept.alt_labels
    )


async def test_create_concept_without_uri(concept_without_uri_pydantic_model) -> None:
    """
    Given a concept pydantic model without uri
    When the concept is created
    Then the concept should be returned correctly
    :return:
    """
    service = ConceptService()
    await service.create_or_update_concept(concept=concept_without_uri_pydantic_model)
    fetched_concept = await service.find_concept_without_uri_by_pref_label(
        concept_without_uri_pydantic_model.pref_labels[0])
    assert fetched_concept
    assert fetched_concept.uri is None
    assert len(fetched_concept.pref_labels) == 1
    assert len(fetched_concept.alt_labels) == 0
    assert fetched_concept.pref_labels[0].value == concept_without_uri_pydantic_model.pref_labels[
        0].value
    assert fetched_concept.pref_labels[0].language == \
           concept_without_uri_pydantic_model.pref_labels[0].language


async def test_update_concept_without_uri(persisted_concept_without_uri_pydantic_model: Concept,
                                          concept_without_uri_pydantic_model: Concept
                                          ) -> None:
    """
    Given a persisted concept pydantic model without uri
    When the concept is updated with a concept with the same preflabel
    Then no other concept should be created and the concept should be returned
    with the initial label

    :param persisted_concept_without_uri_pydantic_model:
    :param concept_without_uri_pydantic_model:
    :return:
    """
    service = ConceptService()
    await service.create_or_update_concept(concept=concept_without_uri_pydantic_model)
    fetched_concept = await service.find_concept_without_uri_by_pref_label(
        concept_without_uri_pydantic_model.pref_labels[0])
    assert fetched_concept
    assert fetched_concept.uri is None
    assert len(fetched_concept.pref_labels) == 1
    assert len(fetched_concept.alt_labels) == 0
    assert fetched_concept.pref_labels[0].value == \
           concept_without_uri_pydantic_model.pref_labels[
               0].value == persisted_concept_without_uri_pydantic_model.pref_labels[0].value
    assert fetched_concept.pref_labels[0].language == \
           concept_without_uri_pydantic_model.pref_labels[0].language == \
           persisted_concept_without_uri_pydantic_model.pref_labels[0].language
