from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.applications.models import Application
from app.applications.schemas import ApplicationCreate, ApplicationUpdate


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
def list_applications(db: Session) -> list[Application]:
    stmt = select(Application).order_by(Application.applied_on.desc(), Application.id.desc())
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
