"""
Scenario fixtures dedicated to manual identifier edition (addition / removal).

The graph shapes mirror the production instance (scanr/hal/idref harvests,
idref-keyed scanr source people, external co-authors aligned with idref/orcid
AgentIdentifiers, legacy HARVESTED_FOR edges without identifier_used properties),
with anonymised people, organizations and publications.
"""
from types import SimpleNamespace

import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.person_dao import PersonDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.document import Document
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person
from app.services.people.people_service import PeopleService
from app.services.source_records.source_record_service import SourceRecordService
from tests.fixtures.common import _source_record_from_json_data

AUTHOR_ROLE = "https://id.loc.gov/vocabulary/relators/aut.html"

CLAIRE_UID = "local-cfontaine@univ-domain.edu"
CLAIRE_IDREF = "100200309"
CLAIRE_ORCID = "0000-0002-1111-2222"
CLAIRE_IDHALS = "claire-fontaine"
RACHID_UID = "local-rbenali@univ-domain.edu"
RACHID_IDREF = "200300408"
NADIA_UID = "local-nroux@univ-domain.edu"
NADIA_IDREF = "400500609"
PIERRE_UID = "local-pvasseur@univ-domain.edu"
PIERRE_IDREF = "600700801"
PIERRE_ORCID = "0000-0003-3333-4444"

SP_CLAIRE_SCANR_UID = f"scanr-idref{CLAIRE_IDREF}"
SP_CLAIRE_HAL_UID = "hal-777001"
SP_RACHID_HAL_UID = "hal-777002"
SP_EVA_UID = "scanr-idref300400507"
SP_MARTA_UID = "idref-http://www.idref.fr/500600708/id"
SP_PIERRE_UID = f"scanr-idref{PIERRE_IDREF}"

VALOMBRE_ORG = {
    "source": "scanr",
    "source_identifier": "scanr_idref_900000001",
    "name": "Université de Valombre",
    "type": "institution",
    "identifiers": [
        {"type": "idref", "value": "900000001"},
        {"type": "ror", "value": "https://ror.org/00valombre"}
    ]
}

CAHIERS_ISSUE = {
    "source": "scanr",
    "source_identifier": "cahiers_histoire_sociale-ScanR",
    "titles": [],
    "volume": "12",
    "number": [],
    "rights": None,
    "date": None,
    "journal": {
        "source": "scanr",
        "source_identifier": "1234-5678-cahiers_histoire_sociale-ScanR",
        "issn": ["1234-5678"],
        "eissn": [],
        "issn_l": None,
        "publisher": "Presses de Valombre",
        "titles": ["Cahiers d'Histoire Sociale"]
    }
}


def _person_json(last_name: str, first_name: str, local_value: str,
                 extra_identifiers: list[dict]) -> dict:
    return {
        "names": [{
            "last_names": [{"value": last_name, "language": "fr"}],
            "first_names": [{"value": first_name, "language": "fr"}]
        }],
        "identifiers": [{"type": "local", "value": local_value}] + extra_identifiers,
        "memberships": []
    }


def _contribution(rank: int, source: str, name: str, source_identifier: str | None,
                  identifiers: list[dict] | None = None,
                  affiliations: list[dict] | None = None,
                  first_name: str | None = None, last_name: str | None = None) -> dict:
    return {
        "rank": rank,
        "contributor": {
            "source": source,
            "source_identifier": source_identifier,
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "name_variants": [],
            "identifiers": identifiers or []
        },
        "role": AUTHOR_ROLE,
        "affiliations": affiliations or []
    }


def _source_record_json(harvester: str, source_identifier: str, title: str,
                        identifiers: list[dict], contributions: list[dict],
                        document_type: str = "Article", issue: dict | None = None) -> dict:
    return {
        "source_identifier": source_identifier,
        "harvester": harvester,
        "harvester_version": "1.2.0",
        "identifiers": identifiers,
        "manifestations": [],
        "titles": [{"value": title, "language": "fr"}],
        "subtitles": [],
        "abstracts": [],
        "subjects": [],
        "document_type": [{"uri": f"http://purl.org/ontology/bibo/{document_type}",
                           "label": document_type}],
        "contributions": contributions,
        "issue": issue,
        "page": None,
        "book": None,
        "issued": None,
        "created": None,
        "version": 0
    }


async def _run_write_query(query: str, **params):
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            await session.run(query, **params)


def _document_dao() -> DocumentDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return factory.get_dao(Document)


