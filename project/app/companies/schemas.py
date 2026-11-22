from typing import Annotated

from pydantic import BaseModel, ConfigDict, HttpUrl, StringConstraints, field_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


# &begin[CreateCompany]
class CompanyCreate(BaseModel):
    name: NonEmptyStr
    website: HttpUrl | None = None
    location: NonEmptyStr
    notes: Notes | None = None

    @field_validator("notes")
    @classmethod
    def blank_notes_is_none(cls, value: str | None) -> str | None:
        return value or None
# &end[CreateCompany]


# &begin[UpdateCompany]
class CompanyUpdate(BaseModel):
    """Partial update: only fields present in the request body are changed."""

    name: NonEmptyStr | None = None
    website: HttpUrl | None = None
    location: NonEmptyStr | None = None
    notes: Notes | None = None

    @field_validator("name", "location", mode="before")
    @classmethod
    def reject_null(cls, value):
        # These columns are required; only website and notes may be cleared with null.
        if value is None:
            raise ValueError("field cannot be null")
        return value

    @field_validator("notes")
    @classmethod
    def blank_notes_is_none(cls, value: str | None) -> str | None:
        return value or None
# &end[UpdateCompany]


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: str | None
    location: str
    notes: str | None
