from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.utils import load_query
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentSubjectsChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the subjects of a Document.
    """

    async def apply(self) -> None:
        subject_uids = self.change.parameters.get("conceptUids")

        if not isinstance(subject_uids, list) or not all(
                isinstance(uid, str) for uid in subject_uids):
            raise ValueError(f"Invalid 'conceptUids' in parameters: {self.change.parameters}")
        document_uid = self.change.target_uid
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")

        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.execute_write(
                    self._remove_subjects_tx,
                    document_uid=document_uid,
                    subject_uids=subject_uids,
                )

    @staticmethod
    async def _remove_subjects_tx(tx, document_uid: str, subject_uids: list[str]):
        query = load_query("remove_document_subjects")
        await tx.run(query, document_uid=document_uid, subject_uids=subject_uids)
