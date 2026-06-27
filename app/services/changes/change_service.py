from typing import cast

from loguru import logger

from app.config import get_app_settings
from app.errors.database_error import DatabaseError
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.change_dao import ChangeDAO
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.change import Change, TargetType, ChangeStatus
from app.models.document import Document
from app.services.changes.change_processor_factory import ChangeProcessorFactory
from app.amqp.message_mode import MessageMode
from app.signals import document_updated


class ChangeService:
    """
    Service for managing changes in the graph.
    """

    async def create_and_apply_change(
            self, change: Change, mode: MessageMode = MessageMode.INTERACTIVE) -> None:
        """
        Create a Change node if it does not exist, or update the status if it does.
        This method is intended to "on the fly" apply changes to the graph.
        :param change:
        :param mode: message mode for the outbound document-updated event
        :return:
        """
        existing = await self._change_dao().get_by_uid(change.uid)

        if existing:
            if existing.status == ChangeStatus.APPLIED:
                logger.info(f"Change {change.uid} already applied. Skipping.")
                return
            if existing.status == ChangeStatus.FAILED:
                logger.info(f"Change {change.uid} had failed. Retrying.")
                return
            logger.info(f"Change {change.uid} found bu not applied. Applying.")
            await self.apply_change(existing, mode=mode)
        else:
            logger.info(f"Change {change.uid} not found. Creating and applying.")
            await self.create_change(change)
            await self.apply_change(change, mode=mode)

    async def create_change(self, change: Change) -> Change:
        """
        Create a Change node in the database.
        :param change:
        :return:
        """
        # Validate existence of the target entity before creating the change
        if change.target_type == TargetType.DOCUMENT:
            document_dao: DocumentDAO = self._document_dao()
            document = await document_dao.get_document_by_uid(change.target_uid)
            if document is None:
                raise ValueError(f"Target document {change.target_uid} does not exist")
            change.status = ChangeStatus.CREATED
            return await self._change_dao().create_document_change(document, change)

    async def apply_change(
            self, change: Change, mode: MessageMode = MessageMode.INTERACTIVE) -> None:
        """
        Apply a change to the graph.
        :param change:
        :param mode: message mode for the outbound document-updated event
        :return:
        """
        try:
            processor = ChangeProcessorFactory.get_processor(change)
            await processor.apply()
            change.status = ChangeStatus.APPLIED
            await self._update_change_status(change)
            # for MERGE changes, the document_updated signal is sent by the processor
            if change.target_type == TargetType.DOCUMENT and change.action_type not in ("MERGE"):
                await document_updated.send_async(self, document_uid=change.target_uid,
                                                  mode=mode)
        except (DatabaseError, ValueError) as e:
            change.status = ChangeStatus.FAILED
            change.error_message = str(e)
            await self._update_change_status(change)
            logger.error(f"Failed to apply change {change.uid}: {e}")
            raise e

    async def apply_changes_to_node(
            self, target_uid: str, mode: MessageMode = MessageMode.BATCH) -> None:
        """
        Apply all changes related to a specific target UID.

        Contribution changes carry full state, so only the latest ``contributions`` change is
        applied; older ones are superseded (kept in the graph for history, not replayed).
        :param target_uid:
        :param mode: message mode for the outbound document-updated events
        :return:
        """
        changes = await self._change_dao().get_changes_by_target_uid(
            target_uid=target_uid
        )
        # changes are returned ordered by timestamp ASC, so the last one wins
        latest_contributions_uid = None
        for change in changes:
            if change.path == "contributions":
                latest_contributions_uid = change.uid
        for change in changes:
            if change.action_type == "MERGE":
                # Skip merge changes to avoid infinite loops
                continue
            # supersession: only the latest contributions change is replayed
            if change.path == "contributions" and change.uid != latest_contributions_uid:
                continue
            try:
                await self.apply_change(change, mode=mode)
            except (DatabaseError, ValueError) as e:
                logger.error(f"Failed to apply change {change.uid} to {target_uid}: {e}")

    async def _update_change_status(self, change: Change) -> None:
        """
        Update the status of a change in the database.
        :param change: The Change object with updated status.
        :return: None
        """
        await self._change_dao().update_status(change)

    def _document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
        return dao

    def _change_dao(self) -> ChangeDAO:
        factory = self._get_dao_factory()
        dao: ChangeDAO = cast(ChangeDAO, factory.get_dao(Change))
        return dao

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
