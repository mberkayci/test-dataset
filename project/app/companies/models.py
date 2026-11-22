from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    website: Mapped[str | None] = mapped_column(String(2048), default=None)
    location: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(String(2000), default=None)
