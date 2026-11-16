from datetime import date
from enum import StrEnum

from sqlalchemy import Date, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ApplicationSource(StrEnum):
    LINKEDIN = "linkedin"
    COMPANY_WEBSITE = "company_website"
    JOB_BOARD = "job_board"
    REFERRAL = "referral"
    OTHER = "other"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    position: Mapped[str] = mapped_column(String(200))
    job_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    source: Mapped[ApplicationSource] = mapped_column(
        Enum(
            ApplicationSource,
            name="application_source",
            values_callable=lambda e: [member.value for member in e],
            validate_strings=True,
        )
    )
    applied_on: Mapped[date] = mapped_column(Date, default=date.today)
