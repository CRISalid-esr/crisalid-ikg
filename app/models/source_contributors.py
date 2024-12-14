from pydantic import BaseModel


class SourceContributor(BaseModel):
    """
    Source Contributor model
    """
    name: str
