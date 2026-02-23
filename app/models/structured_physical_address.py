"""
Structured Physical Address Model (CERIF-compliant)
"""
from typing import List, Optional

from pydantic import BaseModel, model_validator

from app.models.literal import Literal


class StructuredPhysicalAddress(BaseModel):
    """
    CERIF-compliant structured physical address with multilingual support.
    """
    uid: Optional[str] = None

    street: List[Literal] = []
    city: List[Literal] = []
    zip_code: List[Literal] = []
    state_or_province: List[Literal] = []
    country: List[Literal] = []
    continent: Optional[List[Literal]] = []

    @model_validator(mode="after")
    def _build_uid(self):
        if not self.uid:
            self.uid = self._generate_uid()
        return self

    def _generate_uid(self) -> str:
        literals = self.street + self.city + self.zip_code + self.state_or_province + self.country
        literals = [lit for lit in literals if lit.value]
        literals.sort(key=lambda lit: lit.language or '')
        return "-".join(f"{lit.language}-{lit.value}" for lit in literals)
