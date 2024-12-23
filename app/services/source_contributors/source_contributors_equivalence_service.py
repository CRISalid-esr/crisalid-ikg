from typing import cast

from Levenshtein import distance as levenshtein_distance

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.source_people import SourcePerson
from app.models.source_records import SourceRecord


class SourceContributorsEquivalenceService:
    """
    Service to handle operations on source journals data
    """

    def __init__(self):
        self.settings = get_app_settings()

    async def update_source_person_equivalences(self, _, textual_document_uid: str):
        """
        Recompute metadata for a textual document
        :param _: unused (for compatibility with signal handlers)
        :param textual_document_uid: the textual document uid
        :return:
        """
        # fetch the source records whose contributors are to be merged
        dao: SourceRecordDAO = cast(SourceRecordDAO, self._get_dao_factory().get_dao(SourceRecord))
        source_people = await self._fetch_source_people_by_source_platform(dao,
                                                                           textual_document_uid)
        distances = self._compute_equivalence_distances(source_people)
        print(distances)

    async def _fetch_source_people_by_source_platform(self, dao, textual_document_uid):
        sources_record_uids = await dao.get_source_record_uids_by_textual_document_uid(
            textual_document_uid)
        source_records = [await dao.get(source_record_uid) for source_record_uid in
                          sources_record_uids]
        # collect the contributors from the source records and sort it in layers by harvester
        # identifier
        # if 2 contributors (source person) have the same source identifier source and source
        # identifier, deduplicate
        source_people_by_source_platform = {}
        for source_record in source_records:
            for contribution in source_record.contributions:
                # append the contributor to the list of contributors with the same harvester
                # except if the contributor is already in the list (by uid)
                source_person = contribution.contributor
                source = contribution.contributor.source.lower().replace('_', '')
                if any(
                        source_person.uid == sp.uid
                        for sp in source_people_by_source_platform.get(
                            source, [])
                ):
                    continue
                source_people_by_source_platform.setdefault(
                    source, []).append(source_person)
        return source_people_by_source_platform

    # Next layer only versio
    # def _compute_equivalence_distances(self, source_people):
    #     harvesters = self._get_harvesters()  # ['Hal', 'Idref', 'ScanR', 'Scopus', 'OpenAlex']
    #     # take the layers in the order of the harvesters
    #     # for each layer, compute the distance between each contributor and the contributors of
    #     # the next layers (not yet computed)
    #     # if the contributors share a common identifier (type/value), the distance is 0
    #     # else the distance is the levenstein distance between the names
    #     source_people_by_source_platform = source_people
    #     distances = {}
    #     existing_sources = list(source_people_by_source_platform.keys())
    #     # order the sources by the order of the harvesters
    #     sources = [source for source in harvesters if source in existing_sources]
    #     # continue until there is only one source left
    #     for i, source in enumerate(sources):
    #         if i + 1 >= len(sources):
    #             break
    #         next_source = sources[i + 1] if i + 1 < len(sources) else None
    #         source_people = source_people_by_source_platform[source]
    #         next_source_people = source_people_by_source_platform.get(next_source, [])
    #         for source_person in source_people:
    #             for next_source_person in next_source_people:
    #                 distance = self._compute_distance(source_person, next_source_person)
    #                 distances.setdefault(source_person.uid, {})[next_source_person.uid] = distance
    #
    #     return distances

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

    def _compute_distance(self, source_person: SourcePerson, next_source_person: SourcePerson):
        # compare identifiers
        if self._common_identifier(source_person, next_source_person):
            return 0
        return self._compute_levenshtein_distance(source_person.name, next_source_person.name)

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

    @staticmethod
    def _compute_levenshtein_distance(name1: str, name2: str) -> int:
        """
        Compute the Levenshtein distance between two names
        :param name1: First name
        :param name2: Second name
        :return: Levenshtein distance
        """
        return levenshtein_distance(name1, name2)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)

    def _get_policies(self):
        return self.settings.publication_source_policies

    def _get_harvesters(self):
        return [harvester.lower().replace('_', '')
                for harvester in self._get_policies()['harvesters']]
