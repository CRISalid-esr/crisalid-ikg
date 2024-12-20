from pydantic import BaseModel


class SourceOrganizationIdentifier(BaseModel):
    """
    Source Organization Identifier API model
    """

    type: str
    value: str
