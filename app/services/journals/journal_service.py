import time
from typing import Optional

from loguru import logger

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.journal_dao import JournalDAO
from app.graph.neo4j.source_journal_dao import SourceJournalDAO
from app.models.document_publication_channel import DocumentPublicationChannel
from app.models.identifier_types import JournalIdentifierType
from app.models.journal import Journal
from app.models.journal_identifiers import JournalIdentifier
from app.models.source_journal import SourceJournal
from app.models.source_records import SourceRecord
from app.services.journals.issn_service import ISSNService


class JournalService:
    """
    Service to handle operations on journals data
    """

    # constructor. get app settings and take issn_check_delay parameter
    def __init__(self):
        self.settings = get_app_settings()
        self.issn_check_delay = self.settings.issn_check_delay
        self.issn_service = ISSNService()
        self.journal_dao: JournalDAO = self._get_dao_factory().get_dao(Journal)

    async def link_journal_identifiers(self, _, source_journal_uid) -> list[str]:
        """
        Create a source scientific journal in the graph database
        from a Pydantic SourceJournal object
        :param source_journal_uid: the uid of the source journal
        :return: the list of journal uids created or updated
        """
        factory = self._get_dao_factory()
        source_journal_dao: SourceJournalDAO = factory.get_dao(SourceJournal)
        source_journal = await source_journal_dao.get_by_uid(source_journal_uid)
        identifiers = source_journal.identifiers
        # creat a set of identifiers
        journal_uids = set()
        for identifier in identifiers:
            if identifier.type == JournalIdentifierType.ISSN:
                # last_checked is a timestamp (int)
                last_checked = identifier.last_checked
                # if last_checked is None
                # or time since last_checked is greater than issn_check_delay
                if last_checked is None or (time.time() - last_checked) > self.issn_check_delay:
                    # check the related journal exists or create it
                    journal = await self._create_or_update_journal_from(source_journal, identifier)
                    if journal:
                        journal_uids.add(journal.uid)
        return list(journal_uids)

    async def _create_or_update_journal_from(self, source_journal: SourceJournal,
                                             identifier: JournalIdentifier) -> Journal | None:
        """
        Check the identifier and update the last_checked timestamp
        :param identifier: JournalIdentifier object
        :return:
        """
        issn_info = await self.issn_service.check_identifier(identifier)
        if issn_info.errors:
            # if there are errors, set last_checked to None
            identifier.last_checked = None
            return None
        identifier.last_checked = int(time.time())
        # ISSN portal RDF pages do not provide publisher information for now
        issn_info.publisher = source_journal.publisher
        journal = Journal.from_issn_info(issn_info)
        existing_journal = await self.journal_dao.get_by_uid(journal.uid)

        # update the identifiers list with the last_checked timestamp
        journal.identifiers = self._update_identifier_timestamps(
            identifier,
            journal.identifiers,
            existing_identifiers=existing_journal.identifiers
            if existing_journal else [])
        if existing_journal:
            await self.journal_dao.update(journal)
        else:
            await self.journal_dao.create(journal)

        return journal

    @staticmethod
    def _update_identifier_timestamps(
            checked_identifier: JournalIdentifier,
            identifiers: list[JournalIdentifier],
            existing_identifiers: list[JournalIdentifier]) -> list[JournalIdentifier]:
        updated_identifiers = []
        for journal_identifier in identifiers:
            # If an existing journal has a matching identifier, take its timestamp
            for existing_id in existing_identifiers:
                if (journal_identifier.type == existing_id.type
                        and journal_identifier.value == existing_id.value):
                    journal_identifier.last_checked = existing_id.last_checked
                    break

            # If this is the identifier we just checked, override timestamp
            if (journal_identifier.type == checked_identifier.type
                    and journal_identifier.value == checked_identifier.value):
                journal_identifier.last_checked = checked_identifier.last_checked

            updated_identifiers.append(journal_identifier)
        return updated_identifiers

    async def compute_document_publication_channel(self, document_uid: str,
                                                   source_records: list[SourceRecord]) \
            -> Optional[DocumentPublicationChannel]:
        """
        Compute the publication channel for a document based on its source records.
        :param document_uid: The UID of the document to resolve.
        :param source_records: A list of source records associated with the document.
        :return: DocumentPublicationChannel if a journal is resolved, otherwise None.
        """
        harvester_priority = self._get_harvesters()
        selected_journal = None
        selected_volume = None
        selected_number = None

        def record_priority(record: SourceRecord):
            return harvester_priority.index(record.harvester.lower()) \
                if record.harvester.lower() in harvester_priority \
                else float('inf')

        sorted_records = sorted(source_records, key=record_priority)

        # First pass: prefer only unique journal resolution
        selected_journal, selected_volume, selected_number = await self._try_resolve_journal(
            sorted_records, unique_only=True)

        # Second pass: allow multiple journals if nothing was found
        if selected_journal is None:
            selected_journal, selected_volume, selected_number = await self._try_resolve_journal(
                sorted_records, unique_only=False)

        if selected_journal:
            logger.info(
                f"Document {document_uid} resolved to journal {selected_journal.uid} "
                f"with volume={selected_volume} and number={selected_number}")
            return DocumentPublicationChannel(
                publication_channel=selected_journal,
                volume=selected_volume or "",
                issue=selected_number[0] if selected_number else "",
                pages=""
            )
        logger.warning(f"Document {document_uid} could not be resolved to a journal")
        return None

    async def _try_resolve_journal(
            self,
            sorted_records: list[SourceRecord],
            unique_only: bool
    ) -> tuple[Optional[Journal], Optional[str], Optional[list[str]]]:
        selected_journal = None
        selected_volume = None
        selected_number = None

        for record in sorted_records:
            issue = getattr(record, 'issue', None)
            if not issue or not issue.journal:
                continue

            journal_candidates = await self._get_journals_from_source(issue.journal)

            if unique_only:
                if len(journal_candidates) != 1:
                    if len(journal_candidates) > 1:
                        logger.warning(
                            f"Multiple journals found for source journal {issue.journal.uid}, "
                            "ignoring this source record."
                        )
                    continue

                journal = next(iter(journal_candidates.values()))
                if selected_journal is None:
                    selected_journal = journal
                elif selected_journal.uid != journal.uid:
                    continue
                # If we dont have this information yet, take it from the issue
                if selected_volume is None and issue.volume:
                    selected_volume = issue.volume
                if selected_number is None and issue.number:
                    selected_number = issue.number

            else:
                if journal_candidates:
                    journal = next(iter(journal_candidates.values()))
                    selected_journal = journal
                    selected_volume = issue.volume
                    selected_number = issue.number
                    break

        return selected_journal, selected_volume, selected_number

    async def _get_journals_from_source(
            self, source_journal: SourceJournal
    ) -> dict[str, Journal]:
        result = {}
        for identifier in source_journal.identifiers:
            if identifier.type != JournalIdentifierType.ISSN:
                continue
            journal = await self.journal_dao.get_by_identifier(identifier)
            if journal:
                result[journal.uid] = journal
        return result

    def _get_policies(self):
        return self.settings.publication_source_policies

    def _get_harvesters(self):
        return [harvester.lower().replace('_', '')
                for harvester in self._get_policies()['harvesters']]

    def _get_dao_factory(self) -> DAOFactory:
        return AbstractDAOFactory().get_dao_factory(self.settings.graph_db)
