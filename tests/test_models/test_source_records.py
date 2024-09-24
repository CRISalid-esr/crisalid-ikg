from app.models.identifier_types import PublicationIdentifierType
from app.models.source_records import SourceRecord


def test_create_thesis_source_record_from_scanr_data(
        scanr_thesis_source_record_pydantic_model: SourceRecord
):
    """
    Given a source record model representing a thesis harvested from ScanR
    When asked for different field values
    Then the values should be returned correctly
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    assert scanr_thesis_source_record_pydantic_model
    assert len(scanr_thesis_source_record_pydantic_model.titles) == 1
    assert len(scanr_thesis_source_record_pydantic_model.identifiers) == 1
    assert any(
        title for title in scanr_thesis_source_record_pydantic_model.titles if
        title.value == "Understanding Galactic Phenomena through New Data Models"
    )
    assert any(
        identifier for identifier in scanr_thesis_source_record_pydantic_model.identifiers if
        identifier.type == PublicationIdentifierType.NNT and identifier.value == "2023xyz135"
    )
    assert len(scanr_thesis_source_record_pydantic_model.abstracts) == 2
    assert any(
        abstract for abstract in scanr_thesis_source_record_pydantic_model.abstracts if
        abstract.value == "In this research, we investigate the dynamics of galactic structures "
                          "using high-resolution data models. The study focuses on analyzing "
                          "the distribution of matter in the outer regions of galaxies."
    )
    assert any(
        abstract for abstract in scanr_thesis_source_record_pydantic_model.abstracts if
        abstract.value == "Dans cette recherche, nous étudions la dynamique des structures "
                          "galactiques à l'aide de modèles de données haute résolution. "
                          "L'étude se concentre sur l'analyse de la distribution de la matière "
                          "dans les régions externes des galaxies."
    )
    assert len(scanr_thesis_source_record_pydantic_model.subjects) == 2
    assert any(
        subject for subject in scanr_thesis_source_record_pydantic_model.subjects if
        subject.uri == "http://example.org/subject/astronomy"
    )
    assert any(
        subject for subject in scanr_thesis_source_record_pydantic_model.subjects if
        subject.uri == "http://example.org/subject/galactic_physics"
    )
    assert len(scanr_thesis_source_record_pydantic_model.document_type) == 1
    assert any(
        document_type for document_type in scanr_thesis_source_record_pydantic_model.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Thesis"
    )
    assert len(scanr_thesis_source_record_pydantic_model.contributions) == 1
    assert any(
        contribution for contribution in scanr_thesis_source_record_pydantic_model.contributions if
        contribution.rank == 1 and contribution.contributor.name == "Doe, Jane"
        and contribution.contributor.affiliation == "University of Example"
    )
    assert scanr_thesis_source_record_pydantic_model.id is None


def test_create_thesis_source_record_from_idref_data(
        idref_thesis_source_record_pydantic_model: SourceRecord
):
    """
    Given a valid source record model representing a thesis harvested from IdRef
    When asked for different field values
    Then the values should be returned correctly
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    assert idref_thesis_source_record_pydantic_model
    assert len(idref_thesis_source_record_pydantic_model.titles) == 1
    assert len(idref_thesis_source_record_pydantic_model.identifiers) == 1
    assert any(
        title for title in idref_thesis_source_record_pydantic_model.titles if
        title.value == "Études sur les nuages galactiques : turbulence et poussières"
    )
    assert any(
        identifier for identifier in idref_thesis_source_record_pydantic_model.identifiers if
        identifier.type == PublicationIdentifierType.URI
        and identifier.value == "http://www.example.fr/123456789/id"
    )
    assert len(idref_thesis_source_record_pydantic_model.abstracts) == 2
    assert any(
        abstract for abstract in idref_thesis_source_record_pydantic_model.abstracts if
        abstract.value == "English summary (similar)"
    )
    assert any(
        abstract for abstract in idref_thesis_source_record_pydantic_model.abstracts if
        abstract.value == "Résumé français (maximum 1000 caractères)"
    )
    assert len(idref_thesis_source_record_pydantic_model.subjects) == 1
    assert any(
        subject for subject in idref_thesis_source_record_pydantic_model.subjects if
        subject.uri == "http://www.example.fr/subject/123456"
    )
    assert len(idref_thesis_source_record_pydantic_model.document_type) == 2
    assert any(
        document_type for document_type in idref_thesis_source_record_pydantic_model.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Book"
    )
    assert any(
        document_type for document_type in idref_thesis_source_record_pydantic_model.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Thesis"
    )
    assert len(idref_thesis_source_record_pydantic_model.contributions) == 3
    assert any(
        contribution for contribution in idref_thesis_source_record_pydantic_model.contributions if
        contribution.contributor.name == "Doe, John (1980-.... ; astrophysicist)"
    )
    assert any(
        contribution for contribution in idref_thesis_source_record_pydantic_model.contributions if
        contribution.contributor.name == "Smith, Jane (1990-....)"
    )
    assert any(
        contribution for contribution in idref_thesis_source_record_pydantic_model.contributions if
        contribution.contributor.name == "Brown, Alex (1975-....)"
    )
