from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from app.interviews.models import InterviewType

Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


def _to_utc(value: datetime) -> datetime:
    # Times without an offset are taken as UTC; times with one are converted to UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# &begin[AddInterview]
class InterviewCreate(BaseModel):
    scheduled_at: datetime
    type: InterviewType
    notes: Notes | None = None

    @field_validator("scheduled_at")
    @classmethod
    def normalize_scheduled_at(cls, value: datetime) -> datetime:
        return _to_utc(value)

    @field_validator("notes")
    @classmethod
    def blank_notes_is_none(cls, value: str | None) -> str | None:
        return value or None
# &end[AddInterview]


# &begin[UpdateInterview]
class InterviewUpdate(BaseModel):
    """Partial update: only fields present in the request body are changed."""

    scheduled_at: datetime | None = None
    type: InterviewType | None = None
    notes: Notes | None = None

    @field_validator("scheduled_at", "type", mode="before")
    @classmethod
    def reject_null(cls, value):
        # These columns are required; only notes may be cleared with null.
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("scheduled_at")
    @classmethod
    def normalize_scheduled_at(cls, value: datetime) -> datetime:
        return _to_utc(value)

    @field_validator("notes")
    @classmethod
    def blank_notes_is_none(cls, value: str | None) -> str | None:
        return value or None
# &end[UpdateInterview]


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    scheduled_at: datetime
    type: InterviewType
    notes: str | None

    @field_validator("scheduled_at")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        return _to_utc(value)
