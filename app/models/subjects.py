from typing import List, Optional

from pydantic import BaseModel

from app.models.literal import Literal


class Subject(BaseModel):
    """
    Subject model (follows RDF Skos concept schema)
    """
    uri: Optional[str] = None
    pref_labels: List[Literal] = []
    alt_labels: List[Literal] = []
