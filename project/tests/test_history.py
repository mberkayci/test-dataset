from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.applications.models import StateChangeRecord
from tests.helpers import company_id  # &line[ApplicationCompany]


def _create(client):
    body = {"company_id": company_id(client), "position": "Backend Engineer", "source": "linkedin"}  # &line[ApplicationCompany]
    return client.post("/applications", json=body).json()["id"]


def _move(client, app_id, state, comment=None):
    body = {"state": state} if comment is None else {"state": state, "comment": comment}
    return client.post(f"/applications/{app_id}/state", json=body)


def _history(client, app_id):
    return client.get(f"/applications/{app_id}/history")


def test_new_application_has_empty_history(client):
    res = _history(client, _create(client))
    assert res.status_code == 200
    assert res.json() == []


def test_history_records_each_change_oldest_first(client):
    app_id = _create(client)
    before = datetime.now(UTC)
    _move(client, app_id, "screening", comment="Recruiter call booked")
    _move(client, app_id, "interview")
    _move(client, app_id, "offer", comment="  Verbal offer  ")
    after = datetime.now(UTC)

    history = _history(client, app_id).json()
    assert [(h["from_state"], h["to_state"]) for h in history] == [
        ("applied", "screening"),
        ("screening", "interview"),
        ("interview", "offer"),
    ]
    assert [h["comment"] for h in history] == ["Recruiter call booked", None, "Verbal offer"]

    times = [datetime.fromisoformat(h["changed_at"]) for h in history]
    assert all(t.tzinfo is not None for t in times)
    assert times == sorted(times)
    assert before - timedelta(seconds=1) <= times[0] and times[-1] <= after + timedelta(seconds=1)


def test_blank_comment_stored_as_null(client):
    app_id = _create(client)
    _move(client, app_id, "screening", comment="   ")
    assert _history(client, app_id).json()[0]["comment"] is None


def test_rejected_transition_is_not_recorded(client):
    app_id = _create(client)
    assert _move(client, app_id, "offer").status_code == 409
    assert _history(client, app_id).json() == []


def test_comment_too_long_is_rejected(client):
    app_id = _create(client)
    assert _move(client, app_id, "screening", comment="x" * 1001).status_code == 422
    assert _history(client, app_id).json() == []


def test_history_is_per_application(client):
    a, b = _create(client), _create(client)
    _move(client, a, "rejected")
    assert len(_history(client, a).json()) == 1
    assert _history(client, b).json() == []


def test_history_unknown_application(client):
    assert _history(client, 999).status_code == 404


def test_deleting_application_deletes_its_history(client, db_session):
    app_id = _create(client)
    _move(client, app_id, "screening")
    client.delete(f"/applications/{app_id}")
    remaining = db_session.scalars(
        select(StateChangeRecord).where(StateChangeRecord.application_id == app_id)
    ).all()
    assert remaining == []
