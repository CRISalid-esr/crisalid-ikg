import json
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, model_validator, Field, field_validator, AliasChoices

from app.models.change_report import ChangeWarning


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
    action_type: Literal["ADD", "REMOVE", "UPDATE", "MERGE"] = Field(
        validation_alias=AliasChoices("actionType", "action_type")
    )
    path: Optional[str] = None
    parameters: dict
    timestamp: datetime
    status: ChangeStatus = ChangeStatus.CREATED
    error_message: Optional[str] = None  # if status == FAILED
    warnings: list[ChangeWarning] = []  # per-item losses

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

    @field_validator("warnings", mode="before")
    @classmethod
    def _unmarshal_warnings(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON in warnings field") from e
        return v

    def marshal_parameters(self) -> str:
        """
        Convert parameters to a JSON string for storage.
        """
        return json.dumps(self.parameters, ensure_ascii=False)

    def marshal_warnings(self) -> str:
        """
        Convert warnings to a JSON string for storage.
        """
        return json.dumps([warning.model_dump() for warning in self.warnings],
                          ensure_ascii=False)

    def to_event_fields(self) -> dict:
        """
        Build the JSON-safe ``fields`` payload of an outbound change event message.
        """
        return {
            "uid": self.uid,
            "id": self.id,
            "application": self.application,
            "person_uid": self.person_uid,
            # false positive: pylint infers FieldInfo for the aliased field
            "target_type": self.target_type.value,  # pylint: disable=no-member
            "target_uid": self.target_uid,
            "path": self.path,
            "action_type": self.action_type,
            "status": self.status.value,
            "error_message": self.error_message,
            "warnings": [warning.model_dump() for warning in self.warnings],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
