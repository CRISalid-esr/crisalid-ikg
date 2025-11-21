from app.services.documents.doaj_service import DoajService
from app.utils.publication_api.publication_api_service import PublicationApiService


class UnpaywallService(PublicationApiService):
    """
    Service to check Open Access Status in Unpaywall
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.unpaywall.org/"

    async def _fetch_unpaywall_json(self, doi: str) -> str | None:
        url = f"{self.base_url}/{doi}?email={self.settings.email_unpaywall}"
        return await self._fetch_json(url)

    async def get_data(self, doi: str) -> dict:
        """
        Get data from Unpaywall API to be used to compute OpenAccess status
        """
        oa_data = {
            "upw_success": None,
            "upw_status": None,
            "repository_location": None,
            "doaj_success": None,
            "embargo_date": None
        }

        json_data = await self._fetch_unpaywall_json(doi)
        if json_data is None:
            oa_data["upw_success"] = False
            return oa_data

        oa_data["upw_success"] = True
        oa_data["upw_status"] = json_data.get("oa_status", None)

        oa_data["repository_location"] = None if not json_data.get("oa_locations") else any(
            loc.get("host_type") == "repository" for loc in json_data["oa_locations"]
        )

        # Missing potential embargo date to get when example arises

        if oa_data["upw_status"] == "Gold" and json_data.get("journal_is_in_doaj", False):
            apc_data = await DoajService().get_apc_status(json_data.get("journal_issn_l"))
            oa_data["doaj_success"] = apc_data["doaj_success"]
            if not apc_data["has_apc"]:
                oa_data["upw_status"] = "Diamond"

        return oa_data
