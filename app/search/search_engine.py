import json
import os

from elastic_transport import TransportError
from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.config import get_app_settings


class SearchEngine:
    """
    Search engine interface for Elasticsearch
    """

    def __init__(self):
        self.es_client = None

    async def setup_elasticsearch(self) -> None:
        """
        Setup Elasticsearch indexes
        :return: None
        """
        settings = get_app_settings()
        self.es_client = AsyncElasticsearch(
            [f"{settings.es_host}:{settings.es_port}"],
            http_auth=(settings.es_user, settings.es_password),
            verify_certs=True,
        )
        for index, config in settings.es_indexes.items():
            current_directory_path = os.path.dirname(os.path.abspath(__file__))
            try:
                with open(f"{current_directory_path}/indexes/{index}/mappings.json",
                          "r", encoding="utf-8") as f:
                    mappings = json.load(f)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"File mappings.json not found for index {index}") from e
            try:
                with open(f"{current_directory_path}/indexes/{index}/settings.json", "r",
                          encoding="utf-8") as f:
                    settings = json.load(f)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"File settings.json not found for index {index}") from e
            try:
                index_exists = await self.es_client.indices.exists(index=config["index_name"])
                if index_exists:
                    continue
                await self.es_client.indices.create(index=config["index_name"], mappings=mappings,
                                                    settings=settings)
            except TransportError as e:
                logger.error(f"Error while creating index {index}: {e}")
                raise e

    async def close_elasticsearch(self) -> None:
        """
        Close Elasticsearch connection
        :return: None
        """
        try:
            await self.es_client.close()
        except TransportError as e:
            logger.error(f"Error while closing Elasticsearch connexion: {e}")

    def get_es_client(self) -> AsyncElasticsearch:
        """
        Return the Elasticsearch client instance.
        """
        if not self.es_client:
            raise RuntimeError("Elasticsearch has not been set up yet.")
        return self.es_client
