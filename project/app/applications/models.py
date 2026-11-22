from datetime import date
from datetime import UTC, datetime  # &line[StateHistory]
from enum import StrEnum

from sqlalchemy import Date, Enum, String
from sqlalchemy import DateTime, ForeignKey  # &line[StateHistory]
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship  # &line[StateHistory]

from app.applications.states import ApplicationState  # &line[ApplicationState]
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
    # &begin[ApplicationState]
    state: Mapped[ApplicationState] = mapped_column(
        Enum(
            ApplicationState,
            name="application_state",
            values_callable=lambda e: [member.value for member in e],
            validate_strings=True,
        ),
        default=ApplicationState.APPLIED,
        server_default=ApplicationState.APPLIED.value,
        index=True,
    )
    # &end[ApplicationState]
    # &begin[StateHistory]
    state_changes: Mapped[list["StateChangeRecord"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="(StateChangeRecord.changed_at, StateChangeRecord.id)",
    )
    # &end[StateHistory]


# &begin[StateHistory]
def _state_enum(name: str) -> Enum:
    return Enum(
        ApplicationState,
        name=name,
        values_callable=lambda e: [member.value for member in e],
        validate_strings=True,
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


class StateChangeRecord(Base):
    __tablename__ = "application_state_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    from_state: Mapped[ApplicationState] = mapped_column(_state_enum("application_state_from"))
    to_state: Mapped[ApplicationState] = mapped_column(_state_enum("application_state_to"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    comment: Mapped[str | None] = mapped_column(String(1000), default=None)

    application: Mapped[Application] = relationship(back_populates="state_changes")
# &end[StateHistory]
