from sqlalchemy import select
from sqlalchemy.orm import Session

from app.applications.models import Application
from app.applications.service import apply_state_change  # &line[AutoAdvanceToInterview]
from app.applications.states import ApplicationState  # &line[AutoAdvanceToInterview]
from app.interviews.models import Interview
from app.interviews.schemas import InterviewCreate, InterviewUpdate


def _get_owned(db: Session, application_id: int, interview_id: int) -> Interview | None:
    """The interview, but only if it belongs to the given application."""
    interview = db.get(Interview, interview_id)
    if interview is None or interview.application_id != application_id:
        return None
    return interview


# &begin[AutoAdvanceToInterview]
# Scheduling an interview implies the application has reached the interview stage.
_ADVANCE_TO_INTERVIEW_FROM = frozenset({ApplicationState.APPLIED, ApplicationState.SCREENING})
_NO_INTERVIEWS_IN = frozenset({ApplicationState.REJECTED, ApplicationState.WITHDRAWN})


class InterviewNotAllowed(Exception):
    def __init__(self, state: ApplicationState):
        self.state = state
        super().__init__(f"Cannot schedule an interview for an application in state '{state}'.")
# &end[AutoAdvanceToInterview]


# &begin[AddInterview]
def add_interview(
    db: Session, application_id: int, payload: InterviewCreate
) -> Interview | None:
    """None if the application doesn't exist."""
    application = db.get(Application, application_id)  # &line[AutoAdvanceToInterview]
    if application is None:
        return None
    # &begin[AutoAdvanceToInterview]
    if application.state in _NO_INTERVIEWS_IN:
        raise InterviewNotAllowed(application.state)
    if application.state in _ADVANCE_TO_INTERVIEW_FROM:
        # Same transaction as the interview, so state, history and interview stay consistent.
        apply_state_change(application, ApplicationState.INTERVIEW, comment="Interview scheduled")
    # &end[AutoAdvanceToInterview]
    interview = Interview(application_id=application_id, **payload.model_dump())
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview
# &end[AddInterview]


# &begin[ListInterviews]
def list_interviews(db: Session, application_id: int) -> list[Interview] | None:
    """All interviews of an application, earliest first; None if it doesn't exist."""
    if db.get(Application, application_id) is None:
        return None
    stmt = (
        select(Interview)
        .where(Interview.application_id == application_id)
        .order_by(Interview.scheduled_at, Interview.id)
    )
    return list(db.scalars(stmt))
# &end[ListInterviews]


# &begin[UpdateInterview]
def update_interview(
    db: Session, application_id: int, interview_id: int, payload: InterviewUpdate
) -> Interview | None:
    interview = _get_owned(db, application_id, interview_id)
    if interview is None:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interview, field, value)
    db.commit()
    db.refresh(interview)
    return interview
# &end[UpdateInterview]


# &begin[DeleteInterview]
def delete_interview(db: Session, application_id: int, interview_id: int) -> bool:
    interview = _get_owned(db, application_id, interview_id)
    if interview is None:
        return False
    db.delete(interview)
    db.commit()
    return True
# &end[DeleteInterview]
