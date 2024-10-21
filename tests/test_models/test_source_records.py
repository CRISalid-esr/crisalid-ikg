from app.models.identifier_types import PublicationIdentifierType, JournalIdentifierType
from app.models.source_records import SourceRecord


def test_create_thesis_source_record_from_scanr_data(
        scanr_thesis_source_record_json_data: dict
):
    """
    Given a source record model representing a thesis harvested from ScanR
    When asked for different field values
    Then the values should be returned correctly
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    source_record = SourceRecord(**scanr_thesis_source_record_json_data)
    assert source_record
    assert len(source_record.titles) == 1
    assert len(source_record.identifiers) == 1
    assert any(
        title for title in source_record.titles if
        title.value == "Understanding Galactic Phenomena through New Data Models"
    )
    assert any(
        identifier for identifier in source_record.identifiers if
        identifier.type == PublicationIdentifierType.NNT and identifier.value == "2023xyz135"
    )
    assert len(source_record.abstracts) == 2
    assert any(
        abstract for abstract in source_record.abstracts if
        abstract.value == "In this research, we investigate the dynamics of galactic structures "
                          "using high-resolution data models. The study focuses on analyzing "
                          "the distribution of matter in the outer regions of galaxies."
    )
    assert any(
        abstract for abstract in source_record.abstracts if
        abstract.value == "Dans cette recherche, nous étudions la dynamique des structures "
                          "galactiques à l'aide de modèles de données haute résolution. "
                          "L'étude se concentre sur l'analyse de la distribution de la matière "
                          "dans les régions externes des galaxies."
    )
    assert len(source_record.subjects) == 2
    assert any(
        subject for subject in source_record.subjects if
        subject.uri == "http://example.org/subject/astronomy"
    )
    assert any(
        subject for subject in source_record.subjects if
        subject.uri == "http://example.org/subject/galactic_physics"
    )
    assert len(source_record.document_type) == 1
    assert any(
        document_type for document_type in source_record.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Thesis"
    )
    assert len(source_record.contributions) == 1
    assert any(
        contribution for contribution in source_record.contributions if
        contribution.rank == 1 and contribution.contributor.name == "Doe, Jane"
        and contribution.contributor.affiliation == "University of Example"
    )


def test_create_thesis_source_record_from_idref_data(
        idref_thesis_source_record_json_data: dict
):
    """
    Given a valid source record model representing a thesis harvested from IdRef
    When asked for different field values
    Then the values should be returned correctly
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    source_record = SourceRecord(**idref_thesis_source_record_json_data)
    assert source_record
    assert len(source_record.titles) == 1
    assert len(source_record.identifiers) == 1
    assert any(
        title for title in source_record.titles if
        title.value == "Études sur les nuages galactiques : turbulence et poussières"
    )
    assert any(
        identifier for identifier in source_record.identifiers if
        identifier.type == PublicationIdentifierType.URI
        and identifier.value == "http://www.example.fr/123456789/id"
    )
    assert len(source_record.abstracts) == 2
    assert any(
        abstract for abstract in source_record.abstracts if
        abstract.value == "English summary (similar)"
    )
    assert any(
        abstract for abstract in source_record.abstracts if
        abstract.value == "Résumé français (maximum 1000 caractères)"
    )
    assert len(source_record.subjects) == 1
    assert any(
        subject for subject in source_record.subjects if
        subject.uri == "http://www.example.fr/subject/123456"
    )
    assert len(source_record.document_type) == 2
    assert any(
        document_type for document_type in source_record.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Book"
    )
    assert any(
        document_type for document_type in source_record.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Thesis"
    )
    assert len(source_record.contributions) == 3
    assert any(
        contribution for contribution in source_record.contributions if
        contribution.contributor.name == "Doe, John (1980-.... ; astrophysicist)"
    )
    assert any(
        contribution for contribution in source_record.contributions if
        contribution.contributor.name == "Smith, Jane (1990-....)"
    )
    assert any(
        contribution for contribution in source_record.contributions if
        contribution.contributor.name == "Brown, Alex (1975-....)"
    )


async def test_create_article_source_record_from_open_alex_data(
        open_alex_article_source_record_json_data: dict
):
    """
    Given a valid source record model representing an article harvested from OpenAlex
    When asked for different field values
    Then the values should be returned correctly
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    source_record = SourceRecord(**open_alex_article_source_record_json_data)
    assert source_record
    assert source_record.harvester == "OpenAlex"
    assert source_record.source_identifier == "https://openalex.org/W123456789"
    assert len(source_record.titles) == 1
    assert len(source_record.identifiers) == 2
    assert any(
        title for title in source_record.titles if
        title.value == "Sample Title: Anonymized Study on Historical Artifacts"
    )
    assert any(
        identifier for identifier in source_record.identifiers if
        identifier.type == PublicationIdentifierType.DOI
        and identifier.value == "https://doi.org/10.12345/bch.0000.00000"
    )
    assert any(
        identifier for identifier in source_record.identifiers if
        identifier.type == PublicationIdentifierType.OPENALEX
        and identifier.value == "https://openalex.org/W123456789"
    )
    assert len(source_record.abstracts) == 1
    assert any(
        abstract for abstract in source_record.abstracts if
        abstract.value == "This is an abstract of the article."
    )
    assert len(source_record.subjects) == 1
    assert any(
        subject for subject in source_record.subjects if
        subject.uri == "http://www.example.org/entity/123"
    )
    assert len(source_record.document_type) == 1
    assert any(
        document_type for document_type in source_record.document_type
        if
        document_type.uri == "http://purl.org/ontology/bibo/Article"
    )
    assert len(source_record.contributions) == 1
    assert any(
        contribution for contribution in source_record.contributions if
        contribution.rank == 1 and contribution.contributor.name == "John Doe"
    )
    assert source_record.issue
    assert source_record.issue.source == "ExampleSource"
    assert source_record.issue.source_identifier == "journal-issue-identifier"
    assert source_record.issue.titles == []
    assert source_record.issue.volume == "105"
    assert source_record.issue.number == ["2"]
    assert source_record.issue.rights is None
    assert source_record.issue.date is None
    assert source_record.issue.journal.source == "OpenAlex"
    assert source_record.issue.journal.source_identifier == "https://openalex.org/S113942516"
    assert source_record.issue.journal.publisher == "Example Publisher"
    assert source_record.issue.journal.titles == ["Sample Journal Title"]
    assert source_record.issue.journal.uid == "openalex-https://openalex.org/S113942516"


async def test_article_identifiers_from_open_alex_data(
        open_alex_article_source_record_json_data: dict
):
    """
    Given a valid source record model representing an article harvested from OpenAlex
    When asked for identifiers
    Then the values should be returned correctly
    :param open_alex_article_source_record_json_data:
    :return:
    """
    source_record = SourceRecord(**open_alex_article_source_record_json_data)
    assert source_record
    assert len(source_record.issue.journal.identifiers) == 3
    assert any(
        identifier for identifier in source_record.issue.journal.identifiers if
        identifier.type == JournalIdentifierType.ISSN and identifier.value == "0007-4217"
    )
    assert any(
        identifier for identifier in source_record.issue.journal.identifiers if
        identifier.type == JournalIdentifierType.ISSN and identifier.value == "2241-0104"
    )
    assert any(
        identifier for identifier in source_record.issue.journal.identifiers if
        identifier.type == JournalIdentifierType.EISSN and identifier.value == "1234-5678"
    )
