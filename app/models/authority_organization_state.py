from __future__ import annotations

import re
import unicodedata
from typing import List, Optional

from pydantic import field_validator

from app.models.agent_identifiers import OrganizationIdentifier
from app.models.authority_organization import AuthorityOrganization
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.source_organizations import SourceOrganization


class AuthorityOrganizationState(AuthorityOrganization):
    """
    Consistent identity state for an organization.
    """

    type: SourceOrganization.SourceOrganisationType = (
        SourceOrganization.SourceOrganisationType.ORGANIZATION
    )

    names: List[Literal] = []
    normalized_name: Optional[str] = None

    identifiers: List[OrganizationIdentifier] = []
    excluded_identifiers: List[OrganizationIdentifierType] = []

    @classmethod
    def compute_normalized_name(cls, name: str) -> str:
        """
        Normalize an organization name for deduplication / matching.

        Rules:
        - strip
        - lowercase
        - remove diacritics
        - replace punctuation by spaces
        - normalize whitespace
        """
        spaces = re.compile(r"\s+")
        punctuation = re.compile(r"[^\w\s]", re.UNICODE)
        s = (name or "").strip()
        if not s:
            return ""

        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower()
        s = punctuation.sub("", s)
        s = spaces.sub("", s).strip()
        return s

    @classmethod
    def _pick_best_name(cls, names: List[Literal]) -> Optional[str]:
        """
        Choose a non-empty value. If several, take the longest
        """
        chosen = None
        for name in names or []:
            if name.value and (chosen is None or len(name.value) > len(chosen)):
                chosen = name.value
        return chosen

    def _normalize_name(self) -> None:
        """
        Compute normalized_name if not provided.
        """
        chosen = self._pick_best_name(self.names)
        if chosen:
            self.normalized_name = self.compute_normalized_name(chosen)
        else:
            self.normalized_name = None

    def set_names(self, names: List[Literal]) -> None:
        """
        Set names, compute display_names, and recompute normalized_name.

        - trims values
        - removes empties
        - deduplicates by (language, value) (language optional)
        - stores display_names as a list[str] of distinct raw values
        - recomputes normalized_name from the "best" name (see _pick_best_name)
        """
        new_names: list[Literal] = []
        seen_names: set[tuple[Optional[str], str]] = set()
        seen_display_seen: set[str] = set()
        display_names: list[str] = []

        for name in names or []:
            if not name or not name.value:
                continue
            value = name.value.strip()
            if not value:
                continue

            lang = getattr(name, "language", None)
            key = (lang, value)
            if key in seen_names:
                continue
            seen_names.add(key)

            new_names.append(Literal(value=value, language=lang))

            if value not in seen_display_seen:
                seen_display_seen.add(value)
                display_names.append(value)

        self.names = new_names
        self.display_names = display_names
        self._normalize_name()

    @field_validator("identifiers", mode="after")
    @classmethod
    def _deduplicate_identifiers(cls, identifiers: List[OrganizationIdentifier]):
        seen = set()
        out = []
        for ident in identifiers or []:
            key = (ident.type, ident.value)
            if key not in seen:
                seen.add(key)
                out.append(ident)
        return out
