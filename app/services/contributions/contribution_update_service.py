from collections import defaultdict
from typing import cast, Optional

from loguru import logger

from app.config import get_app_settings
from app.errors.conflict_error import ConflictError
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.person_dao import PersonDAO
from app.models.change_report import ChangeApplicationReport
from app.models.document import Document
from app.models.harvesting_sources import HarvestingSource
from app.models.identifier_types import OrganizationIdentifierType, PersonIdentifierType
from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person
from app.models.source_organization_identifiers import SourceOrganizationIdentifier
from app.models.source_organizations import SourceOrganization
from app.services.authority_organizations.authority_organization_service import \
    AuthorityOrganizationService
from app.services.source_contributors.source_contributor_mapping_service import \
    SourceContributorMappingService
from app.utils.name_matching import fuzz_distance


class ContributionUpdateService:
    """
    Reconcile a document's contributions against the full, authoritative contributor list
    carried by a sovisuplus contribution-update message (replace semantics).

    Contributors present in the list are created/updated, contributors absent from it are
    removed. Person identifiers are frozen for internal people and updatable for external
    people; affiliations are resolved to authority organizations using the existing
    in-memory authority resolution algorithm (no source-layer node is persisted).
    """

    # HAL structure types (message ``type``) → in-memory SourceOrganisationType
    _ORG_TYPE_MAP = {
        "institution": SourceOrganization.SourceOrganisationType.INSTITUTION,
        "regroupinstitution": SourceOrganization.SourceOrganisationType.INSTITUTION_GROUP,
        "laboratory": SourceOrganization.SourceOrganisationType.LABORATORY,
        "regrouplaboratory": SourceOrganization.SourceOrganisationType.LABORATORY_GROUP,
        "researchteam": SourceOrganization.SourceOrganisationType.RESEARCH_TEAM,
        "regroupresearchteam": SourceOrganization.SourceOrganisationType.RESEARCH_TEAM_GROUP,
        "department": SourceOrganization.SourceOrganisationType.DEPARTMENT,
    }

    # Affiliation identifier keys carried inline in the message (besides the HAL structId)
    _AFFILIATION_IDENTIFIER_KEYS = ("idref", "ror", "isni", "nns", "wikidata")

    def __init__(self) -> None:
        self.authority_organization_service = AuthorityOrganizationService()

    async def reconcile(self, document_uid: str,
                        contributions: list[dict]) -> ChangeApplicationReport:
        """
        Reconcile the document's contributions to exactly the submitted list.

        :param document_uid: target document uid
        :param contributions: full ordered contribution list from the message
        :return: application report with one warning per skipped or degraded item
        """
        report = ChangeApplicationReport()
        document_dao = self._document_dao()
        contribution_ids: list[str] = []
        for contribution in contributions:
            person = contribution.get("person") or {}
            warnings_before = len(report.warnings)
            person_uid = await self._resolve_person(person, report)
            if person_uid is None:
                logger.warning("Skipping contribution with unresolvable person: {}", person)
                # a more specific warning may already have been recorded during resolution
                if len(report.warnings) == warnings_before:
                    report.add_warning(
                        "UNRESOLVABLE_PERSON",
                        "Skipping contribution with unresolvable person",
                        display_name=person.get("displayName") or person.get("display_name"),
                        identifiers=self._incoming_identifiers(person),
                    )
                continue
            # a contribution without roles defaults to the generic Contributor role
            roles = contribution.get("roles") or [LocContributionRole.CONTRIBUTOR.value]
            rank = contribution.get("rank")
            contribution_id = await document_dao.create_contribution(
                document_uid=document_uid,
                person_uid=person_uid,
                roles=roles,
                rank=rank,
            )
            if contribution_id is None:
                report.add_warning(
                    "CONTRIBUTION_NOT_CREATED",
                    "Contribution could not be created",
                    person_uid=person_uid,
                )
                continue
            targets = await self._resolve_affiliations(
                contribution.get("affiliations") or [], report)
            await document_dao.update_contribution_affiliation_statements(
                contribution_id=contribution_id,
                targets=targets,
            )
            contribution_ids.append(contribution_id)
        # Safety guard: a non-empty submitted list that resolved to nothing must not wipe
        # every contributor from the document — abort and keep the previous state.
        if contributions and not contribution_ids:
            details = "; ".join(
                f"{warning.code}: {warning.message}" for warning in report.warnings)
            raise ValueError(
                f"None of the {len(contributions)} submitted contributions could be applied "
                f"to document {document_uid}; aborting to avoid removing all contributors"
                f"{f' ({details})' if details else ''}")
        # Remove contributors absent from the submitted list
        await document_dao.delete_contributions_not_in(
            document_uid=document_uid,
            contribution_ids=contribution_ids,
        )
        return report

    # ------------------------------------------------------------------ persons

    async def _resolve_person(
            self, person: dict, report: ChangeApplicationReport) -> Optional[str]:
        """
        Resolve the contribution's person to a graph Person uid, creating a new external
        person when necessary, and applying the internal/external identifier policy.

        An incoming identifier already owned by an existing person through an ``AgentIdentifier``
        is authoritative: the contribution is re-pointed onto that owner (internal owners win
        over external ones) rather than copying the identifier onto a second person and creating
        a shared node.
        """
        uid = person.get("uid")
        incoming_identifiers = self._incoming_identifiers(person)
        display_name = person.get("displayName") or person.get("display_name")

        candidates = await self._person_dao().find_candidates_by_identifiers(incoming_identifiers)

        # Authoritative re-point: a person that owns an incoming identifier via AgentIdentifier.
        owner = self._select_agent_owner(candidates, display_name)
        if owner is not None:
            owner_uid, owner_external = owner
            await self._apply_identifier_policy(
                owner_uid, owner_external, incoming_identifiers,
                self._agent_inconsistent_keys(candidates, owner_uid),
                report=report, display_name=display_name)
            return owner_uid

        if uid:
            existing = await self._person_dao().get(uid)
            if existing is not None:
                await self._apply_identifier_policy(
                    existing.uid, bool(existing.external), incoming_identifiers, set(),
                    report=report, display_name=display_name)
                return existing.uid
            # uid provided but not found: fall back to matching/creation
            logger.info("Person uid {} not found, falling back to identifier matching", uid)

        return await self._match_or_create_person(
            candidates, incoming_identifiers, display_name, report)

    async def _match_or_create_person(
            self, candidates: list[dict], incoming_identifiers: list[dict],
            display_name: Optional[str], report: ChangeApplicationReport
    ) -> Optional[str]:
        """
        Match the person against source-identifier candidates (AgentIdentifier owners are
        handled earlier by re-pointing), else create a new external person.
        """
        persons: dict[str, dict] = {}
        id_to_persons: dict[tuple, set] = defaultdict(set)
        for row in candidates:
            persons[row["person_uid"]] = {
                "external": row.get("external"),
                "display_name": row.get("display_name"),
            }
            id_to_persons[(row["id_type"], row["id_value"])].add(row["person_uid"])

        distinct = list(persons.keys())
        if not distinct:
            return await self._create_external_person(
                incoming_identifiers, display_name, report)

        if len(distinct) == 1:
            selected = distinct[0]
        else:
            selected = self._select_by_name_similarity(distinct, persons, display_name)

        await self._apply_identifier_policy(
            selected, bool(persons[selected]["external"]), incoming_identifiers,
            self._inconsistent_identifier_keys(id_to_persons, selected),
            report=report, display_name=display_name)
        return selected

    @classmethod
    def _select_agent_owner(
            cls, candidates: list[dict], submitted_name: Optional[str]
    ) -> Optional[tuple]:
        """
        Among the candidates that own an incoming identifier through an ``AgentIdentifier``,
        pick the one to re-point onto: internal persons take precedence over external ones,
        ties broken by name similarity. Returns ``(uid, external)`` or ``None`` when no
        candidate owns an incoming identifier via an AgentIdentifier.
        """
        agent_persons: dict[str, dict] = {}
        for row in candidates:
            if row.get("via") != "agent":
                continue
            agent_persons[row["person_uid"]] = {
                "external": bool(row.get("external")),
                "display_name": row.get("display_name"),
            }
        if not agent_persons:
            return None
        internal = [uid for uid, data in agent_persons.items() if not data["external"]]
        pool = internal or list(agent_persons.keys())
        if len(pool) == 1:
            selected = pool[0]
        else:
            selected = cls._select_by_name_similarity(pool, agent_persons, submitted_name)
        return selected, agent_persons[selected]["external"]

    @classmethod
    def _agent_inconsistent_keys(cls, candidates: list[dict], selected: str) -> set:
        """
        AgentIdentifier (type, value) keys owned by a person other than the selected one; these
        must not be written onto the selected person.
        """
        id_to_persons: dict[tuple, set] = defaultdict(set)
        for row in candidates:
            if row.get("via") != "agent":
                continue
            id_to_persons[(row["id_type"], row["id_value"])].add(row["person_uid"])
        return cls._inconsistent_identifier_keys(id_to_persons, selected)

    @staticmethod
    def _inconsistent_identifier_keys(id_to_persons: dict[tuple, set], selected: str) -> set:
        """
        Identifier (type, value) keys that point to a person other than the selected one and
        must therefore not be written onto the selected person.
        """
        return {key for key, owners in id_to_persons.items() if owners - {selected}}

    async def _apply_identifier_policy(  # pylint: disable=too-many-arguments
            self,
            person_uid: str,
            external: bool,
            incoming_identifiers: list[dict],
            inconsistent_keys: set,
            *,
            report: ChangeApplicationReport,
            display_name: Optional[str],
    ) -> None:
        """
        Internal people: identifiers are frozen (incoming identifiers ignored).
        External people: add the consistent and valid incoming identifiers
        (MERGE, names untouched).
        """
        if not external:
            return
        consistent = [
            identifier for identifier in incoming_identifiers
            if (identifier["type"], identifier["value"]) not in inconsistent_keys
        ]
        consistent = self._validate_identifiers(consistent, report, display_name)
        await self._person_dao().add_person_identifiers(person_uid, consistent)

    @staticmethod
    def _validate_identifiers(
            identifiers: list[dict], report: ChangeApplicationReport,
            display_name: Optional[str]
    ) -> list[dict]:
        """
        Keep only identifiers whose type is known and whose value matches the type-specific
        pattern; each dropped identifier is reported — the Person model validators would
        otherwise discard it silently and the DAO would persist it unchecked.
        """
        valid = []
        for identifier in identifiers:
            identifier_type = PersonIdentifierType.from_str(identifier["type"])
            value = str(identifier["value"])
            if identifier_type is None or not PersonIdentifierType.validate_identifier(
                    identifier_type, value):
                logger.warning("Invalid person identifier ignored: {}", identifier)
                report.add_warning(
                    "INVALID_IDENTIFIER",
                    "Invalid person identifier ignored",
                    type=identifier["type"],
                    value=identifier["value"],
                    display_name=display_name,
                )
                continue
            valid.append({"type": identifier["type"], "value": value})
        return valid

    @staticmethod
    def _select_by_name_similarity(
            uids: list[str], persons: dict[str, dict], submitted_name: Optional[str]
    ) -> str:
        if not submitted_name:
            return uids[0]
        best_uid = uids[0]
        best_score = -1.0
        for uid in uids:
            score = fuzz_distance(submitted_name, persons[uid]["display_name"] or "")
            if score > best_score:
                best_score = score
                best_uid = uid
        return best_uid

    async def _create_external_person(
            self, incoming_identifiers: list[dict], display_name: Optional[str],
            report: ChangeApplicationReport
    ) -> Optional[str]:
        incoming_identifiers = self._validate_identifiers(
            incoming_identifiers, report, display_name)
        if not display_name:
            logger.warning("Cannot create external person without a display name")
            report.add_warning(
                "MISSING_DISPLAY_NAME",
                "Cannot create external person without a display name",
                identifiers=incoming_identifiers,
            )
            return None
        person = Person(
            uid=None,
            display_name=display_name,
            external=True,
            identifiers=incoming_identifiers,
        )
        try:
            person_uid, _, _ = await self._person_dao().create(person)
            return person_uid
        except (ConflictError, ValueError) as error:
            logger.error("Could not create external person {}: {}", display_name, error)
            report.add_warning(
                "EXTERNAL_PERSON_CREATION_FAILED",
                "Could not create external person",
                display_name=display_name,
                error=str(error),
            )
            return None

    @staticmethod
    def _incoming_identifiers(person: dict) -> list[dict]:
        identifiers = person.get("identifiers") or []
        return [
            {"type": identifier["type"], "value": identifier["value"]}
            for identifier in identifiers
            if identifier.get("type") and identifier.get("value")
        ]

    # ------------------------------------------------------------- affiliations

    async def _resolve_affiliations(
            self, affiliations: list[dict], report: ChangeApplicationReport) -> list[str]:
        """
        Resolve message affiliations to elected authority-organization target uids, reusing
        the existing in-memory authority resolution (no SourceOrganization node persisted).
        """
        source_organisations = [
            org for org in (self._build_source_organization(aff, report)
                            for aff in affiliations)
            if org is not None
        ]
        if not source_organisations:
            return []

        root_objects = []
        seen: set = set()
        for organisation in source_organisations:
            if organisation.uid in seen:
                continue
            seen.add(organisation.uid)
            try:
                root = await self.authority_organization_service\
                    .get_or_create_authority_organization(
                        [organisation],
                        # a recognized type was chosen by the user: it overrides the
                        # state's type and is protected from harvest overwrite
                        type_authoritative=organisation.type
                        != SourceOrganization.SourceOrganisationType.ORGANIZATION)
                root_objects.append(root)
            except ConflictError as error:
                logger.error(
                    "Conflict error while resolving affiliation {}: {}", organisation.uid, error)
                report.add_warning(
                    "AFFILIATION_CONFLICT",
                    "Conflict error while resolving affiliation",
                    source_organization_uid=organisation.uid,
                    error=str(error),
                )

        # pylint: disable=protected-access
        return SourceContributorMappingService\
            ._elect_authority_organizations_for_affiliation_statements(
                root_objects, source_organisations)

    def _build_source_organization(
            self, affiliation: dict,
            report: ChangeApplicationReport) -> Optional[SourceOrganization]:
        source_identifier = affiliation.get("hal")
        if not source_identifier:
            # affiliations are normally HAL-sourced; fall back to any other identifier
            for key in self._AFFILIATION_IDENTIFIER_KEYS:
                if affiliation.get(key):
                    source_identifier = affiliation.get(key)
                    break
        if not source_identifier:
            logger.warning("Affiliation without usable identifier skipped: {}", affiliation)
            report.add_warning(
                "AFFILIATION_WITHOUT_IDENTIFIER",
                "Affiliation without usable identifier skipped",
                affiliation=affiliation,
            )
            return None

        identifiers = []
        # The HAL structId is both the source key and a genuine identifier: record it as a
        # ``hal`` identifier so the resolved authority is identified and converges (by identifier)
        # on the harvested authority keyed on the same structId.
        if affiliation.get("hal"):
            identifiers.append(SourceOrganizationIdentifier(
                type=OrganizationIdentifierType.HAL.value, value=str(affiliation["hal"])))
        identifiers += [
            SourceOrganizationIdentifier(type=key, value=affiliation[key])
            for key in self._AFFILIATION_IDENTIFIER_KEYS
            if affiliation.get(key)
        ]
        return SourceOrganization(
            source=HarvestingSource.HAL,
            source_identifier=str(source_identifier),
            name=affiliation.get("name") or affiliation.get("label") or "",
            type=self._resolve_affiliation_type(affiliation, report),
            identifiers=identifiers,
        )

    def _resolve_affiliation_type(
            self, affiliation: dict,
            report: ChangeApplicationReport) -> SourceOrganization.SourceOrganisationType:
        """
        Map the message's HAL structure type; a missing type is the generic placeholder,
        an unknown value is reported and treated the same way.
        """
        raw_type = affiliation.get("type")
        if not raw_type:
            return SourceOrganization.SourceOrganisationType.ORGANIZATION
        org_type = self._ORG_TYPE_MAP.get(raw_type)
        if org_type is None:
            logger.warning("Unknown affiliation type {} ignored: {}", raw_type, affiliation)
            report.add_warning(
                "AFFILIATION_TYPE_UNKNOWN",
                "Unknown affiliation type ignored",
                type=raw_type,
                affiliation=affiliation,
            )
            return SourceOrganization.SourceOrganisationType.ORGANIZATION
        return org_type

    # --------------------------------------------------------------------- daos

    def _document_dao(self) -> DocumentDAO:
        return cast(DocumentDAO, self._get_dao_factory().get_dao(Document))

    def _person_dao(self) -> PersonDAO:
        return cast(PersonDAO, self._get_dao_factory().get_dao(Person))

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
