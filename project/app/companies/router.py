from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.companies import service
from app.companies.schemas import CompanyCreate, CompanyRead, CompanyUpdate
from app.companies.service import DuplicateCompanyName
from app.companies.service import CompanyHasApplications  # &line[ApplicationCompany]
from app.core.db import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")


def _conflict(exc: DuplicateCompanyName) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# &begin[CreateCompany]
@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    try:
        return service.create_company(db, payload)
    except DuplicateCompanyName as exc:
        raise _conflict(exc) from exc
# &end[CreateCompany]


# &begin[ListCompanies]
@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    return service.list_companies(db)
# &end[ListCompanies]


# &begin[ViewCompany]
@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = service.get_company(db, company_id)
    if company is None:
        raise _not_found()
    return company
# &end[ViewCompany]


# &begin[UpdateCompany]
@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    try:
        company = service.update_company(db, company_id, payload)
    except DuplicateCompanyName as exc:
        raise _conflict(exc) from exc
    if company is None:
        raise _not_found()
    return company
# &end[UpdateCompany]


# &begin[DeleteCompany]
@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    # &begin[ApplicationCompany]
    try:
        deleted = service.delete_company(db, company_id)
    except CompanyHasApplications as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    # &end[ApplicationCompany]
    if not deleted:
        raise _not_found()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
# &end[DeleteCompany]
