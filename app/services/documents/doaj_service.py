from dataclasses import dataclass
from typing import Optional

from app.utils.api.api_service import ApiService


class DoajService(ApiService):
    """
    Service to check APC Status in DOAJ
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://doaj.org/api/search/journals/issn:"

    async def _fetch_doaj_json(self, issn: str) -> dict | None:
        url = f"{self.base_url}{issn}"
        return await self._fetch_json(url)

    @dataclass
    class DoajResponseSchema:
        """
        Dataclass for information gathered from DOAJ
        """
        doaj_success: Optional[bool] = None
        has_apc: Optional[bool] = None

    async def get_apc_status(self, issn: str) -> DoajResponseSchema:
        """
        Get data from DOAJ API to check if a journal has APC
        """
        apc_data = self.DoajResponseSchema()

        json_data = await self._fetch_doaj_json(issn)
        if json_data is None:
            apc_data.doaj_success = False
            return apc_data

        apc_data.doaj_success = True

        if json_data.get("results"):
            apc_data.has_apc = json_data.get("results")[0].get(
                "bibjson", {}).get("apc", {}).get("has_apc", None)

        return apc_data
