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