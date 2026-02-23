from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models.open_access_status import UnpaywallOAStatus
from app.services.documents.doaj_service import DoajService
from app.utils.api.api_service import ApiService


class UnpaywallService(ApiService):
    """
    Service to check Open Access Status in Unpaywall
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.unpaywall.org/"

    async def _fetch_unpaywall_json(self, doi: str) -> str | None:
        url = f"{self.base_url}/{doi}?email={self.settings.email_unpaywall}"
        return await self._fetch_json(url)

    @dataclass
    class UpwResponseSchema:
        """
        Dataclass for information gathered from Unpaywall
        """
        upw_success: Optional[bool] = None
        upw_status: Optional[str] = None
        repository_location: Optional[bool] = None
        doaj_success: Optional[bool] = None
        embargo_date: Optional[datetime] = None

    async def get_data(self, doi: str) -> UpwResponseSchema:
        """
        Get data from Unpaywall API to be used to compute OpenAccess status
        """
        oa_data = self.UpwResponseSchema()

        json_data = await self._fetch_unpaywall_json(doi)
        if json_data is None:
            # The error may result from either an invalid doi or from platform unavailability
            oa_data.upw_success = False
            return oa_data

        assert isinstance(json_data, dict), "Unpaywall API response should be a json dict"

        oa_data.upw_success = True
        oa_data.upw_status = json_data.get("oa_status", None)

        # Check if document file is available in a repository
        oa_data.repository_location = None if not json_data.get("oa_locations") else any(
            loc.get("host_type") == "repository" for loc in json_data["oa_locations"]
        )

        # Missing potential embargo date to get when example arises

        # If gold status, check if Journal has APCs in DOAJ. If not, set status to Diamond
        if (oa_data.upw_status and oa_data.upw_status.lower() == UnpaywallOAStatus.GOLD
                and json_data.get("journal_is_in_doaj", False)):
            apc_data = await DoajService().get_apc_status(json_data.get("journal_issn_l"))
            oa_data.doaj_success = apc_data.doaj_success
            if not apc_data.has_apc:
                oa_data.upw_status = "diamond"

        return oa_data
