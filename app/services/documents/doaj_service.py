from app.services.documents.publication_api_service import PublicationApiService


class DoajService(PublicationApiService):
    """
    Service to check APC Status in DOAJ
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://doaj.org/api/search/journals/issn:"

    async def _fetch_doaj_json(self, issn: str) -> dict | None:
        url = f"{self.base_url}{issn}"
        return await self._fetch_json(url)

    async def get_apc_status(self, issn: str) -> dict:
        """
        Get data from DOAJ API to check if a journal has APC
        """
        apc_data = {
            "doaj_success": None,
            "has_apc": None,
        }

        json_data = await self._fetch_doaj_json(issn)
        if json_data is None:
            apc_data["doaj_success"] = False
            return apc_data

        apc_data["doaj_success"] = True

        if json_data.get("results"):
            apc_data["has_apc"] = json_data.get("results")[0].get(
                "bibjson", {}).get("apc", {}).get("has_apc", None)

        return apc_data
