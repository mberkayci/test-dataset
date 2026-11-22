from sqlalchemy import Connection, inspect, text

from app.core.db import migration

PLACEHOLDER_LOCATION = "Unknown"


@migration
def company_name_to_company_reference(conn: Connection) -> None:
    """Older databases store the company as free text on each application. Create one
    company per distinct name (case-insensitive, location unknown), point applications
    at it and drop the text column."""
    columns = {c["name"] for c in inspect(conn).get_columns("applications")}
    if "company" not in columns:
        return
    rows = conn.execute(text("SELECT id, company FROM applications")).all()
    if "company_id" not in columns:
        conn.execute(text(
            "ALTER TABLE applications ADD COLUMN company_id INTEGER REFERENCES companies(id)"
        ))
    company_ids = {
        name.lower(): id_
        for id_, name in conn.execute(text("SELECT id, name FROM companies"))
    }
    for application_id, raw_name in rows:
        name = (raw_name or "").strip() or "Unknown company"
        key = name.lower()
        if key not in company_ids:
            company_ids[key] = conn.execute(
                text("INSERT INTO companies (name, location) VALUES (:name, :location) RETURNING id"),
                {"name": name, "location": PLACEHOLDER_LOCATION},
            ).scalar_one()
        conn.execute(
            text("UPDATE applications SET company_id = :cid WHERE id = :id"),
            {"cid": company_ids[key], "id": application_id},
        )
    conn.execute(text("ALTER TABLE applications DROP COLUMN company"))