def _inject_mocked_exchange(test_app, mocked_exchange):
    test_app.amqp_interface.pika_exchanges[
        get_app_settings().amqp_graph_exchange_name] = mocked_exchange


@pytest_asyncio.fixture(name="identifier_removal_scenario")
async def fixture_identifier_removal_scenario(test_app, mocked_exchange) -> SimpleNamespace:
    """
    Removal scenario: an internal researcher (Claire) with idref, orcid and idhals
    identifiers, whose idref triggered several harvests:

    - ``rec_exclusive`` (scanr article, journal, external co-author with affiliation):
      harvested exclusively for Claire through her idref;
    - ``rec_shared`` (hal chapter, co-authored with internal Rachid): harvested for
      Claire through her idref and owned by Rachid through a legacy HARVESTED_FOR
      edge without identifier_used properties (as found in the production graph);
    - ``rec_sp_shared`` (scanr thesis, same scanr SourcePerson as rec_exclusive):
      harvested for Claire through her orcid;
    - ``rec_no_recorded_by`` (idref thesis, Claire absent from the contributors):
      harvested exclusively for Claire through her idref — the harvesting path
      without the final RECORDED_BY relationship.
    """
    _inject_mocked_exchange(test_app, mocked_exchange)
    people_service = PeopleService()
    claire = Person(**_person_json("Fontaine", "Claire", "cfontaine@univ-domain.edu", [
        {"type": "idref", "value": CLAIRE_IDREF},
        {"type": "orcid", "value": CLAIRE_ORCID},
        {"type": "idhals", "value": CLAIRE_IDHALS}
    ]))
    await people_service.create_person(claire)
    rachid = Person(**_person_json("Benali", "Rachid", "rbenali@univ-domain.edu", [
        {"type": "idref", "value": RACHID_IDREF}
    ]))
    await people_service.create_person(rachid)

    claire_idref = PersonIdentifier(type=PersonIdentifierType.IDREF, value=CLAIRE_IDREF)
    claire_orcid = PersonIdentifier(type=PersonIdentifierType.ORCID, value=CLAIRE_ORCID)
    source_record_service = SourceRecordService()

    rec_exclusive = _source_record_from_json_data(_source_record_json(
        "scanr", "halhal-01000001",
        "Poussières et mémoire ouvrière dans la vallée de Valombre",
        [{"type": "doi", "value": "10.9000/valombre.0001"}],
        [
            _contribution(0, "scanr", "Fontaine, Claire", f"idref{CLAIRE_IDREF}",
                          identifiers=[{"type": "idref", "value": CLAIRE_IDREF}]),
            _contribution(1, "scanr", "Kovács, Éva", "idref300400507",
                          identifiers=[{"type": "idref", "value": "300400507"}],
                          affiliations=[VALOMBRE_ORG])
        ],
        issue=CAHIERS_ISSUE))
    await source_record_service.create_source_record(
        source_record=rec_exclusive, harvested_for=claire, identifier_used=claire_idref)

    rec_shared = _source_record_from_json_data(_source_record_json(
        "hal", "hal-04000002",
        "Archives orales des houillères : un chapitre de méthode",
        [{"type": "hal", "value": "hal-04000002"}],
        [
            _contribution(0, "hal", "Claire Fontaine", "777001",
                          identifiers=[{"type": "idhali", "value": "777001"}],
                          first_name="Claire", last_name="Fontaine"),
            _contribution(1, "hal", "Rachid Benali", "777002",
                          identifiers=[{"type": "idref", "value": RACHID_IDREF}],
                          first_name="Rachid", last_name="Benali")
        ],
        document_type="Chapter"))
    await source_record_service.create_source_record(
        source_record=rec_shared, harvested_for=claire, identifier_used=claire_idref)
    # legacy co-ownership: HARVESTED_FOR edge without identifier_used properties,
    # as observed on the production graph
    await _run_write_query(
        "MATCH (s:SourceRecord {uid: $source_record_uid}) "
        "MATCH (p:Person {uid: $person_uid}) "
        "MERGE (s)-[:HARVESTED_FOR]->(p)",
        source_record_uid=rec_shared.uid, person_uid=RACHID_UID)

    rec_sp_shared = _source_record_from_json_data(_source_record_json(
        "scanr", "nnt2021valx042",
        "Mineurs et médecins : la silicose devant les commissions (1935-1965)",
        [{"type": "nnt", "value": "2021valx042"}],
        [
            _contribution(0, "scanr", "Fontaine, Claire", f"idref{CLAIRE_IDREF}",
                          identifiers=[{"type": "idref", "value": CLAIRE_IDREF}])
        ],
        document_type="Thesis"))
    await source_record_service.create_source_record(
        source_record=rec_sp_shared, harvested_for=claire, identifier_used=claire_orcid)

    rec_no_recorded_by = _source_record_from_json_data(_source_record_json(
        "idref", "http://www.idref.fr/900800701/id",
        "Le charbon et la plume : correspondances d'ingénieurs (1890-1914)",
        [{"type": "nnt", "value": "2019valx777"}],
        [
            _contribution(0, "idref", "Marta Silva", "http://www.idref.fr/500600708/id",
                          identifiers=[{"type": "idref", "value": "500600708"}],
                          first_name="Marta", last_name="Silva")
        ],
        document_type="Thesis"))
    await source_record_service.create_source_record(
        source_record=rec_no_recorded_by, harvested_for=claire, identifier_used=claire_idref)

    document_dao = _document_dao()
    documents = {}
    for name, record in [("rec_exclusive", rec_exclusive), ("rec_shared", rec_shared),
                         ("rec_sp_shared", rec_sp_shared),
                         ("rec_no_recorded_by", rec_no_recorded_by)]:
        document = await document_dao.get_document_by_source_record_uid(record.uid)
        documents[name] = document.uid if document else None

    return SimpleNamespace(
        claire=claire,
        rachid=rachid,
        rec_exclusive_uid=rec_exclusive.uid,
        rec_shared_uid=rec_shared.uid,
        rec_sp_shared_uid=rec_sp_shared.uid,
        rec_no_recorded_by_uid=rec_no_recorded_by.uid,
        document_uids=documents
    )


