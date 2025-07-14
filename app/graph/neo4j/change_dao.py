from neo4j import AsyncManagedTransaction, AsyncTransaction, Record, AsyncResult

from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.change import Change, TargetType
from app.models.document import Document


class ChangeDAO(Neo4jDAO):
    """
    DAO for managing Change nodes related to user modifications.
    """

    @handle_database_errors
    async def get_by_uid(self, uid: str) -> Change | None:
        """
        Retrieve a Change node by its UID.
        :param uid:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result: AsyncResult = await self._get_by_uid_tx(tx, uid)
                    record: Record | None = await result.single()
                    if record is None:
                        return None
                    return self._hydrate(record)

    @handle_database_errors
    async def create_document_change(self, document: Document, change: Change) -> Change:
        """
        Create a Change node for a Document modification.
        :param document:
        :param change:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    await self._create_document_change_tx(tx, document, change)
        return change

    @handle_database_errors
    async def update_status(self, change: Change) -> None:
        """
        Update the status of a Change node.
        :param change:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._update_change_status_tx, change)

    @handle_database_errors
    async def get_changes_by_target_uid(self, target_uid: str) -> list[Change]:
        """
        Retrieve all Change nodes related to a specific target UID.
        :param target_uid:
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                return await session.read_transaction(
                    self._get_changes_by_target_uid_tx, target_uid
                )

    @staticmethod
    async def _get_by_uid_tx(tx: AsyncTransaction, uid: str) -> AsyncResult:
        query = load_query("get_change_by_uid")
        return await tx.run(query, uid=uid)

    @staticmethod
    async def _create_document_change_tx(
            tx: AsyncManagedTransaction, document: Document, change: Change
    ):
        query = load_query("create_document_change")
        await tx.run(
            query,
            uid=change.uid,
            document_uid=document.uid,
            person_uid=change.person_uid,
            application=change.application,
            id=change.id,
            action=change.action,
            path=change.path,
            params=change.marshal_parameters(),
            timestamp=change.timestamp.isoformat(),
            status=change.status.value,
            error_message=change.error_message
        )

    @staticmethod
    async def _update_change_status_tx(tx: AsyncManagedTransaction, change: Change):
        query = load_query("update_change_status")
        await tx.run(
            query,
            uid=change.uid,
            status=change.status.value,
            error_message=change.error_message
        )

    @classmethod
    async def _get_changes_by_target_uid_tx(
            cls, tx: AsyncTransaction, target_uid: str
    ) -> list[Change]:
        query = load_query("get_changes_by_target_uid")
        result = await tx.run(query, target_uid=target_uid)
        return [
            cls._hydrate(record)
            async for record in result
        ]

    @staticmethod
    def _hydrate(record: Record) -> Change:
        """
        Build a Change model instance from a Neo4j record.

        Required fields in the record:
        - record["change"]: the Change node
        - record["target_uid"]: UID of the target node
        - record["target_labels"]: list of labels on the target node
        """
        change_data = dict(record["change"])
        change_data["target_uid"] = record["target_uid"]

        # Convert Neo4j DateTime to Python datetime
        timestamp = change_data["timestamp"]
        if hasattr(timestamp, "to_native"):
            change_data["timestamp"] = timestamp.to_native()
        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

        labels = record["target_labels"]
        if "Document" in labels:
            change_data["target_type"] = TargetType.DOCUMENT
        else:
            raise ValueError(f"Unsupported target labels: {labels}")

        return Change.model_validate(change_data)
