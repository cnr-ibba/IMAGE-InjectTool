# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

IMAGE InjectTool: a Django web app that imports animal/sample metadata from several sources (Cryoweb DB dumps, CRB-Anim CSV, Excel templates), validates it against ontologies/dictionaries, and submits it to EBI BioSamples through USI. Everything runs under Docker Compose; there is no host-side Python environment. The Django project lives in `django-data/image/` (bind-mounted into the containers at `/var/uwsgi/image/`).

## Commands

Run everything through `docker compose` from the repo root (needs a `.env` file; see README.md for required variables such as `POSTGRES_PASSWORD`, `IMAGE_USER`, `IMAGE_PASSWORD`, `CRYOWEB_INSERT_ONLY_PW`, `SECRET_KEY`, `USI_MANAGER*`). `postgres-data/` must not exist on first run, since DB init scripts in `postgres/docker-entrypoint-initdb.d/` only run on an empty data dir.

```bash
docker compose build
docker compose up -d                                   # add -f docker-compose-devel.yml for celery-flower (port 5555)
docker compose run --rm uwsgi python manage.py migrate
docker compose run --rm uwsgi python manage.py initializedb   # fills default dictionary tables

# tests (pytest-django, settings in django-data/image/pytest.ini)
docker compose run --rm uwsgi pytest
docker compose run --rm uwsgi pytest uid/tests/test_models.py
docker compose run --rm uwsgi pytest --verbosity=2 path/to/test.py::Class::test_name

# CI runs tests with coverage; wait-for-postgres avoids racing the db container
docker compose run --no-deps --rm uwsgi /root/wait-for-postgres.sh coverage run --source='.' -m py.test

# sphinx docs
docker compose run --rm uwsgi bash -c "cd docs; make html"
```

CI (`.github/workflows/docker-compose-workflow.yml`) runs on `master` and `devel`; `devel` is the working branch, `master` the release branch. Version is managed with `bumpversion` (`.bumpversion.cfg`). Commits use gitmoji shortcodes. The repo uses git LFS and submodules (`git clone --recursive`).

Note: the README still references an `image_app` app in some examples; it no longer exists. Use the real app names below.

## Architecture

**Containers** (`docker-compose.yml`): `db` (postgres), `redis`, `uwsgi` (Django via uwsgi), `asgi` (daphne, websockets on 8001), `celery-worker`, `celery-beat` (DatabaseScheduler), `nginx` (port 26080). All Django-based containers share the same `./uwsgi` image and the same bind-mounted code.

**Two databases** (`image/settings.py`, `image/routers.py`): `default` (`image`) holds all app data; `cryoweb` holds a staging copy of the Cryoweb schema (`search_path=apiis_admin`). `CryowebRouter` pins the `cryoweb` app's models to that DB and restricts its migrations to it. Tests for `cryoweb` use the `template_cryoweb` template database.

**Django apps** (in `django-data/image/`):
- `uid`: core data model (the "UID" = unified IMAGE data): `Submission`, `Animal`, `Sample`, `Person`, `Organization`, dictionaries (`DictBreed`, `DictSpecie`, `DictCountry`, …) and the `Name` base class. Other apps build on these.
- `cryoweb`, `crbanim`, `excel`: one importer per data source. Each has a `tasks.py` (celery) and `helpers.py` that convert the source into `uid` objects. `cryoweb` imports a dump into the staging DB first, then maps it into `uid`.
- `validation`: validates submission data (ontologies, required fields) and stores results; uses `zooma` for ontology term lookup and mapping.
- `biosample`: builds BioSamples/USI payloads, with celery tasks split into `tasks/submission.py`, `retrieval.py`, `cleanup.py`.
- `submissions`: submission lifecycle views and the shared submission-level celery tasks. `submissions_ws`: channels consumers/routing that push status to the browser over websockets.
- `animals`, `samples`: list/detail/edit views for the UID objects. `accounts`: registration/users. `language`: language dictionaries. `common`: shared helpers, constants, storage, and base celery task classes.

**Celery pattern**: long-running work (import, validation, submission) runs as celery tasks derived from `common.tasks.BaseTask` (plus `NotifyAdminTaskMixin` for error mails), with a redis-based lock helper to prevent concurrent runs on the same submission. Task state is reflected on `Submission` status and surfaced through `submissions_ws`. After changing task code, restart the workers: `docker compose restart celery-worker`.

**Other directories**: `cryoweb-data/` (sample Cryoweb dumps and helper scripts), `Jun-code/` (standalone prototype scripts), and the large `*.sql.gz`/`*.tar.gz` files in the repo root are database dumps/data, not code.
