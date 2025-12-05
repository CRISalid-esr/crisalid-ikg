import json

import aiohttp
from aiohttp import ClientError
from aiohttp.http_exceptions import HttpProcessingError
from loguru import logger

from app.config import get_app_settings
from app.http.aio_http_client_manager import AioHttpClientManager

class ApiService:
    """
    Base service for API services
    """
    def __init__(self):
        self.headers = {"Accept": "application/ld+json"}
        self.settings = get_app_settings()

    async def _fetch_json(self, url: str) -> dict | None:
        try:
            session = await AioHttpClientManager.get_session()
            if self.settings.app_env == "TEST" and not hasattr(session.get, "mock_calls"):
                raise RuntimeError("In TEST environment, aiohttp session must be mocked")
            async with session.get(url, headers=self.headers, allow_redirects=False) as resp:
                if resp.status != 200:
                    logger.error(f"HTTP error {resp.status} fetching {url}")
                    return None
                json_data = await resp.json()
                try:
                    if not isinstance(json_data, dict) and isinstance(json_data, str):
                        json_data = json.loads(json_data)
                except (json.JSONDecodeError, TypeError) as e:
                    # to handle an error in API response
                    print("Error parsing JSON from Unpaywall:", e)
                return json_data
        except ClientError as e:
            logger.exception(f"ClientError while fetching {url}: {e}")
            return None
        except HttpProcessingError as e:
            logger.exception(f"HTTP processing error for {url}: {e}")
            return None

    async def _fetch_rdf(self, url: str) -> str | None:
        try:
            session = await AioHttpClientManager.get_session()
            if self.settings.app_env == "TEST" and not hasattr(session.get, "mock_calls"):
                raise RuntimeError("In TEST environment, aiohttp session must be mocked")
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
