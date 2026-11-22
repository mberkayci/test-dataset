import os
from collections.abc import Callable, Generator

from sqlalchemy import Connection, Engine, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.schema import CreateColumn

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./applications.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Data migrations that the automatic column-adding below can't handle (e.g. replacing
# a column). Each runs on every startup after create_all and must be idempotent.
MIGRATIONS: list[Callable[[Connection], None]] = []


def migration(fn: Callable[[Connection], None]) -> Callable[[Connection], None]:
    MIGRATIONS.append(fn)
    return fn


def init_db(bind: Engine = engine) -> None:
    """Create missing tables, and add columns that were added to a model after its
    table was created (create_all never alters existing tables). New columns need a
    server_default or must be nullable so existing rows get a value."""
    Base.metadata.create_all(bind=bind)
    with bind.begin() as conn:
        for run in MIGRATIONS:
            run(conn)
    inspector = inspect(bind)
    with bind.begin() as conn:
        for table in Base.metadata.sorted_tables:
            existing = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                if not column.nullable and column.server_default is None:
                    raise RuntimeError(
                        f"Cannot add NOT NULL column {table.name}.{column.name} without a server_default"
                    )
                ddl = CreateColumn(column).compile(dialect=bind.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))
            for index in table.indexes:
                index.create(conn, checkfirst=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
