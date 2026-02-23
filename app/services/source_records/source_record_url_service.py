import urllib.parse

from loguru import logger
from pydantic import HttpUrl

from app.models.harvesters import Harvester


class SourceRecordUrlService:
    """
    Stateless service to compute the source record main page URL
    based on harvester and source identifier.
    """

    OPENALEX_IDREF_HARVESTERS = {Harvester.OPENALEX.value, Harvester.IDREF.value}
    HAL_PREFIX = "https://hal.science/"
    SCANR_PREFIX = "https://scanr.enseignementsup-recherche.gouv.fr/publications/"

    @staticmethod
    def compute_url(harvester: str, source_identifier: str) -> HttpUrl:
        """
        Compute the URL for the source record main page
        based on the harvester and source identifier.

        :param harvester:
        :param source_identifier:
        :return:
        """
        try:
            if not source_identifier or not source_identifier.strip():
                raise ValueError("Source identifier cannot be blank or whitespace")
            if harvester in SourceRecordUrlService.OPENALEX_IDREF_HARVESTERS:
                url = source_identifier  # Directly use the source identifier
            elif harvester == Harvester.HAL.value:
                url = f"{SourceRecordUrlService.HAL_PREFIX}{source_identifier}"
            elif harvester == Harvester.SCANR.value:
                encoded_identifier = urllib.parse.quote(source_identifier, safe='')
                url = f"{SourceRecordUrlService.SCANR_PREFIX}{encoded_identifier}"
            else:
                raise ValueError(f"Unsupported harvester: {harvester}")

            # Validate the URL
            return HttpUrl(url)
        except ValueError as e:
            logger.error(
                f"Error computing URL for harvester='{harvester}', "
                f"source_identifier='{source_identifier}': {e}")
            raise ValueError("Invalid source record URL computation") from e
