import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class OAStatus(str, Enum):
    """
    Enumeration of generic OA statuses
    """
    GREEN = "green"
    CLOSED = "closed"


class UnpaywallOAStatus(str, Enum):
    """
    Enumeration of Unpaywall OA statuses
    """
    GREEN = "green"
    DIAMOND = "diamond"
    GOLD = "gold"
    BRONZE = "bronze"
    HYBRID = "hybrid"
    OTHER = "other"
    CLOSED = "closed"

class OpenAccessStatus(BaseModel):
    """
    Submodel to gather information about the open access status
    """
    oa_computation_timestamp: Optional[datetime.datetime] = None
    oa_computed_status: Optional[bool] = False
    oa_upw_success_status: Optional[bool] = None
    oa_doaj_success_status: Optional[bool] = None
    oa_status: Optional[OAStatus] = None
    upw_oa_status: Optional[UnpaywallOAStatus] = None
    coar_oa_status: Optional[str] = None
