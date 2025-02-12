import re
import unicodedata
from typing import cast, AsyncGenerator, List
from venv import logger

from rapidfuzz import fuzz

from app.config import get_app_settings
from app.errors.conflict_error import ConflictError
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.person_dao import PersonDAO
from app.graph.neo4j.source_person_dao import SourcePersonDAO
from app.models.document import Document
from app.models.literal import Literal
from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person
from app.models.people_names import PersonName
from app.models.source_contributions import SourceContribution
from app.models.source_people import SourcePerson
from app.models.source_records import SourceRecord


class SourceContributorMappingService:
    """
    Service to handle operations on source journals data
    """

    def __init__(self, source_records: List[SourceRecord], document_uid: str):
        self.settings = get_app_settings()
        self.source_records = source_records
        self.document_uid = document_uid
        self.contributions: List[SourceContribution] = [contribution for source_record in
                                                        self.source_records for contribution
                                                        in
                                                        source_record.contributions]
        self.source_people: List[SourcePerson] = self._get_source_people(self.source_records)
        self.person_dao = self._get_person_dao()
        self.source_person_dao = self._get_source_person_dao()

    async def update_contributions(self) -> None:
        """
        Recompute metadata for a document
        :return: None
        """
        # create the equivalence relationships between contributors
        await self._create_contextual_equivalences()
        # link the source people to the real people
        linked_people = await self._link_source_people_to_people()
        # update the contributions of the document
        await self._update_contributions(linked_people)

    async def _create_contextual_equivalences(self):
        source_people_by_source_platform = self._sort_source_people_by_source_platform(
            self.source_people)
        # if there is less than 2 source platforms, there is no need to compute distances
        number_of_layers = len(source_people_by_source_platform)
        if number_of_layers < 2:
            return
        distances = self._compute_equivalence_distances(source_people_by_source_platform)
        source_person_uids = [
            source_person.uid for source_person in self.source_people
        ]
        paths = await self.source_person_dao.create_source_people_clusters(
            source_people_uids=source_person_uids,
            distances=distances,
            document_uid=self.document_uid,
            number_of_layers=number_of_layers)
        filtered_paths = self.filter_unique_paths(paths)
        couples = self.convert_paths_to_couples(filtered_paths)
        await self.source_person_dao.create_contextual_equivalents(
            source_people_couples=couples,
            document_uid=self.document_uid)

    async def _link_source_people_to_people(self) -> dict[
        str, [list[SourcePerson]]]:
        """
        Link source people to real people based on identifiers and names
        :return: a dictionary of found people with their corresponding source people
        """
        yet_processed_source_person_uids = set()
        linked_people: dict[str, [list[SourcePerson]]] = {}
        for source_person in self.source_people:
            source_person_uid = source_person.uid
            if source_person_uid in yet_processed_source_person_uids:
                continue
            source_people_cluster_uids = await self.source_person_dao.get_equivalents(
                source_person_uid)
            # append the source person uid to the cluster if it is not already in the cluster
            source_people_cluster_uids = list(set(source_people_cluster_uids + [source_person_uid]))
            source_people_cluster = [person for person in self.source_people if
                                     person.uid in source_people_cluster_uids]
            yet_processed_source_person_uids.update(source_people_cluster_uids)
            person_uid = (
                    await self._match_by_identifiers(source_people_cluster)
                    or await self._match_by_name(source_people_cluster)
                    or await self._match_with_external_person(source_people_cluster)
            )
            if person_uid is not None:
                linked_people[person_uid] = source_people_cluster
        return linked_people

    async def _match_by_name(self, source_people_cluster: List[SourcePerson]) -> str | None:
        """
        Match source people to real people based on names.
        :param source_people_cluster: List of SourcePerson objects.
        :return: The UID of the matched person, or None if no match is found.
        """
        async for harvested_for_person in self._fetch_harvested_for_people(self.person_dao,
                                                                           self.source_records):

            if self._is_similar(harvested_for_person, source_people_cluster):
                await self.source_person_dao.link_to_person([source_person.uid for
                                                             source_person in
                                                             source_people_cluster],
                                                            harvested_for_person.uid)
                return harvested_for_person.uid
        return None

    async def _match_by_identifiers(self, source_people_cluster: List[SourcePerson]) -> str:
        """
        Match source people to real people based on identifiers.

        :param source_people_cluster:
        :return:
        """
        person_uid = None
        identifiers = [identifier.model_dump() for person in source_people_cluster
                       for identifier in person.identifiers]
        if identifiers:
            person_uid = await self.person_dao.find_by_identifiers(identifiers)
            if person_uid:
                await self.source_person_dao.link_to_person([source_person.uid for
                                                             source_person in
                                                             source_people_cluster],
                                                            person_uid)
        return person_uid

    async def _match_with_external_person(self, source_people_cluster: List[SourcePerson]) -> str:
        existing_external_people_uids = set()
        for source_person in source_people_cluster:
            external_person_uid = await self.person_dao.get_person_uid_by_source_person_uid(
                source_person_uid=source_person.uid)
            if external_person_uid:
                existing_external_people_uids.add(external_person_uid)
        if len(existing_external_people_uids) == 0:
            external_person: Person = self._build_external_person(source_people_cluster)
            try:
                person_uid, _, _ = await self.person_dao.create(external_person)
            except ConflictError:
                logger.error("External person %s already exists", external_person)
                person_uid = external_person.uid
            existing_external_people_uids.add(person_uid)
        if len(existing_external_people_uids) == 1:
            external_person_uid = existing_external_people_uids.pop()
            await self.source_person_dao.link_to_person([source_person.uid for
                                                         source_person in
                                                         source_people_cluster],
                                                        external_person_uid)
            return external_person_uid
        # the more complex case where there are multiple existing external people
        # we need to merge them
        return await self._merge_external_people(existing_external_people_uids,
                                                 source_people_cluster)

    def _build_external_person(self, source_people_cluster):
        external_person_data = {
            'uid': None,
            'display_name': None,
            'display_name_variants': [],
            "names": [],
            "identifiers": [],
            "external": True
        }
        source_people_cluster = sorted(
            source_people_cluster,
            key=lambda person: self._get_harvesters().index(person.source)
            if person.source in self._get_harvesters() else float('inf')
        )
        for source_person in source_people_cluster:
            if external_person_data['uid'] is None:
                external_person_data['uid'] = source_person.uid
            if external_person_data['display_name'] is None:
                external_person_data['display_name'] = source_person.name
                if source_person.last_name and source_person.first_name:
                    external_person_data['names'] = [PersonName(
                        first_names=[Literal(value=source_person.first_name)],
                        last_names=[Literal(value=source_person.last_name)]
                    )]
            elif source_person.name not in external_person_data['display_name_variants']:
                external_person_data['display_name_variants'].append(source_person.name)
            if source_person.name_variants:
                external_person_data['display_name_variants'] = list(
                    set(external_person_data[
                            'display_name_variants'] + source_person.name_variants))

        return Person(**external_person_data)

    async def _merge_external_people(self,
                                     existing_external_people_uids,
                                     source_people_cluster) -> str:
        """
        Merge multiple external people into a single person
        :param existing_external_people_uids: List of UIDs of existing external people
        :param source_people_cluster: List of SourcePerson objects
        :return: The UID of the merged person
        """
        person_to_keep_uid = existing_external_people_uids.pop()
        for person_to_merge_uid in existing_external_people_uids:
            await self.person_dao.merge_people(person_to_keep_uid, person_to_merge_uid)
        # Link the source people to the merged person
        await self.source_person_dao.link_to_person([source_person.uid for source_person in
                                                     source_people_cluster],
                                                    person_to_keep_uid)
        return person_to_keep_uid

    async def _update_contributions(self, linked_people):
        document_dao = self._get_document_dao()
        current_contribution_ids = set()
        for person_uid, source_people_cluster in linked_people.items():
            roles = self._get_roles_by_harvester_order(
                source_people_cluster,
            )
            # Create contribution node and relationships
            contribution_id = await document_dao.create_contribution(
                document_uid=self.document_uid,
                person_uid=person_uid,
                roles=[role.value for role in roles]
            )
            if contribution_id is not None:
                current_contribution_ids.add(contribution_id)
        # Delete contributions that are not in the current set
        await document_dao.delete_contributions_not_in(
            document_uid=self.document_uid,
            contribution_ids=list(current_contribution_ids)
        )

    def _get_roles_by_harvester_order(
            self,
            source_people: List[SourcePerson],
    ) -> List[LocContributionRole]:
        """
        Sort source people by harvester order and extract roles based on contributions.

        :param source_people: List of SourcePerson objects.
        :return: the first encountered role
        """
        # Sort source_people by harvester order
        harvester_order = {harvester: index for index, harvester in
                           enumerate(self._get_harvesters())}
        sorted_people = sorted(
            source_people,
            key=lambda person: harvester_order.get(person.source, float('inf'))
        )

        roles = []

        # Search for each person in contributions and extract roles
        for person in sorted_people:
            for contribution in self.contributions:
                if (contribution.contributor.uid == person.uid
                        and contribution.role is not None
                        and contribution.role not in roles):
                    roles.append(contribution.role)

        return roles

    async def _fetch_harvested_for_people(
            self, person_dao: PersonDAO, source_records: list[SourceRecord]
    ) -> AsyncGenerator[Person, None]:
        """
        Fetch the harvested_for people associated with the given source records.

        :param person_dao: DAO for fetching Person data.
        :param source_records: List of SourceRecord objects.
        :return: An async generator yielding Person objects.
        """
        harvested_for_uids: set[str] = set()

        # Gather all harvested_for_uids from the source records
        for source_record in source_records:
            harvested_for_uids.update(source_record.harvested_for_uids)

        # Fetch Person objects for each harvested_for_uid
        for harvested_for_uid in harvested_for_uids:
            person = await person_dao.get(harvested_for_uid)
            if person:
                yield person

    @staticmethod
    def filter_unique_paths(paths: list[list[str]]) -> list[list[str]]:
        """
        Filters paths to retain only those without previously visited nodes.

        :param paths: List of lists where each inner list represents a path of UIDs.
        :return: A filtered list of paths with no overlapping nodes.
        """
        visited_nodes = set()
        filtered_paths = []

        for path in paths:
            if all(node not in visited_nodes for node in path):
                filtered_paths.append(path)
                visited_nodes.update(path)  # Mark nodes in this path as visited

        return filtered_paths

    @staticmethod
    def convert_paths_to_couples(paths: list[list[str]]) -> list[tuple[str, str]]:
        """
        Converts a list of paths into a list of consecutive couples.

        :param paths: List of paths, where each path is a list of UIDs.
        :return: A list of consecutive couples from the paths.
        """
        couples = []
        for path in paths:
            couples.extend((path[i], path[i + 1]) for i in range(len(path) - 1))
        return couples

    @staticmethod
    def _get_source_people(
            source_records: list[SourceRecord]
    ) -> list[SourcePerson]:
        source_people = [contribution.contributor for source_record in source_records for \
                         contribution in
                         source_record.contributions]
        return list({source_person.uid: source_person for source_person in source_people}.values())

    @staticmethod
    def _sort_source_people_by_source_platform(
            source_people: list[SourcePerson],
    ) -> dict[str, list[SourcePerson]]:
        # sort contributors in layers by harvester identifier
        source_people_by_source_platform = {}
        for source_person in source_people:
            # append the contributor to the list of contributors with the same harvester
            # except if the contributor is already in the list (by uid)
            source = source_person.source.lower().replace('_', '')
            if not any(
                    source_person.uid == sp.uid
                    for sp in source_people_by_source_platform.get(
                        source, [])
            ):
                source_people_by_source_platform.setdefault(
                    source, []).append(source_person)
        return source_people_by_source_platform

    def _compute_equivalence_distances(self, source_people):
        """
        Compute distances between contributors in layers and all subsequent layers.
        :param source_people: Dictionary of contributors by source platform
        :return: Dictionary of distances between contributors
        """
        harvesters = self._get_harvesters()  # ['Hal', 'Idref', 'ScanR', 'Scopus', 'OpenAlex']
        source_people_by_source_platform = source_people
        distances = {}
        existing_sources = list(source_people_by_source_platform.keys())
        # Order the sources by the order of the harvesters
        sources = [source for source in harvesters if source in existing_sources]

        # Compute distances between each layer and all subsequent layers
        for i, source in enumerate(sources):
            source_people = source_people_by_source_platform[source]
            for j in range(i + 1, len(sources)):  # Compare with all following layers
                next_source = sources[j]
                next_source_people = source_people_by_source_platform[next_source]
                for source_person in source_people:
                    for next_source_person in next_source_people:
                        distance = self._compute_distance(source_person, next_source_person)
                        # Store the distance
                        distances.setdefault(source_person.uid, {})[
                            next_source_person.uid] = distance

        return distances

    def _compute_distance(
            self, source_person: SourcePerson, next_source_person: SourcePerson
    ) -> float | None:
        if self._common_identifier(source_person, next_source_person):
            return 0
        proximity = self._compute_fuzz_distance(source_person.name, next_source_person.name)
        if (distance := 100 - proximity) > self._coauthor_names_maximal_distance():
            return None
        if distance == 0:
            return 0.0001  # as identical name is not as accurate as common identifier
        return distance

    def _normalize_string(self, input_string):
        # Convert to lowercase
        normalized = input_string.lower()

        # Replace accented characters with their ASCII equivalents
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')

        # Replace all non-letter characters with spaces
        normalized = re.sub(r'[^a-z]', ' ', normalized)

        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _coauthor_names_maximal_distance(self):
        return self.settings.coauthor_names_maximal_distance

    def _common_identifier(self, source_person: SourcePerson,
                           next_source_person: SourcePerson) -> bool:
        """
        Check if the two source persons have a common identifier with the same type and value.
        :param source_person: First source person
        :param next_source_person: Second source person
        :return: True if a common identifier exists, False otherwise
        """
        for identifier in source_person.identifiers:
            for next_identifier in next_source_person.identifiers:
                if (identifier.type == next_identifier.type
                        and identifier.value == next_identifier.value):
                    return True
        return False

    def _compute_fuzz_distance(self, name1: str, name2: str) -> float:
        """
        Compute the Levenshtein distance between two names
        :param name1: First name
        :param name2: Second name
        :return: normalized Levenshtein distance
        """
        return fuzz.token_sort_ratio(name1, name2, processor=self._normalize_string)

    def _is_similar(self, internal_person: Person, external_people: list[SourcePerson]) -> bool:
        """
        Check if an internal_person is similar to any person in the external_people cluster
        based on name similarity.

        :param internal_person: A Person object with structured names (internal person).
        :param external_people: List of SourcePerson objects
            with unstructured names (external people).
        :return: True if similar, False otherwise.
        """
        # Extract structured names from the internal person
        internal_names = [
            f"{fn.value} {ln.value}"
            for name in internal_person.names
            for fn in name.first_names
            for ln in name.last_names
        ]

        # Iterate over each SourcePerson in the external cluster
        for external_person in external_people:
            # Combine unstructured name and name_variants
            unstructured_names = [external_person.name] + (external_person.name_variants or [])
            for unstructured_name in unstructured_names:
                for internal_name in internal_names:
                    distance = self._compute_fuzz_distance(unstructured_name, internal_name)
                    if distance >= 85:  # Define a similarity threshold
                        return True

        return False

    def _get_person_dao(self):
        person_dao: PersonDAO = cast(PersonDAO, self._get_dao_factory().get_dao(Person))
        return person_dao

    def _get_source_person_dao(self):
        source_person_dao: SourcePersonDAO = cast(SourcePersonDAO, self._get_dao_factory().get_dao(
            SourcePerson))
        return source_person_dao

    def _get_document_dao(self):
        document_dao: DocumentDAO = cast(DocumentDAO, self._get_dao_factory().get_dao(Document))
        return document_dao

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)

    def _get_policies(self):
        return self.settings.publication_source_policies

    def _get_harvesters(self):
        return [harvester.lower().replace('_', '')
                for harvester in self._get_policies()['harvesters']]
