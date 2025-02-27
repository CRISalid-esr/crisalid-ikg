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

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        """
        Build a unique identifier for the structured address by concatenating its fields.
        :param values:
        :return:
        """
        values['uid'] = cls._generate_uid(values)
        return values

    @staticmethod
    def _generate_uid(values):
        """
        Generate a unique identifier for the structured address by concatenating its fields
        Sort literals by language to ensure consistency
        :param values:
        :return:
        """
        return "-".join(
            [f"{literal.language}-{literal.value}" for literal in sorted(
                values['street'] + values['city'] + values['zip_code'] + values[
                    'state_or_province'] + values['country'],
                key=lambda literal: literal.language)]
        )
