import pytest
from sqlalchemy import create_engine, inspect, text

from app.applications.states import ALLOWED_TRANSITIONS, ApplicationState
from tests.helpers import company_id  # &line[ApplicationCompany]


def _create(client, **overrides):
    body = {"company_id": company_id(client), "position": "Backend Engineer", "source": "linkedin", **overrides}  # &line[ApplicationCompany]
    return client.post("/applications", json=body).json()


def _move(client, app_id, state):
    return client.post(f"/applications/{app_id}/state", json={"state": state})


def test_new_application_starts_applied(client):
    app = _create(client)
    assert app["state"] == "applied"
    assert client.get(f"/applications/{app['id']}").json()["state"] == "applied"


def test_state_cannot_be_set_on_create_or_update(client):
    app = _create(client, state="offer")
    assert app["state"] == "applied"
    res = client.patch(f"/applications/{app['id']}", json={"state": "offer"})
    assert res.json()["state"] == "applied"


# &begin[ChangeState]
def test_full_happy_path(client):
    app_id = _create(client)["id"]
    for state in ["screening", "interview", "offer"]:
        res = _move(client, app_id, state)
        assert res.status_code == 200, res.json()
        assert res.json()["state"] == state


def test_screening_can_be_skipped(client):
    app_id = _create(client)["id"]
    assert _move(client, app_id, "interview").status_code == 200


def test_applied_cannot_jump_to_offer(client):
    app_id = _create(client)["id"]
    res = _move(client, app_id, "offer")
    assert res.status_code == 409
    assert res.json()["detail"] == (
        "Cannot change state from 'applied' to 'offer'. "
        "Allowed next states: interview, rejected, screening, withdrawn."
    )
    assert client.get(f"/applications/{app_id}").json()["state"] == "applied"


def test_cannot_move_backwards(client):
    app_id = _create(client)["id"]
    _move(client, app_id, "interview")
    assert _move(client, app_id, "screening").status_code == 409
    assert _move(client, app_id, "applied").status_code == 409


@pytest.mark.parametrize("final", ["rejected", "withdrawn"])
def test_final_states_are_locked(client, final):
    app_id = _create(client)["id"]
    assert _move(client, app_id, final).status_code == 200
    res = _move(client, app_id, "screening")
    assert res.status_code == 409
    assert res.json()["detail"] == f"Application is in final state '{final}' and cannot be changed."


def test_same_state_is_rejected(client):
    app_id = _create(client)["id"]
    res = _move(client, app_id, "applied")
    assert res.status_code == 409
    assert res.json()["detail"] == "Application is already in state 'applied'."


def test_offer_can_be_withdrawn_or_rejected(client):
    for final in ["withdrawn", "rejected"]:
        app_id = _create(client)["id"]
        for state in ["interview", "offer", final]:
            assert _move(client, app_id, state).status_code == 200


def test_change_state_errors(client):
    assert _move(client, 999, "screening").status_code == 404
    app_id = _create(client)["id"]
    assert _move(client, app_id, "hired").status_code == 422


def test_every_state_has_a_transition_rule():
    assert set(ALLOWED_TRANSITIONS) == set(ApplicationState)
# &end[ChangeState]


# &begin[FilterByState]
def test_filter_by_state(client):
    a = _create(client, position="A")["id"]
    b = _create(client, position="B")["id"]
    _create(client, position="C")
    _move(client, a, "screening")
    _move(client, b, "rejected")

    def positions(query):
        return sorted(x["position"] for x in client.get(f"/applications{query}").json())

    assert positions("?state=screening") == ["A"]
    assert positions("?state=screening&state=rejected") == ["A", "B"]
    assert positions("?state=offer") == []
    assert positions("") == ["A", "B", "C"]
    assert client.get("/applications?state=hired").status_code == 422
# &end[FilterByState]


# &begin[Database]
def test_init_db_adds_state_column_to_existing_table(tmp_path):
    from app.core.db import init_db

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE applications (id INTEGER PRIMARY KEY, company VARCHAR(200) NOT NULL, "
            "position VARCHAR(200) NOT NULL, job_url VARCHAR(2048), source VARCHAR(15) NOT NULL, "
            "applied_on DATE NOT NULL)"
        ))
        conn.execute(text(
            "INSERT INTO applications (company, position, source, applied_on) "
            "VALUES ('Old Co', 'Dev', 'other', '2026-01-01')"
        ))
    init_db(engine)
    init_db(engine)  # idempotent
    assert "state" in {c["name"] for c in inspect(engine).get_columns("applications")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT state FROM applications")).scalar_one() == "applied"
    engine.dispose()
# &end[Database]
