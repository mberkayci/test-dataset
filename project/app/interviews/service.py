from sqlalchemy import select
from sqlalchemy.orm import Session

from app.applications.models import Application
from app.interviews.models import Interview
from app.interviews.schemas import InterviewCreate, InterviewUpdate


def _get_owned(db: Session, application_id: int, interview_id: int) -> Interview | None:
    """The interview, but only if it belongs to the given application."""
    interview = db.get(Interview, interview_id)
    if interview is None or interview.application_id != application_id:
        return None
    return interview


# &begin[AddInterview]
def add_interview(
    db: Session, application_id: int, payload: InterviewCreate
) -> Interview | None:
    """None if the application doesn't exist."""
    if db.get(Application, application_id) is None:
        return None
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
