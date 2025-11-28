from datetime import datetime
from typing import List

from app.config import get_app_settings
from app.models.document import Document
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
        document_oa_status.oa_status = next(
            (OAStatus.GREEN for sr in self.source_records if sr.harvester.lower() == 'hal'
                  and getattr(sr.custom_metadata, 'hal_submit_type', None) == 'file'),
            None)

        if doi is None:
            if document_oa_status.oa_status == OAStatus.GREEN:
                document_oa_status.oa_computed_status = True
                return self.document

            return self.document

        upw_data = await UnpaywallService().get_data(doi)

        document_oa_status.upw_oa_status = UnpaywallOAStatus(upw_data.upw_status) \
            if upw_data.upw_status else None
        document_oa_status.oa_upw_success_status = upw_data.upw_success
        document_oa_status.oa_doaj_success_status = upw_data.doaj_success
        if document_oa_status.oa_upw_success_status:
            document_oa_status.oa_computed_status = True

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

        return self.document
