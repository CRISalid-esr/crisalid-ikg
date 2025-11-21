import aiohttp
from aiohttp import ClientError
from loguru import logger

from app.config import get_app_settings
from app.http.aio_http_client_manager import AioHttpClientManager

class PublicationApiService:
    """
    Base service for API services
    """
    def __init__(self):
        self.headers = {"Accept": "application/ld+json"}
        self.settings = get_app_settings()

    async def _fetch_json(self, url: str) -> dict | None:
        try:
            session = await AioHttpClientManager.get_session()
            async with session.get(url, headers=self.headers, allow_redirects=False) as resp:
                if resp.status != 200:
                    logger.error(f"HTTP error {resp.status} fetching {url}")
                    return None
                return await resp.json()
        except ClientError as e:
            logger.exception(f"ClientError while fetching {url}: {e}")
            return None
        except aiohttp.http_exceptions.HttpProcessingError as e:
            logger.exception(f"HTTP processing error for {url}: {e}")
            return None

    async def _fetch_rdf(self, url: str) -> str | None:
        try:
            session = await AioHttpClientManager.get_session()
            async with session.get(url, headers=self.headers, allow_redirects=False) as resp:
                if resp.status != 200:
                    logger.error(f"HTTP error {resp.status} fetching {url}")
                    return None
                return await resp.text()
        except ClientError as e:
            logger.exception(f"ClientError while fetching {url}: {e}")
            return None
        except aiohttp.http_exceptions.HttpProcessingError as e:
            logger.exception(f"HTTP processing error for {url}: {e}")
            return None
