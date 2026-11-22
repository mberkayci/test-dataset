from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.applications.models import Application  # &line[ApplicationCompany]
from app.companies.models import Company
from app.companies.schemas import CompanyCreate, CompanyUpdate


class DuplicateCompanyName(Exception):
    def __init__(self, name: str):
        self.name = name
        super().__init__(f"A company named '{name}' already exists.")


# &begin[ApplicationCompany]
class CompanyHasApplications(Exception):
    def __init__(self, count: int):
        self.count = count
        super().__init__(
            f"Company still has {count} application(s); delete or reassign them first."
        )
# &end[ApplicationCompany]


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    # HttpUrl objects are stored as plain strings.
    if data.get("website") is not None:
        data["website"] = str(data["website"])
    return data


def _ensure_name_free(db: Session, name: str, exclude_id: int | None = None) -> None:
    """Company names are unique, ignoring case."""
    stmt = select(Company.id).where(func.lower(Company.name) == name.lower())
    if exclude_id is not None:
        stmt = stmt.where(Company.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise DuplicateCompanyName(name)


# &begin[CreateCompany]
def create_company(db: Session, payload: CompanyCreate) -> Company:
    """Raises DuplicateCompanyName if the name is taken."""
    _ensure_name_free(db, payload.name)
    company = Company(**_normalize(payload.model_dump()))
    db.add(company)
    db.commit()
    db.refresh(company)
    return company
# &end[CreateCompany]


# &begin[ListCompanies]
def list_companies(db: Session) -> list[Company]:
    stmt = select(Company).order_by(func.lower(Company.name), Company.id)
    return list(db.scalars(stmt))
# &end[ListCompanies]


# &begin[ViewCompany]
def get_company(db: Session, company_id: int) -> Company | None:
    return db.get(Company, company_id)
# &end[ViewCompany]


# &begin[UpdateCompany]
def update_company(db: Session, company_id: int, payload: CompanyUpdate) -> Company | None:
    """None if the company doesn't exist. Raises DuplicateCompanyName if the name is taken."""
    company = db.get(Company, company_id)
    if company is None:
        return None
    changes = _normalize(payload.model_dump(exclude_unset=True))
    if "name" in changes:
        _ensure_name_free(db, changes["name"], exclude_id=company_id)
    for field, value in changes.items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
# &end[UpdateCompany]


# &begin[DeleteCompany]
def delete_company(db: Session, company_id: int) -> bool:
    """False if the company doesn't exist. Raises CompanyHasApplications if it is in use."""
    company = db.get(Company, company_id)
    if company is None:
        return False
    # &begin[ApplicationCompany]
    count = db.scalar(
        select(func.count()).select_from(Application).where(Application.company_id == company_id)
    )
    if count:
        raise CompanyHasApplications(count)
    # &end[ApplicationCompany]
    db.delete(company)
    db.commit()
    return True
# &end[DeleteCompany]
