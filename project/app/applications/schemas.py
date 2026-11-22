from datetime import date
from datetime import UTC, datetime  # &line[StateHistory]
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, field_validator

from app.applications.models import ApplicationSource
from app.applications.states import ApplicationState  # &line[ApplicationState]

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


# &begin[CreateApplication]
class ApplicationCreate(BaseModel):
    company_id: int  # &line[ApplicationCompany]
    position: NonEmptyStr
    job_url: HttpUrl | None = None
    source: ApplicationSource
    applied_on: date = Field(default_factory=date.today)
# &end[CreateApplication]


# &begin[UpdateApplication]
class ApplicationUpdate(BaseModel):
    """Partial update: only fields present in the request body are changed."""

    company_id: int | None = None  # &line[ApplicationCompany]
    position: NonEmptyStr | None = None
    job_url: HttpUrl | None = None
    source: ApplicationSource | None = None
    applied_on: date | None = None

    @field_validator("company_id", "position", "source", "applied_on", mode="before")
    @classmethod
    def reject_null(cls, value):
        # These columns are required; only job_url may be cleared with null.
        if value is None:
            raise ValueError("field cannot be null")
        return value
# &end[UpdateApplication]


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # &begin[ApplicationCompany]
    company_id: int
    company_name: str
    # &end[ApplicationCompany]
    position: str
    job_url: str | None
    source: ApplicationSource
    applied_on: date
    state: ApplicationState  # &line[ApplicationState]


# &begin[ChangeState]
class StateChange(BaseModel):
    state: ApplicationState
    # &begin[StateHistory]
    comment: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None = None

    @field_validator("comment")
    @classmethod
    def blank_comment_is_none(cls, value: str | None) -> str | None:
        return value or None
    # &end[StateHistory]
# &end[ChangeState]


# &begin[StateHistory]
class StateChangeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_state: ApplicationState
    to_state: ApplicationState
    changed_at: datetime
    comment: str | None

    @field_validator("changed_at")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        # SQLite drops the timezone; timestamps are always stored in UTC.
        return value if value.tzinfo else value.replace(tzinfo=UTC)
# &end[StateHistory]
