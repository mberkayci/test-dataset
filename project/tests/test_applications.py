from datetime import date

import pytest


def _create(client, **overrides):
    body = {"company": "Acme", "position": "Backend Engineer", "source": "linkedin", **overrides}
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
    "overrides", [{"source": "newspaper"}, {"company": "  "}, {"job_url": "not a url"}]
)
def test_create_rejects_invalid_input(client, overrides):
    assert _create(client, **overrides).status_code == 422
# &end[CreateApplication]


# &begin[ListApplications]
def test_list_newest_first(client):
    _create(client, company="Old", applied_on="2026-01-01")
    _create(client, company="New", applied_on="2026-06-01")
    res = client.get("/applications")
    assert res.status_code == 200
    assert [a["company"] for a in res.json()] == ["New", "Old"]
# &end[ListApplications]


# &begin[ViewApplication]
def test_view_application(client):
    app_id = _create(client).json()["id"]
    assert client.get(f"/applications/{app_id}").json()["company"] == "Acme"
    assert client.get("/applications/999").status_code == 404
# &end[ViewApplication]


# &begin[UpdateApplication]
def test_partial_update(client):
    app_id = _create(client, job_url="https://acme.example/jobs/1").json()["id"]
    res = client.patch(f"/applications/{app_id}", json={"position": "Staff Engineer"})
    assert res.status_code == 200
    assert res.json()["position"] == "Staff Engineer"
    assert res.json()["company"] == "Acme"
    assert res.json()["job_url"] == "https://acme.example/jobs/1"


def test_update_can_clear_job_url_but_not_required_fields(client):
    app_id = _create(client, job_url="https://acme.example/jobs/1").json()["id"]
    assert client.patch(f"/applications/{app_id}", json={"job_url": None}).json()["job_url"] is None
    assert client.patch(f"/applications/{app_id}", json={"company": None}).status_code == 422
    assert client.patch("/applications/999", json={"position": "X"}).status_code == 404
# &end[UpdateApplication]


# &begin[DeleteApplication]
def test_delete_application(client):
    app_id = _create(client).json()["id"]
    assert client.delete(f"/applications/{app_id}").status_code == 204
    assert client.get(f"/applications/{app_id}").status_code == 404
    assert client.delete(f"/applications/{app_id}").status_code == 404
# &end[DeleteApplication]
