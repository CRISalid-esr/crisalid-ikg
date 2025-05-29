from typing import List, Optional

from pydantic import BaseModel


class HalCustomMetadata(BaseModel):
    """
    Submodel for HAL source records custom metadata.
    """
    hal_collection_codes: Optional[List[str]] = None
    hal_submit_type: Optional[str] = None
