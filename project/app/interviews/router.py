from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.interviews import service
from app.interviews.schemas import InterviewCreate, InterviewRead, InterviewUpdate
from app.interviews.service import InterviewNotAllowed  # &line[AutoAdvanceToInterview]

router = APIRouter(prefix="/applications/{application_id}/interviews", tags=["interviews"])


def _application_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")


def _interview_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")


# &begin[AddInterview]
@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
def add_interview(application_id: int, payload: InterviewCreate, db: Session = Depends(get_db)):
    # &begin[AutoAdvanceToInterview]
    try:
        interview = service.add_interview(db, application_id, payload)
    except InterviewNotAllowed as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    # &end[AutoAdvanceToInterview]
    if interview is None:
        raise _application_not_found()
    return interview
# &end[AddInterview]


# &begin[ListInterviews]
@router.get("", response_model=list[InterviewRead])
def list_interviews(application_id: int, db: Session = Depends(get_db)):
    interviews = service.list_interviews(db, application_id)
    if interviews is None:
        raise _application_not_found()
    return interviews
# &end[ListInterviews]


# &begin[UpdateInterview]
@router.patch("/{interview_id}", response_model=InterviewRead)
def update_interview(
    application_id: int,
    interview_id: int,
    payload: InterviewUpdate,
    db: Session = Depends(get_db),
):
    interview = service.update_interview(db, application_id, interview_id, payload)
    if interview is None:
        raise _interview_not_found()
    return interview
# &end[UpdateInterview]


# &begin[DeleteInterview]
@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(application_id: int, interview_id: int, db: Session = Depends(get_db)):
    if not service.delete_interview(db, application_id, interview_id):
        raise _interview_not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# &end[DeleteInterview]
