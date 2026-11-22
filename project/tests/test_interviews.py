import pytest
from sqlalchemy import select

from app.interviews.models import Interview
from tests.helpers import company_id  # &line[ApplicationCompany]


def _create_application(client):
    body = {"company_id": company_id(client), "position": "Backend Engineer", "source": "linkedin"}  # &line[ApplicationCompany]
    return client.post("/applications", json=body).json()["id"]


def _add(client, app_id, **overrides):
    body = {"scheduled_at": "2026-12-01T10:00:00Z", "type": "phone", **overrides}
    return client.post(f"/applications/{app_id}/interviews", json=body)


def _list(client, app_id):
    return client.get(f"/applications/{app_id}/interviews")


# &begin[AddInterview]
def test_add_interview(client):
    app_id = _create_application(client)
    res = _add(client, app_id, type="on_site", notes="  Bring portfolio  ")
    assert res.status_code == 201
    data = res.json()
    assert data["application_id"] == app_id
    assert data["type"] == "on_site"
    assert data["notes"] == "Bring portfolio"
    assert data["scheduled_at"] == "2026-12-01T10:00:00Z"


def test_add_interview_notes_optional_and_blank_is_null(client):
    app_id = _create_application(client)
    assert _add(client, app_id).json()["notes"] is None
    assert _add(client, app_id, notes="   ").json()["notes"] is None


def test_add_interview_converts_offset_to_utc(client):
    app_id = _create_application(client)
    res = _add(client, app_id, scheduled_at="2026-12-01T10:00:00+02:00")
    assert res.json()["scheduled_at"] == "2026-12-01T08:00:00Z"


@pytest.mark.parametrize(
    "overrides",
    [
        {"type": "lunch"},
        {"scheduled_at": "tomorrow"},
        {"scheduled_at": None},
        {"notes": "x" * 2001},
    ],
)
def test_add_interview_rejects_invalid_input(client, overrides):
    app_id = _create_application(client)
    assert _add(client, app_id, **overrides).status_code == 422


def test_add_interview_unknown_application(client):
    assert _add(client, 999).status_code == 404
# &end[AddInterview]


# &begin[ListInterviews]
def test_list_interviews_sorted_by_date(client):
    app_id = _create_application(client)
    _add(client, app_id, scheduled_at="2026-12-10T09:00:00Z", type="technical")
    _add(client, app_id, scheduled_at="2026-12-01T09:00:00Z", type="phone")
    _add(client, app_id, scheduled_at="2026-12-05T14:30:00Z", type="hr")
    res = _list(client, app_id)
    assert res.status_code == 200
    assert [i["type"] for i in res.json()] == ["phone", "hr", "technical"]


def test_list_interviews_is_per_application(client):
    a, b = _create_application(client), _create_application(client)
    _add(client, a)
    assert len(_list(client, a).json()) == 1
    assert _list(client, b).json() == []


def test_list_interviews_unknown_application(client):
    assert _list(client, 999).status_code == 404
# &end[ListInterviews]


# &begin[UpdateInterview]
def test_update_interview_partial(client):
    app_id = _create_application(client)
    interview = _add(client, app_id, notes="Initial").json()
    res = client.patch(
        f"/applications/{app_id}/interviews/{interview['id']}",
        json={"scheduled_at": "2026-12-02T15:00:00Z", "type": "video"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scheduled_at"] == "2026-12-02T15:00:00Z"
    assert data["type"] == "video"
    assert data["notes"] == "Initial"


def test_update_interview_can_clear_notes(client):
    app_id = _create_application(client)
    interview = _add(client, app_id, notes="Initial").json()
    res = client.patch(f"/applications/{app_id}/interviews/{interview['id']}", json={"notes": None})
    assert res.json()["notes"] is None


@pytest.mark.parametrize("body", [{"type": None}, {"scheduled_at": None}, {"type": "lunch"}])
def test_update_interview_rejects_invalid_input(client, body):
    app_id = _create_application(client)
    interview = _add(client, app_id).json()
    res = client.patch(f"/applications/{app_id}/interviews/{interview['id']}", json=body)
    assert res.status_code == 422


def test_update_interview_of_other_application_is_not_found(client):
    a, b = _create_application(client), _create_application(client)
    interview = _add(client, a).json()
    res = client.patch(f"/applications/{b}/interviews/{interview['id']}", json={"type": "hr"})
    assert res.status_code == 404
    assert client.patch(f"/applications/{a}/interviews/999", json={"type": "hr"}).status_code == 404
# &end[UpdateInterview]


# &begin[DeleteInterview]
def test_delete_interview(client):
    app_id = _create_application(client)
    keep = _add(client, app_id, scheduled_at="2026-12-01T09:00:00Z").json()
    drop = _add(client, app_id, scheduled_at="2026-12-02T09:00:00Z").json()
    res = client.delete(f"/applications/{app_id}/interviews/{drop['id']}")
    assert res.status_code == 204
    assert [i["id"] for i in _list(client, app_id).json()] == [keep["id"]]
    assert client.delete(f"/applications/{app_id}/interviews/{drop['id']}").status_code == 404


def test_delete_interview_of_other_application_is_not_found(client):
    a, b = _create_application(client), _create_application(client)
    interview = _add(client, a).json()
    assert client.delete(f"/applications/{b}/interviews/{interview['id']}").status_code == 404
    assert len(_list(client, a).json()) == 1
# &end[DeleteInterview]


def test_deleting_application_deletes_its_interviews(client, db_session):
    app_id = _create_application(client)
    _add(client, app_id)
    client.delete(f"/applications/{app_id}")
    remaining = db_session.scalars(
        select(Interview).where(Interview.application_id == app_id)
    ).all()
    assert remaining == []


# &begin[AutoAdvanceToInterview]
def _move(client, app_id, state):
    return client.post(f"/applications/{app_id}/state", json={"state": state})


def _app(client, app_id):
    return client.get(f"/applications/{app_id}").json()


def _history(client, app_id):
    return client.get(f"/applications/{app_id}/history").json()


@pytest.mark.parametrize("path", [[], ["screening"]])
def test_add_interview_advances_application_to_interview(client, path):
    app_id = _create_application(client)
    for state in path:
        _move(client, app_id, state)
    before = path[-1] if path else "applied"
    assert _add(client, app_id).status_code == 201
    assert _app(client, app_id)["state"] == "interview"
    last = _history(client, app_id)[-1]
    assert (last["from_state"], last["to_state"]) == (before, "interview")
    assert last["comment"] == "Interview scheduled"


@pytest.mark.parametrize("path", [["interview"], ["interview", "offer"]])
def test_add_interview_keeps_later_states(client, path):
    app_id = _create_application(client)
    for state in path:
        _move(client, app_id, state)
    history_before = _history(client, app_id)
    assert _add(client, app_id).status_code == 201
    assert _app(client, app_id)["state"] == path[-1]
    assert _history(client, app_id) == history_before


def test_second_interview_does_not_add_history(client):
    app_id = _create_application(client)
    _add(client, app_id)
    _add(client, app_id)
    assert len(_history(client, app_id)) == 1
    assert len(_list(client, app_id).json()) == 2


@pytest.mark.parametrize("final_state", ["rejected", "withdrawn"])
def test_add_interview_blocked_for_final_states(client, final_state):
    app_id = _create_application(client)
    _move(client, app_id, final_state)
    res = _add(client, app_id)
    assert res.status_code == 409
    assert final_state in res.json()["detail"]
    assert _list(client, app_id).json() == []
    assert _app(client, app_id)["state"] == final_state
    assert len(_history(client, app_id)) == 1
# &end[AutoAdvanceToInterview]
