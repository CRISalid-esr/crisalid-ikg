from pydantic import BaseModel


class VoidCustomMetadata(BaseModel):
    """
    Empty submodel for Source record models without  custom metadata.
    """
