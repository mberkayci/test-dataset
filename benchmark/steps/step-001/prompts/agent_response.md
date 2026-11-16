The job application tracker API is built in `app/`. All 10 tests pass, and I also ran it once against a real SQLite file: creating and then listing an application worked, and the date defaulted to today.

**Endpoints** (in `app/routers/applications.py`, with the logic in `app/services/applications.py`):

| Method | Path                 | Result                                                        |
| ------ | -------------------- | ------------------------------------------------------------- |
| POST   | `/applications`      | Creates an application (201). `applied_on` defaults to today. |
| GET    | `/applications`      | Lists applications, most recently applied first.              |
| GET    | `/applications/{id}` | Returns one application, or 404.                              |
| PATCH  | `/applications/{id}` | Changes only the fields you send.                             |
| DELETE | `/applications/{id}` | Deletes it (204), or 404.                                     |

**Other files:**
- The database model is in `app/models/application.py`. `source` only accepts linkedin, company_website, job_board, referral or other.
- The request and response formats are in `app/schemas/application.py`. Company and position can't be blank, and `job_url` must be a valid URL if you give one.
- The database setup is in `app/db.py`. The file is `./applications.db` unless you set `DATABASE_URL`, and the table is created when the app starts.
- The tests in `app/tests/test_applications.py` use an in-memory database.

**Choices I made that you may want to change:**
- Updates use PATCH rather than PUT, so you can change one field without resending the rest. You can clear `job_url` by sending `null`, but sending `null` for company, position, source or date is rejected.
- A URL with no path gets a trailing slash when saved, so `https://acme.com` is stored as `https://acme.com/`.

**Feature tracking:** there was no feature model, so I created `.feature-model`. The root is `JobApplicationTracker`, with `Database` and `Applications` under it, and `Applications` has `CreateApplication`, `ListApplications`, `ViewApplication`, `UpdateApplication` and `DeleteApplication`. All the new code is annotated against these, and I checked that every annotation names a feature in the model. The summary has been shown in the Agent HAnS window.

Nothing is committed. There's no `.gitignore` yet, so `applications.db` and `__pycache__/` will show up as untracked files. I can add one if you'd like.

To run the server: `.venv\Scripts\python -m uvicorn app.main:app --reload`. The interactive API docs are then at `http://127.0.0.1:8000/docs`.


I reorganized the project by feature, and nothing about the API changed. All 10 tests still pass, whether you run `pytest` or `python -m pytest`. The endpoints are the same: `GET`/`POST /applications`, `GET`/`PATCH`/`DELETE /applications/{application_id}`, and `/`.

```
app/
  main.py
  core/
    db.py            ← was app/db.py
  applications/
    models.py        ← was models/application.py
    schemas.py       ← was schemas/application.py
    service.py       ← was services/applications.py
    router.py        ← was routers/applications.py
tests/
  conftest.py        ← test database setup, moved out of the test file
  test_applications.py
```

- **Imports:** I updated them in `main.py`, the new modules and the tests. Nothing still imports from the old paths.
- **Old folders:** `models/`, `schemas/`, `services/`, `routers/` and `app/tests/` are deleted, along with their `__init__.py` and cache files.
- **Tests setup:** `tests/__init__.py` is there so a plain `pytest` run from the project root can find the `app` package.
- **Feature tracking:** the feature model itself is unchanged, because no features were added or removed. I rewrote the `.feature-to-file` mappings for the new locations and checked that every annotation still names a real feature. The summary has been shown in the Agent HAnS window.

Nothing is committed yet. Because none of these files had been committed before, git will just show the new layout as new files.