from __future__ import annotations

from typing import Optional, List
from uuid import uuid4

from pydantic import BaseModel


class AuthorityOrganization(BaseModel):
    """
    One consistent identity state for an organization.
    """
    uid: Optional[str] = None

    # List of source organization UIDs contributing to this authority organization
    source_organization_uids: List[str] = []

    def random_uid(self):
        """
        assign a random uuid4 string to uid if not already set
        """
        if not self.uid:
            self.uid = str(uuid4())
