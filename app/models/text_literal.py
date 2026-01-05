import hashlib

from pydantic import computed_field

from app.models.literal import Literal


class TextLiteral(Literal):
    """
    Long literal value (abstracts, descriptions).

    Not indexed on value; deduplicated via hash key.
    """
    value: str  # override: no max_length

    @computed_field
    @property
    def key(self) -> str:
        """
        Stable hash key for deduplication.
        Includes language + value.
        """
        payload = f"{self.language}|{self.value}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
