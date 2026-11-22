Applications now have a state, there's an endpoint to change it, and you can filter the list by state. All 24 tests pass: the 10 existing ones plus 14 new ones.

**Allowed state changes:**

| From                | Can move to                               |
| ------------------- | ----------------------------------------- |
| applied             | screening, interview, rejected, withdrawn |
| screening           | interview, rejected, withdrawn            |
| interview           | offer, rejected, withdrawn                |
| offer               | rejected, withdrawn                       |
| rejected, withdrawn | nothing (these are final)                 |

States only move forward. Screening can be skipped, since some companies invite you straight to an interview. An offer always needs an interview first. Rejected covers an offer being taken back, and withdrawn covers you turning it down. Tell me if you want different rules; they're all in one table in `app/applications/states.py`.

**API changes:**
- **Every application** now includes `state` in its response. New applications always start as `applied`.
- **Changing state:** `POST /applications/{id}/state` with `{"state": "interview"}`. A change that isn't allowed is refused with a 409 error and a message, for example: *"Cannot change state from 'applied' to 'offer'. Allowed next states: interview, rejected, screening, withdrawn."* Final states and "already in this state" get their own messages. An unknown application returns 404, and an invalid state name returns 422.
- **Filtering:** `GET /applications?state=interview`. You can repeat it, as in `?state=screening&state=interview`.
- **No other way to set state:** a `state` sent to create or PATCH is ignored, so the rules can't be bypassed.

**Your existing database:** `applications.db` was created before states existed, and the usual table creation never adds columns to existing tables. So the app now adds any missing columns when it starts (in `app/core/db.py`), and existing applications become `applied`. I tested this on a copy of your database file and in a test. It's a lightweight approach; if the schema keeps changing, a proper migration tool like Alembic would be the better choice.

**Feature tracking:** I added `ApplicationState` to the feature model under `Applications`, with `ChangeState` and `FilterByState` beneath it. `ListApplications` and `Database` were modified. Every annotation names a feature in the model and opens and closes correctly. The summary has been shown in the Agent HAnS window.

Nothing is committed yet.

---

Every state change is now saved to a history, and you can view an application's full history, oldest change first. All 32 tests pass: the 24 existing ones plus 8 new ones. I also tried it on a copy of your `applications.db`: the history table was created on startup and recorded a change correctly.

**How to use it:**
- **Adding a comment:** the state change endpoint takes an optional comment: `POST /applications/{id}/state` with `{"state": "screening", "comment": "Recruiter call booked"}`.
- **Viewing the history:** `GET /applications/{id}/history` returns a 404 if the application doesn't exist. Otherwise it returns entries like:
  ```json
  [{"id": 1, "from_state": "applied", "to_state": "screening",
    "changed_at": "2026-11-16T02:01:44.777474Z", "comment": "Recruiter call booked"}]
  ```

**How it behaves:**
- **When it's recorded:** each entry is saved together with the state change itself, so the history can't get out of step with the current state.
- **Refused changes:** when a change is refused (the 409 errors), nothing is recorded.
- **Times** are stored and returned in UTC.
- **Comments** have spaces trimmed from the ends and are limited to 1000 characters. A blank comment is saved as empty (`null`).
- **Deleting** an application also deletes its history.
- **Storage:** the history lives in a new `application_state_changes` table, created automatically on startup, so your existing database needs nothing extra.

**One choice you may want to change:** creating an application doesn't add a history entry, because it has no previous state. A new application's history is therefore empty until its first change, and the `applied_on` date marks where it started. If you'd prefer creation to be logged too, with an empty previous state, that's a small change.

**Feature tracking:** I added `StateHistory` to the feature model under `ApplicationState`. `ChangeState` was modified, because it now takes a comment and writes the history. `Database` was modified only in the test setup, which now lets tests look at the database directly. All annotations check out, and the summary has been shown in the Agent HAnS window.

Nothing is committed yet.