@pytest_asyncio.fixture(name="identifier_collision_scenario")
async def fixture_identifier_collision_scenario(test_app, mocked_exchange) -> SimpleNamespace:
    """
    Addition/collision scenario: a record harvested for internal Nadia carries a
    co-author (Pierre Vasseur) whose scanr SourcePerson holds idref and orcid
    identifiers. The pipeline creates an external person for him, contributing to
    the resulting document; a sovisuplus author alignment then attaches the idref
    and orcid AgentIdentifiers to that external person. Meanwhile the same Pierre
    Vasseur exists as a (newly recruited) internal person with only a local
    identifier.
    """
    _inject_mocked_exchange(test_app, mocked_exchange)
    people_service = PeopleService()
    nadia = Person(**_person_json("Roux", "Nadia", "nroux@univ-domain.edu", [
        {"type": "idref", "value": NADIA_IDREF}
    ]))
    await people_service.create_person(nadia)
    pierre = Person(**_person_json("Vasseur", "Pierre", "pvasseur@univ-domain.edu", []))
    await people_service.create_person(pierre)

    nadia_idref = PersonIdentifier(type=PersonIdentifierType.IDREF, value=NADIA_IDREF)
    source_record_service = SourceRecordService()
    rec_coauthored = _source_record_from_json_data(_source_record_json(
        "scanr", "halhal-02000001",
        "Cartographier les solidarités minières : une approche croisée",
        [{"type": "doi", "value": "10.9000/valombre.0002"}],
        [
            _contribution(0, "scanr", "Roux, Nadia", f"idref{NADIA_IDREF}",
                          identifiers=[{"type": "idref", "value": NADIA_IDREF}]),
            _contribution(1, "scanr", "Vasseur, Pierre", f"idref{PIERRE_IDREF}",
                          identifiers=[{"type": "idref", "value": PIERRE_IDREF},
                                       {"type": "orcid", "value": PIERRE_ORCID}])
        ]))
    await source_record_service.create_source_record(
        source_record=rec_coauthored, harvested_for=nadia, identifier_used=nadia_idref)

    # sovisuplus author alignment: the external person gets the co-author identifiers
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    person_dao: PersonDAO = factory.get_dao(Person)
    await person_dao.add_person_identifiers(SP_PIERRE_UID, [
        {"type": "idref", "value": PIERRE_IDREF},
        {"type": "orcid", "value": PIERRE_ORCID}
    ])

    document = await _document_dao().get_document_by_source_record_uid(rec_coauthored.uid)

    return SimpleNamespace(
        nadia=nadia,
        pierre=pierre,
        external_pierre_uid=SP_PIERRE_UID,
        rec_coauthored_uid=rec_coauthored.uid,
        document_uid=document.uid if document else None
    )
