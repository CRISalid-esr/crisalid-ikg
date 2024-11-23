from typing import List, Optional

from pydantic import BaseModel

from app.models.literal import Literal


class Document(BaseModel):
    """
    Document model
    """

    titles: Optional[List[Literal]] = None

    to_be_recomputed: bool = False
