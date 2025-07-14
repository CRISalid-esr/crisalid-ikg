import json
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, model_validator, Field, field_validator, AliasChoices


class ChangeStatus(str, Enum):
    """
    Status of a change in the system.
    """
    CREATED = "created"
    APPLIED = "applied"
    FAILED = "failed"


class TargetType(str, Enum):
    """
    Type of the target node that the change applies to.
    """
    DOCUMENT = "DOCUMENT"
    PROJECT = "PROJECT"
    PERSON = "PERSON"


class Change(BaseModel):
    """
    Change node representing a user action on a graph object (e.g., Document).
    Stored in Neo4j and replayed after document remerges.
    """

    uid: str
    # allow validation of both snake_case and camelCase (from AMQP messages)
    target_uid: str = Field(validation_alias=AliasChoices("targetUid", "target_uid"))
    target_type: TargetType = Field(validation_alias=AliasChoices("targetType", "target_type"))
    person_uid: str = Field(validation_alias=AliasChoices("personUid", "person_uid"))
    application: str
    id: str  # unique within the source application
    action: Literal["ADD", "REMOVE", "UPDATE"]
    path: str  # e.g., "subjects", "titles"
    parameters: dict
    timestamp: datetime
    status: ChangeStatus = ChangeStatus.CREATED
    error_message: Optional[str] = None  # if status == FAILED

    @model_validator(mode="before")
    @classmethod
    def compute_uid(cls, values: dict) -> dict:
        """
        Automatically compute uid from application and id.
        """
        if not values.get("uid"):
            app = values.get("application")
            raw_id = values.get("id")
            if not app or not raw_id:
                raise ValueError("application and id must be provided to compute uid")
            values["uid"] = f"{app}:{raw_id}"
        return values

    @field_validator("parameters", mode="before")
    @classmethod
    def _unmarshal_parameters(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON in parameters field") from e
        return v

    def marshal_parameters(self) -> str:
        """
        Convert parameters to a JSON string for storage.
        """
        return json.dumps(self.parameters, ensure_ascii=False)
