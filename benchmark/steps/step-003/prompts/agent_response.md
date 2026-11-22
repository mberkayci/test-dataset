You can now add interviews to an application, list them sorted by date, update them and delete them. The full test suite passes (52 tests), including the new interview tests.

**Endpoints** (all under `/applications/{application_id}/interviews`):

| Action | Request                  | Notes                                                                                                |
| ------ | ------------------------ | ---------------------------------------------------------------------------------------------------- |
| Add    | `POST`                   | Body: `scheduled_at`, `type`, optional `notes`                                                       |
| List   | `GET`                    | Earliest interview first                                                                             |
| Update | `PATCH /{interview_id}`  | Changes only the fields you send. `notes` can be cleared with `null`; the other fields can't be null |
| Delete | `DELETE /{interview_id}` | Returns 204                                                                                          |

**Behaviour:**
- **Types:** `phone`, `video`, `on_site`, `technical`, `hr`.
- **Time zones:** times are stored in UTC. A time with an offset (e.g. `+02:00`) is converted to UTC, and a time without one is treated as UTC. If you send local times without an offset, they will be stored as if they were UTC.
- **Notes:** limited to 2000 characters. Spaces at the start and end are trimmed, and blank notes are saved as `null`.
- **Not found:** you get a 404 if the application doesn't exist, or if the interview belongs to a different application.
- **Deleting an application** also deletes its interviews.

**Code:** it's in a new `app/interviews/` package (`models.py`, `schemas.py`, `service.py`, `router.py`). I also added a relationship to `Application` in `app/applications/models.py`, registered the router in `app/main.py`, and wrote tests in `tests/test_interviews.py`. The existing `init_db()` creates the `interviews` table in your existing database on the next startup.

**Feature model:** I added `Interviews` under `Applications`, with children `AddInterview`, `ListInterviews`, `UpdateInterview` and `DeleteInterview`. The new files are linked to `Interviews` through `.feature-to-file`, and annotations mark the parts of the code that belong to each child feature.
---
Scheduling an interview now moves the application forward automatically, and it's blocked for rejected or withdrawn applications. All 59 tests pass, including the new ones.

**How it behaves:**
- **Applied or screening:** the application moves to interview. A normal entry, `applied → interview` or `screening → interview`, is added to the state history with the comment "Interview scheduled". The state change, the history entry and the interview are saved together, so you can't end up with only some of them.
- **Rejected or withdrawn:** scheduling is refused with an error saying why (HTTP 409). No interview is created and the state stays as it was.
- **Interview or offer:** the interview is added, but the state and history are left alone. So a second interview doesn't add another history entry, and an offer doesn't get moved back.

**Changes:**
- **`app/applications/service.py`:** I pulled the existing "check the move is allowed, record history, set the state" steps out of `change_state` into a helper, `apply_state_change`, that doesn't save on its own. Interview scheduling reuses it, so the history entry looks exactly like one from a manual state change.
- **`app/interviews/service.py` and `app/interviews/router.py`:** the new check before an interview is added, and the 409 error.
- **`tests/test_interviews.py`:** tests for each case above.
- **`.feature-model`:** new feature `AutoAdvanceToInterview` under `AddInterview`. All new code is annotated with it.

**Two choices to check:**
- **History comment:** "Interview scheduled" is a fixed text I picked.
- **Test run:** the project has no virtual environment and pytest isn't installed, so I ran the tests in a temporary one at `/tmp/claude-1000/-home-mba-Desktop-UNI-thesis-test-dataset-project/b7b9f244-ee47-4119-8fbf-54d73b2507e8/scratchpad/venv`. Nothing was installed in your project.