import pytest


def _create(client, **overrides):
    body = {"name": "Acme", "location": "Berlin", **overrides}
    return client.post("/companies", json=body)


# &begin[CreateCompany]
def test_create_company_minimal(client):
    res = _create(client)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Acme"
    assert data["location"] == "Berlin"
    assert data["website"] is None
    assert data["notes"] is None


def test_create_company_with_all_fields(client):
    res = _create(client, website="https://acme.example", notes="  Great culture  ")
    assert res.status_code == 201
    assert res.json()["website"] == "https://acme.example/"
    assert res.json()["notes"] == "Great culture"


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": "  "},
        {"name": None},
        {"location": ""},
        {"location": None},
        {"website": "not a url"},
        {"notes": "x" * 2001},
    ],
)
def test_create_company_rejects_invalid_input(client, overrides):
    assert _create(client, **overrides).status_code == 422


def test_create_company_requires_location(client):
    assert client.post("/companies", json={"name": "Acme"}).status_code == 422


def test_create_company_rejects_duplicate_name(client):
    _create(client)
    res = _create(client, name="  ACME ")
    assert res.status_code == 409
    assert len(client.get("/companies").json()) == 1
# &end[CreateCompany]


# &begin[ListCompanies]
def test_list_companies_sorted_by_name(client):
    for name in ["zeta", "Beta", "alpha"]:
        _create(client, name=name)
    res = client.get("/companies")
    assert res.status_code == 200
    assert [c["name"] for c in res.json()] == ["alpha", "Beta", "zeta"]


def test_list_companies_empty(client):
    assert client.get("/companies").json() == []
# &end[ListCompanies]


# &begin[ViewCompany]
def test_view_company(client):
    company_id = _create(client).json()["id"]
    assert client.get(f"/companies/{company_id}").json()["name"] == "Acme"
    assert client.get("/companies/999").status_code == 404
# &end[ViewCompany]


# &begin[UpdateCompany]
def test_update_company_partial(client):
    company_id = _create(client, notes="Initial").json()["id"]
    res = client.patch(f"/companies/{company_id}", json={"location": "Munich"})
    assert res.status_code == 200
    data = res.json()
    assert data["location"] == "Munich"
    assert data["name"] == "Acme"
    assert data["notes"] == "Initial"


def test_update_company_can_clear_optional_fields(client):
    company_id = _create(client, website="https://acme.example", notes="Initial").json()["id"]
    res = client.patch(f"/companies/{company_id}", json={"website": None, "notes": None})
    assert res.json()["website"] is None
    assert res.json()["notes"] is None


@pytest.mark.parametrize("body", [{"name": None}, {"location": None}, {"name": " "}, {"website": "x"}])
def test_update_company_rejects_invalid_input(client, body):
    company_id = _create(client).json()["id"]
    assert client.patch(f"/companies/{company_id}", json=body).status_code == 422


def test_update_company_rejects_duplicate_name(client):
    _create(client, name="Globex")
    company_id = _create(client).json()["id"]
    assert client.patch(f"/companies/{company_id}", json={"name": "globex"}).status_code == 409
    # Renaming to its own name (different case) is fine.
    res = client.patch(f"/companies/{company_id}", json={"name": "ACME"})
    assert res.status_code == 200
    assert res.json()["name"] == "ACME"


def test_update_unknown_company(client):
    assert client.patch("/companies/999", json={"location": "Munich"}).status_code == 404
# &end[UpdateCompany]


# &begin[DeleteCompany]
def test_delete_company(client):
    company_id = _create(client).json()["id"]
    assert client.delete(f"/companies/{company_id}").status_code == 204
    assert client.get(f"/companies/{company_id}").status_code == 404
    assert client.delete(f"/companies/{company_id}").status_code == 404


def test_deleted_company_name_can_be_reused(client):
    company_id = _create(client).json()["id"]
    client.delete(f"/companies/{company_id}")
    assert _create(client).status_code == 201
# &end[DeleteCompany]
