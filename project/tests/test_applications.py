from datetime import date

import pytest
from sqlalchemy import create_engine, inspect, text

from tests.helpers import company_id  # &line[ApplicationCompany]


def _create(client, **overrides):
    body = {"company_id": company_id(client), "position": "Backend Engineer", "source": "linkedin", **overrides}  # &line[ApplicationCompany]
    return client.post("/applications", json=body)


# &begin[CreateApplication]
def test_create_defaults_applied_on_to_today(client):
    res = _create(client)
    assert res.status_code == 201
    data = res.json()
    assert data["applied_on"] == date.today().isoformat()
    assert data["job_url"] is None
    assert data["source"] == "linkedin"


def test_create_with_all_fields(client):
    res = _create(
        client, job_url="https://acme.example/jobs/1", source="referral", applied_on="2026-10-01"
    )
    assert res.status_code == 201
    assert res.json()["job_url"] == "https://acme.example/jobs/1"
    assert res.json()["applied_on"] == "2026-10-01"


@pytest.mark.parametrize(
    "overrides", [{"source": "newspaper"}, {"position": "  "}, {"job_url": "not a url"}]
)
def test_create_rejects_invalid_input(client, overrides):
    assert _create(client, **overrides).status_code == 422
# &end[CreateApplication]


# &begin[ListApplications]
def test_list_newest_first(client):
    _create(client, position="Old", applied_on="2026-01-01")
    _create(client, position="New", applied_on="2026-06-01")
    res = client.get("/applications")
    assert res.status_code == 200
    assert [a["position"] for a in res.json()] == ["New", "Old"]
# &end[ListApplications]


# &begin[ViewApplication]
def test_view_application(client):
    app_id = _create(client).json()["id"]
    assert client.get(f"/applications/{app_id}").json()["company_name"] == "Acme"  # &line[ApplicationCompany]
    assert client.get("/applications/999").status_code == 404
# &end[ViewApplication]


# &begin[UpdateApplication]
def test_partial_update(client):
    app_id = _create(client, job_url="https://acme.example/jobs/1").json()["id"]
    res = client.patch(f"/applications/{app_id}", json={"position": "Staff Engineer"})
    assert res.status_code == 200
    assert res.json()["position"] == "Staff Engineer"
    assert res.json()["company_name"] == "Acme"  # &line[ApplicationCompany]
    assert res.json()["job_url"] == "https://acme.example/jobs/1"


def test_update_can_clear_job_url_but_not_required_fields(client):
    app_id = _create(client, job_url="https://acme.example/jobs/1").json()["id"]
    assert client.patch(f"/applications/{app_id}", json={"job_url": None}).json()["job_url"] is None
    assert client.patch(f"/applications/{app_id}", json={"company_id": None}).status_code == 422  # &line[ApplicationCompany]
    assert client.patch("/applications/999", json={"position": "X"}).status_code == 404
# &end[UpdateApplication]


# &begin[DeleteApplication]
def test_delete_application(client):
    app_id = _create(client).json()["id"]
    assert client.delete(f"/applications/{app_id}").status_code == 204
    assert client.get(f"/applications/{app_id}").status_code == 404
    assert client.delete(f"/applications/{app_id}").status_code == 404
# &end[DeleteApplication]


# &begin[ApplicationCompany]
def test_application_shows_company(client):
    acme = company_id(client, "Acme")
    data = _create(client, company_id=acme).json()
    assert (data["company_id"], data["company_name"]) == (acme, "Acme")
    assert "company" not in data
    listed = client.get("/applications").json()[0]
    assert (listed["company_id"], listed["company_name"]) == (acme, "Acme")


def test_company_rename_is_reflected_in_application(client):
    acme = company_id(client, "Acme")
    app_id = _create(client, company_id=acme).json()["id"]
    client.patch(f"/companies/{acme}", json={"name": "Acme Corp"})
    assert client.get(f"/applications/{app_id}").json()["company_name"] == "Acme Corp"


def test_create_requires_existing_company(client):
    body = {"position": "Dev", "source": "linkedin"}
    assert client.post("/applications", json=body).status_code == 422
    res = client.post("/applications", json={**body, "company_id": 999})
    assert res.status_code == 422
    assert "999" in res.json()["detail"]
    assert client.get("/applications").json() == []


def test_update_moves_application_to_other_company(client):
    app_id = _create(client, company_id=company_id(client, "Acme")).json()["id"]
    globex = company_id(client, "Globex")
    res = client.patch(f"/applications/{app_id}", json={"company_id": globex})
    assert res.status_code == 200
    assert (res.json()["company_id"], res.json()["company_name"]) == (globex, "Globex")


def test_update_rejects_unknown_company(client):
    acme = company_id(client)
    app_id = _create(client, company_id=acme).json()["id"]
    assert client.patch(f"/applications/{app_id}", json={"company_id": 999}).status_code == 422
    assert client.get(f"/applications/{app_id}").json()["company_id"] == acme


def test_company_with_applications_cannot_be_deleted(client):
    acme = company_id(client)
    app_id = _create(client, company_id=acme).json()["id"]
    res = client.delete(f"/companies/{acme}")
    assert res.status_code == 409
    assert "1 application" in res.json()["detail"]
    assert client.get(f"/companies/{acme}").status_code == 200
    # Once its applications are gone the company can be deleted.
    client.delete(f"/applications/{app_id}")
    assert client.delete(f"/companies/{acme}").status_code == 204


def test_init_db_migrates_company_names_to_companies(tmp_path):
    from app.core.db import init_db

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE applications (id INTEGER PRIMARY KEY, company VARCHAR(200) NOT NULL, "
            "position VARCHAR(200) NOT NULL, job_url VARCHAR(2048), source VARCHAR(15) NOT NULL, "
            "applied_on DATE NOT NULL)"
        ))
        conn.execute(text(
            "INSERT INTO applications (company, position, source, applied_on) VALUES "
            "('Acme', 'Dev', 'other', '2026-01-01'), ('acme ', 'Ops', 'other', '2026-01-02'), "
            "('Globex', 'QA', 'other', '2026-01-03')"
        ))
    init_db(engine)
    init_db(engine)  # idempotent
    columns = {c["name"] for c in inspect(engine).get_columns("applications")}
    assert "company" not in columns and "company_id" in columns
    with engine.connect() as conn:
        companies = conn.execute(text("SELECT name, location FROM companies ORDER BY name")).all()
        assert [tuple(c) for c in companies] == [("Acme", "Unknown"), ("Globex", "Unknown")]
        rows = conn.execute(text(
            "SELECT a.position, c.name FROM applications a JOIN companies c ON c.id = a.company_id "
            "ORDER BY a.id"
        )).all()
        assert [tuple(r) for r in rows] == [("Dev", "Acme"), ("Ops", "Acme"), ("QA", "Globex")]
    engine.dispose()
# &end[ApplicationCompany]
