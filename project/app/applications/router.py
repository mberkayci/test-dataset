from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.applications.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
from app.applications.schemas import StateChange  # &line[ChangeState]
from app.applications.schemas import StateChangeRead  # &line[StateHistory]
from app.applications.states import ApplicationState, InvalidStateTransition  # &line[ApplicationState]
from app.applications import service

router = APIRouter(prefix="/applications", tags=["applications"])


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")


# &begin[CreateApplication]
@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    return service.create_application(db, payload)
# &end[CreateApplication]


# &begin[ListApplications]
@router.get("", response_model=list[ApplicationRead])
def list_applications(
    # &begin[FilterByState]
    state: list[ApplicationState] | None = Query(
        default=None, description="Only return applications in these states (repeatable)."
    ),
    # &end[FilterByState]
    db: Session = Depends(get_db),
):
    return service.list_applications(db, states=state)  # &line[FilterByState]
# &end[ListApplications]


# &begin[ViewApplication]
@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application_id: int, db: Session = Depends(get_db)):
    application = service.get_application(db, application_id)
    if application is None:
        raise _not_found()
    return application
# &end[ViewApplication]


# &begin[UpdateApplication]
@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)
):
    application = service.update_application(db, application_id, payload)
    if application is None:
        raise _not_found()
    return application
# &end[UpdateApplication]


# &begin[DeleteApplication]
@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    if not service.delete_application(db, application_id):
        raise _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# &end[DeleteApplication]


# &begin[ChangeState]
@router.post("/{application_id}/state", response_model=ApplicationRead)
def change_state(application_id: int, payload: StateChange, db: Session = Depends(get_db)):
    try:
        application = service.change_state(
            db, application_id, payload.state,
            comment=payload.comment,  # &line[StateHistory]
        )
    except InvalidStateTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if application is None:
        raise _not_found()
    return application
# &end[ChangeState]


# &begin[StateHistory]
@router.get("/{application_id}/history", response_model=list[StateChangeRead])
def get_state_history(application_id: int, db: Session = Depends(get_db)):
    history = service.get_state_history(db, application_id)
    if history is None:
        raise _not_found()
    return history
# &end[StateHistory]
