import json

from elastic_transport import TransportError
from loguru import logger
from pydantic_core import PydanticSerializationError

from app.config import get_app_settings
from app.services.source_records.source_record_service import SourceRecordService


class SourceRecordIndex:
    """
    Search engine interface for source records
    """

    def __init__(self, app_state):
        self.app_state = app_state
        self.es_client = None
        self.service = None
        settings = get_app_settings()
        self.index_config = settings.es_indexes["source_records"]

    async def add_source_record(self, _, source_record_id):
        """
        Add a source record to the index
        :param emitter: the emitter of the signal
        :param source_record_id: the source record id
        :return: True if the source record has been added to the index, False otherwise
        """

        if not self._init_es_client():
            logger.debug(
                "Elasticsearch client is not set up, cannot add source record %s to the index",
                source_record_id)
            return False
        print(f"Adding source record {source_record_id} to the index")
        self.service = SourceRecordService()
        source_record = await self.service.get_source_record(source_record_id)
        try:
            metadata = source_record.model_dump() | {"id": source_record_id}
        except PydanticSerializationError as e:
            logger.error(f"Error while converting source record {source_record_id} to dict: {e}")
            return False
        try:
            json_metadata = json.dumps(metadata, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"Error while serializing source record {source_record_id} to JSON: {e}")
            return False

        try:
            await self.es_client.index(index=self.index_config["index_name"],
                                       id=source_record_id, body=json_metadata)
            return True
        except TransportError as e:
            print(f"Connexion error while adding source record {source_record_id} to the index:"
                  f" {e}")
            return False

    def _init_es_client(self) -> bool:
        if not self.es_client:
            self.es_client = self.app_state.es_client
        return self.es_client is not None
