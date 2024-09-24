from pydantic import BaseModel

class DocumentType(BaseModel):
    """
    Document Type model
    """
    uri: str
    label: str
