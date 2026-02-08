from datetime import datetime
from typing import List

from app.config import get_app_settings
from app.models.document import Document
from app.models.harvesters import Harvester
from app.models.identifier_types import PublicationIdentifierType
from app.models.open_access_status import OpenAccessStatus, UnpaywallOAStatus, OAStatus
from app.models.source_records import SourceRecord
from app.services.documents.unpaywall_service import UnpaywallService

class OAColorsComputationService:
    """
    Service to compute the open access status of a document
    """

    def __init__(self, document: Document, source_records: List[SourceRecord]):
        """
        Constructor
        :docu
        :param source_records: the source records to be merged
        """
        self.document = document
        self.document.open_access_status = OpenAccessStatus()
        self.source_records = source_records
        self.settings = get_app_settings()

    async def compute_oa_colors(self) -> Document:
        """
        Compute the OpenAccess status for the document
        :return: the Document instance
        """

        doi = next((id.value for sr in self.source_records
                for id in sr.identifiers if id.type == PublicationIdentifierType.DOI),
                None)

        document_oa_status = self.document.open_access_status
        document_oa_status.oa_computation_timestamp = datetime.now()

        # Add green open access status if file is available in Hal
        document_oa_status.oa_status = next(
            (OAStatus.GREEN for sr in self.source_records if sr.harvester == Harvester.HAL.value
                  and getattr(sr.custom_metadata, 'hal_submit_type', None) == 'file'),
            None)

        # if no doi, the only status available depends on Hal (above)
        if doi is None:
            if document_oa_status.oa_status == OAStatus.GREEN:
                document_oa_status.oa_computed_status = True
                return self.document

            document_oa_status.oa_status = OAStatus.CLOSED
            document_oa_status.oa_computed_status = True
            return self.document

        # if doi available, get OA status from Unpaywall (with call to DOAJ if necessary)
        upw_data = await UnpaywallService().get_data(doi)

        # unpaywall oa status and success status are updated
        document_oa_status.upw_oa_status = UnpaywallOAStatus(upw_data.upw_status) \
            if upw_data.upw_status else None
        document_oa_status.oa_upw_success_status = upw_data.upw_success
        document_oa_status.oa_doaj_success_status = upw_data.doaj_success
        if document_oa_status.oa_upw_success_status:
            document_oa_status.oa_computed_status = True

        # generic OA status is updated based on unpaywall information
        if document_oa_status.oa_status != OAStatus.GREEN:
            if upw_data.repository_location:
                document_oa_status.oa_computed_status = True
                document_oa_status.oa_status = OAStatus.GREEN
            elif upw_data.upw_status and upw_data.upw_status.lower() == OAStatus.GREEN:
                document_oa_status.oa_computed_status = True
                document_oa_status.oa_status = OAStatus.GREEN
            elif upw_data.upw_status and upw_data.upw_status.lower() == OAStatus.CLOSED:
                document_oa_status.oa_computed_status = True
                document_oa_status.oa_status = OAStatus.CLOSED
            elif upw_data.upw_status is None:
                document_oa_status.oa_computed_status = True
                document_oa_status.oa_status = OAStatus.CLOSED

        # Add COAR color based on info from upw_data (when embargo date available...)
        # TO BE ADDED

        return self.document
