from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.applications.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate
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
def list_applications(db: Session = Depends(get_db)):
    return service.list_applications(db)
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
