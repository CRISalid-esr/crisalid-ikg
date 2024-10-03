from typing import List, Optional

from pydantic import BaseModel, model_validator

from app.models.literal import Literal


class Concept(BaseModel):
    """
    Subject model (follows RDF Skos concept schema)
    """
    uri: Optional[str] = None
    pref_labels: List[Literal] = []
    alt_labels: List[Literal] = []

    @model_validator(mode="after")
    def _check_labels(self):
        if self.uri is None:
            if len(self.pref_labels) != 1:
                raise ValueError("When uri is None, there must be exactly one pref_label.")
            if self.alt_labels:
                raise ValueError("When uri is None, alt_labels must be empty.")
        return self
