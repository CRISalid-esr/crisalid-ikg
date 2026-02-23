from pydantic import BaseModel


class SourcePersonIdentifier(BaseModel):
    """
    Source Organization Identifier API model
    """

    type: str
    value: str
