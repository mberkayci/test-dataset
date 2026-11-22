from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.applications.models import Application
from app.applications.models import StateChangeRecord  # &line[StateHistory]
from app.applications.schemas import ApplicationCreate, ApplicationUpdate
from app.applications.states import ApplicationState, ensure_transition_allowed  # &line[ApplicationState]


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    # HttpUrl objects are stored as plain strings.
    if data.get("job_url") is not None:
        data["job_url"] = str(data["job_url"])
    return data


# &begin[CreateApplication]
def create_application(db: Session, payload: ApplicationCreate) -> Application:
    application = Application(**_normalize(payload.model_dump()))
    db.add(application)
    db.commit()
    db.refresh(application)
    return application
# &end[CreateApplication]


# &begin[ListApplications]
def list_applications(
    db: Session,
    states: list[ApplicationState] | None = None,  # &line[FilterByState]
) -> list[Application]:
    stmt = select(Application).order_by(Application.applied_on.desc(), Application.id.desc())
    # &begin[FilterByState]
    if states:
        stmt = stmt.where(Application.state.in_(states))
    # &end[FilterByState]
    return list(db.scalars(stmt))
# &end[ListApplications]


# &begin[ViewApplication]
def get_application(db: Session, application_id: int) -> Application | None:
    return db.get(Application, application_id)
# &end[ViewApplication]


# &begin[UpdateApplication]
def update_application(
    db: Session, application_id: int, payload: ApplicationUpdate
) -> Application | None:
    application = db.get(Application, application_id)
    if application is None:
        return None
    for field, value in _normalize(payload.model_dump(exclude_unset=True)).items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application
# &end[UpdateApplication]


# &begin[DeleteApplication]
def delete_application(db: Session, application_id: int) -> bool:
    application = db.get(Application, application_id)
    if application is None:
        return False
    db.delete(application)
    db.commit()
    return True
# &end[DeleteApplication]


# &begin[ChangeState]
def change_state(
    db: Session,
    application_id: int,
    new_state: ApplicationState,
    comment: str | None = None,  # &line[StateHistory]
) -> Application | None:
    """Move an application to a new state. Raises InvalidStateTransition if not allowed."""
    application = db.get(Application, application_id)
    if application is None:
        return None
    apply_state_change(
        application, new_state,
        comment=comment,  # &line[StateHistory]
    )
    db.commit()
    db.refresh(application)
    return application


def apply_state_change(
    application: Application,
    new_state: ApplicationState,
    comment: str | None = None,  # &line[StateHistory]
) -> None:
    """Validate and apply a state change without committing, so callers can bundle it
    into a larger transaction. Raises InvalidStateTransition if not allowed."""
    ensure_transition_allowed(application.state, new_state)
    # &begin[StateHistory]
    # Recorded in the same transaction as the state change, so history never drifts.
    application.state_changes.append(
        StateChangeRecord(from_state=application.state, to_state=new_state, comment=comment)
    )
    # &end[StateHistory]
    application.state = new_state
# &end[ChangeState]


# &begin[StateHistory]
def get_state_history(db: Session, application_id: int) -> list[StateChangeRecord] | None:
    """All state changes of an application, oldest first; None if it doesn't exist."""
    if db.get(Application, application_id) is None:
        return None
    stmt = (
        select(StateChangeRecord)
        .where(StateChangeRecord.application_id == application_id)
        .order_by(StateChangeRecord.changed_at, StateChangeRecord.id)
    )
    return list(db.scalars(stmt))
# &end[StateHistory]
