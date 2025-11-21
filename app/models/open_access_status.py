import datetime
from typing import Optional

from pydantic import BaseModel


class OpenAccessStatus(BaseModel):
    """
    Submodel to gather information about the open access status
    """
    oa_computation_timestamp: Optional[datetime.datetime] = None
    oa_computed_status: Optional[bool] = False
    oa_upw_success_status: Optional[bool] = None
    oa_doaj_success_status: Optional[bool] = None
    oa_status: Optional[str] = None
    upw_oa_status: Optional[str] = None
    coar_oa_status: Optional[str] = None
