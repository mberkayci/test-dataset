from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, field_validator

from app.applications.models import ApplicationSource

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


# &begin[CreateApplication]
class ApplicationCreate(BaseModel):
    company: NonEmptyStr
    position: NonEmptyStr
    job_url: HttpUrl | None = None
    source: ApplicationSource
    applied_on: date = Field(default_factory=date.today)
# &end[CreateApplication]


# &begin[UpdateApplication]
class ApplicationUpdate(BaseModel):
    """Partial update: only fields present in the request body are changed."""

    company: NonEmptyStr | None = None
    position: NonEmptyStr | None = None
    job_url: HttpUrl | None = None
    source: ApplicationSource | None = None
    applied_on: date | None = None

    @field_validator("company", "position", "source", "applied_on", mode="before")
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
    company: str
    position: str
    job_url: str | None
    source: ApplicationSource
    applied_on: date
