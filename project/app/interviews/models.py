from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class InterviewType(StrEnum):
    PHONE = "phone"
    VIDEO = "video"
    ON_SITE = "on_site"
    TECHNICAL = "technical"
    HR = "hr"


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    # Always stored in UTC (SQLite drops the offset, so it is re-attached on read).
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[InterviewType] = mapped_column(
        Enum(
            InterviewType,
            name="interview_type",
            values_callable=lambda e: [member.value for member in e],
            validate_strings=True,
        )
    )
    notes: Mapped[str | None] = mapped_column(String(2000), default=None)

    application: Mapped["Application"] = relationship(back_populates="interviews")  # noqa: F821
